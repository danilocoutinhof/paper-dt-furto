"""Revalidation ladder (E0 -> E4) for the resubmission.

Each stage adds exactly one protocol correction to the previous one, so the
effect of every correction on the headline results can be isolated:

- E0: v1 protocol (per-scenario model, chronological 70/30 split, metrics on
  the full week), but repeated over many independent seeds instead of one.
  Replicate 0 reproduces the submitted campaign exactly.
- E1: one supervised model trained on pooled training realizations of all
  scenarios, frozen, and evaluated only on unseen test realizations.
- E2: causal hour-of-day recurrence feature (v1 leaked ~24 future values).
- E3: random sampling phase per realization (same for all policies) and a
  per-day jitter of the theft onset, so that basal 60-min sampling is no
  longer aligned with the theft onset.
- E4: history-dependent features computed only from the samples actually
  received by the back-office (instead of the native 5-min grid).

Budget-matched fixed cadences (20/25/30/40 min) and a like-for-like detector
for fixed policies (the same weighted fusion used by the adaptive twin) are
evaluated in every stage.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from .comparison import ComparisonSettings
from .config import build_config
from .control import EvidenceCapOrchestrator, FixedCadenceOrchestrator, PolicyOrchestrator
from .decision import DecisionEngine, build_fusion_strategies
from .decision.fusion import WeightedProbabilityFusion
from .devices import MockTransport, estimate_communication_cost
from .features import OnlineFeatureState, build_feature_dataset, recompute_features_on_received
from .risk import (
    FrozenSupervisedModel,
    score_rule_based_record,
    score_rule_based_risk,
    train_supervised_baseline,
)
from .runtime import SimulationRunner
from .schemas import Scenario
from .synthetic import NATIVE_INTERVAL_MINUTES, generate_synthetic_frames

SCENARIOS = list(Scenario)
THEFT_SCENARIOS = [
    Scenario.PERSISTENT_THEFT.value,
    Scenario.PEAK_THEFT.value,
    Scenario.NIGHT_THEFT.value,
    Scenario.INTERMITTENT_EVENING.value,
]
NO_THEFT_SCENARIOS = [s.value for s in SCENARIOS if s.value not in THEFT_SCENARIOS]

FIXED_POLICIES = {
    "fixed_dense": 5,
    "fixed_short": 15,
    "fixed_20": 20,
    "fixed_25": 25,
    "fixed_30": 30,
    "fixed_40": 40,
    "fixed_long": 60,
}
FIXED_SOURCES = ["risk_probability", "supervised_probability", "fused_weighted_probability"]
ADAPTIVE_KEY = ("adaptive", "decision_probability", "weighted")
DENSE_PAPER_KEY = ("fixed_dense", "supervised_probability", "not_applicable")

PHASE_SEED_SALT = 104729


@dataclass(frozen=True)
class Protocol:
    name: str
    training: str  # "per_scenario" (v1) | "global"
    slot_fix: bool
    random_phase: bool
    feature_mode: str  # "native" (v1) | "emitted"
    description: str
    phase_a: bool = False  # also run the Phase A policy variants


STAGES: dict[str, Protocol] = {
    "E0": Protocol("E0", "per_scenario", False, False, "native", "v1 protocol, multi-seed"),
    "E1": Protocol("E1", "global", False, False, "native", "+ global frozen model, unseen test realizations"),
    "E2": Protocol("E2", "global", True, False, "native", "+ causal slot_recurrence"),
    "E3": Protocol("E3", "global", True, True, "native", "+ random sampling phase and theft-onset jitter"),
    "E4": Protocol("E4", "global", True, True, "emitted", "+ features from received samples only"),
    "E5": Protocol("E5", "global", True, True, "emitted", "E4 + Phase A variants (backfill, basal period, evidence cap)", phase_a=True),
}


def evaluation_seed(scenario_index: int, replicate: int) -> int:
    """Replicate 0 uses the v1 campaign seed (42 + scenario index)."""
    return 42 + scenario_index + 100 * replicate


def training_seed(scenario_index: int, replicate: int) -> int:
    """Disjoint from every test seed."""
    return 50_000 + 1_000 * scenario_index + replicate


def phase_offset_minutes(seed: int) -> int:
    rng = np.random.default_rng([seed, PHASE_SEED_SALT])
    return int(rng.integers(0, 60 // NATIVE_INTERVAL_MINUTES)) * NATIVE_INTERVAL_MINUTES


def build_scored_dataset(scenario: Scenario, seed: int, protocol: Protocol, days: int) -> pd.DataFrame:
    forensic_df, billing_df, alarm_df = generate_synthetic_frames(
        days=days, scenario=scenario, seed=seed, onset_jitter=protocol.random_phase
    )
    for frame in (forensic_df, billing_df, alarm_df):
        frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    merged = build_feature_dataset(forensic_df, billing_df, alarm_df, fix_slot_recurrence=protocol.slot_fix)
    return score_rule_based_risk(merged)


def _training_frame(args: tuple) -> pd.DataFrame:
    scenario_index, replicate, protocol, days = args
    return build_scored_dataset(SCENARIOS[scenario_index], training_seed(scenario_index, replicate), protocol, days)


def train_global_model(protocol: Protocol, train_replicates: int, days: int, n_jobs: int) -> FrozenSupervisedModel:
    from joblib import Parallel, delayed

    tasks = [(i, j, protocol, days) for i in range(len(SCENARIOS)) for j in range(train_replicates)]
    frames = Parallel(n_jobs=n_jobs)(delayed(_training_frame)(task) for task in tasks)
    return FrozenSupervisedModel().fit(pd.concat(frames, ignore_index=True))


def _fused_weighted(risk: pd.Series | np.ndarray, supervised: pd.Series | np.ndarray) -> np.ndarray:
    fusion = WeightedProbabilityFusion()
    values = np.asarray(risk) * fusion.rule_weight + np.asarray(supervised) * fusion.supervised_weight
    return np.clip(values, 0.0, 0.99)


def _received_mask(df: pd.DataFrame) -> np.ndarray:
    """Samples available at the back-office: live emissions plus, for the
    backfill policies (Phase A), samples retrieved later from the device's
    local buffer."""
    column = "received" if "received" in df.columns else "observed"
    return df[column].to_numpy() == 1


def _detection_counts(df: pd.DataFrame, probability_column: str, threshold: float) -> dict:
    observed = _received_mask(df)
    y_true = df["theft_active"].to_numpy().astype(int) == 1
    y_pred = (df[probability_column].to_numpy() >= threshold) & observed
    tp = int((y_pred & y_true).sum())
    fp = int((y_pred & ~y_true).sum())
    fn = int((~y_pred & y_true).sum())
    tn = int((~y_pred & ~y_true).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fp / (fp + tn) if fp + tn else 0.0,
        "theft_received": int((observed & y_true).sum()),
    }


EPISODE_MERGE_GAP_MINUTES = 15
"""Theft ticks separated by at most this gap belong to the same episode (the
v1 intermittent generator draws theft per tick, so short gaps are merged)."""


def theft_episodes(df: pd.DataFrame) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """[start, end) of each theft episode; end = last theft tick + 1 tick."""
    theft_times = df.loc[df["theft_active"].astype(int) == 1, "timestamp"].sort_values().to_numpy()
    if len(theft_times) == 0:
        return []
    gaps = np.diff(theft_times) > np.timedelta64(EPISODE_MERGE_GAP_MINUTES, "m")
    starts = np.concatenate([[0], np.nonzero(gaps)[0] + 1])
    ends = np.concatenate([np.nonzero(gaps)[0], [len(theft_times) - 1]])
    tick = np.timedelta64(NATIVE_INTERVAL_MINUTES, "m")
    return [(pd.Timestamp(theft_times[s]), pd.Timestamp(theft_times[e] + tick)) for s, e in zip(starts, ends)]


def _episode_metrics(df: pd.DataFrame, probability_column: str, threshold: float, episodes: list) -> dict:
    """Episode-level detection (R1.3): an episode is detected when at least
    one sample inside it is received and flagged (probability >= threshold).
    The delay runs from the episode start to the moment the first such flag
    became known at the back-office (`known_at`; equal to the sample time for
    live emissions, and to the backfill time for samples retrieved later).
    Undetected minutes add, per episode, the time until detection (capped at
    the episode duration) or the full duration of missed episodes."""
    if not episodes:
        return {
            "episodes": 0, "episodes_detected": 0, "delay_sum_min": 0.0, "delay_max_min": np.nan,
            "undetected_theft_min": 0.0, "episodes_detected_live": 0, "delay_live_sum_min": 0.0,
        }
    flags = (df[probability_column].to_numpy() >= threshold) & _received_mask(df)
    sample_times = df["timestamp"].to_numpy()[flags]
    known_column = "known_at" if "known_at" in df.columns else "timestamp"
    known_times = pd.to_datetime(df[known_column]).to_numpy()[flags]
    order = np.argsort(sample_times)
    sample_times, known_times = sample_times[order], known_times[order]
    live = known_times == sample_times
    detected, delays, undetected = 0, [], 0.0
    detected_live, delays_live = 0, []
    for start, end in episodes:
        lo = np.searchsorted(sample_times, start.to_datetime64(), side="left")
        hi = np.searchsorted(sample_times, end.to_datetime64(), side="left")
        duration = (end - start) / pd.Timedelta(minutes=1)
        if hi > lo:
            first_known = pd.Timestamp(known_times[lo:hi].min())
            delay = (first_known - start) / pd.Timedelta(minutes=1)
            detected += 1
            delays.append(delay)
            undetected += min(delay, duration)
            live_in_episode = sample_times[lo:hi][live[lo:hi]]
            if len(live_in_episode):
                detected_live += 1
                delays_live.append((pd.Timestamp(live_in_episode.min()) - start) / pd.Timedelta(minutes=1))
        else:
            undetected += duration
    return {
        "episodes": len(episodes),
        "episodes_detected": detected,
        "delay_sum_min": float(sum(delays)),
        "delay_max_min": float(max(delays)) if delays else np.nan,
        "undetected_theft_min": float(undetected),
        "episodes_detected_live": detected_live,
        "delay_live_sum_min": float(sum(delays_live)),
    }


def _cost_summary(df: pd.DataFrame, settings: ComparisonSettings) -> dict:
    observed_rows = df.loc[df["observed"] == 1, ["timestamp", "link_ok", "heartbeat_ok"]]
    costs = estimate_communication_cost(observed_rows, settings.link_profile, seed=settings.cost_model_seed)
    if costs.empty:
        return {"observed_samples": 0, "communication_bytes": 0, "mean_latency_ms": 0.0, "ble_fallback_ratio": 0.0}
    return {
        "observed_samples": int(len(observed_rows)),
        "communication_bytes": int(costs["total_bytes"].sum()),
        "mean_latency_ms": float(costs["latency_ms"].mean()),
        "ble_fallback_ratio": float(costs["fallback_used"].mean()),
    }


def _mode_stats(modes: pd.Series) -> dict:
    values = modes.astype(str).to_numpy()
    elevated = values != "basal"
    escalations = int(((values[1:] != "basal") & (values[:-1] == "basal")).sum()) if len(values) > 1 else 0
    return {
        "share_moderate": float((values == "moderate").mean()),
        "share_aggressive": float((values == "aggressive").mean()),
        "share_elevated": float(elevated.mean()),
        "escalations": escalations,
    }


def _rescore_received(sub: pd.DataFrame, model: FrozenSupervisedModel) -> pd.DataFrame:
    sub = recompute_features_on_received(sub)
    sub = score_rule_based_risk(sub)
    sub["supervised_probability"] = model.predict_proba(sub)
    sub["fused_weighted_probability"] = _fused_weighted(sub["risk_probability"], sub["supervised_probability"])
    return sub


def run_realization(protocol: Protocol, scenario_index: int, replicate: int, model: FrozenSupervisedModel | None, days: int) -> list[dict]:
    scenario = SCENARIOS[scenario_index]
    seed = evaluation_seed(scenario_index, replicate)
    df = build_scored_dataset(scenario, seed, protocol, days)
    if protocol.training == "per_scenario":
        df, _ = train_supervised_baseline(df)
    else:
        df = model.apply(df)
    df["fused_weighted_probability"] = _fused_weighted(df["risk_probability"], df["supervised_probability"])

    classifier_auc = np.nan
    if df["theft_active"].nunique() == 2:
        from sklearn.metrics import roc_auc_score

        classifier_auc = float(roc_auc_score(df["theft_active"], df["supervised_probability"]))

    settings = ComparisonSettings()
    episodes = theft_episodes(df)
    config = build_config(Path("."))
    offset = phase_offset_minutes(seed) if protocol.random_phase else 0
    t0 = df["timestamp"].iloc[0]
    minutes = ((df["timestamp"] - t0) / pd.Timedelta(minutes=1)).round().astype(int).to_numpy()
    base = {
        "stage": protocol.name,
        "scenario": scenario.value,
        "has_theft": scenario.value in THEFT_SCENARIOS,
        "replicate": replicate,
        "seed": seed,
        "phase_offset_min": offset,
        "classifier_auc_full_week": classifier_auc,
        "theft_ticks": int(df["theft_active"].sum()),
    }
    rows: list[dict] = []

    for policy_name, period in FIXED_POLICIES.items():
        first = offset % period
        observed = (minutes >= first) & ((minutes - first) % period == 0)
        policy_df = df.copy()
        policy_df["observed"] = observed.astype(int)
        if protocol.feature_mode == "emitted":
            received = _rescore_received(policy_df.loc[policy_df["observed"] == 1].copy(), model)
            columns = ["risk_probability", "supervised_probability", "fused_weighted_probability"]
            policy_df = policy_df.set_index("timestamp")
            policy_df.loc[received["timestamp"].to_numpy(), columns] = received.set_index("timestamp")[columns].to_numpy()
            policy_df = policy_df.reset_index()
        cost = _cost_summary(policy_df, settings)
        for source in FIXED_SOURCES:
            rows.append(
                {
                    **base,
                    "policy_name": policy_name,
                    "probability_source": source,
                    "fusion_strategy": "not_applicable",
                    "cadence_min": period,
                    **cost,
                    **_detection_counts(policy_df, source, settings.prediction_threshold),
                    **_episode_metrics(policy_df, source, settings.prediction_threshold, episodes),
                }
            )

    first_emit_time = t0 + pd.Timedelta(minutes=offset) if offset else None
    for fusion_name, fusion in build_fusion_strategies().items():
        runner = SimulationRunner(
            config=config,
            decision_engine=DecisionEngine(thresholds=config.thresholds, fusion_strategy=fusion),
            orchestrator=PolicyOrchestrator(policy=config.policy, thresholds=config.thresholds),
            transport=MockTransport(ble_available=True),
        )
        scorer = None
        if protocol.feature_mode == "emitted":
            state = OnlineFeatureState()

            def scorer(record: dict, _state: OnlineFeatureState = state) -> dict:
                record = _state.update(record)
                record["risk_probability"] = score_rule_based_record(record)
                record["supervised_probability"] = model.predict_record(record)
                return record

        adaptive_df, *_ = runner.run(df, first_emit_time=first_emit_time, online_scorer=scorer)
        adaptive_df["observed"] = adaptive_df["observed"].astype(int)
        cost = _cost_summary(adaptive_df, settings)
        modes = _mode_stats(adaptive_df["observation_mode"])
        sources = ["decision_probability"] + (["risk_probability", "supervised_probability"] if fusion_name == "weighted" else [])
        for source in sources:
            rows.append(
                {
                    **base,
                    "policy_name": "adaptive",
                    "probability_source": source,
                    "fusion_strategy": fusion_name,
                    "cadence_min": np.nan,
                    **cost,
                    **modes,
                    **_detection_counts(adaptive_df, source, settings.prediction_threshold),
                    **_episode_metrics(adaptive_df, source, settings.prediction_threshold, episodes),
                }
            )
    if protocol.phase_a:
        rows.extend(_phase_a_rows(protocol, df, model, base, settings, episodes, config, offset, seed))
    return rows


# --- Phase A: backfill, basal period, evidence cap ---------------------------------

BACKFILL_HOURS = 2.0
"""On every flagged live sample, the back-office requests the device's local
5-min records not yet received, at most BACKFILL_HOURS back (the full window
at alert onset, the gap since the last retrieval afterwards)."""

EVIDENCE_CAP_MINUTES = 120


@dataclass(frozen=True)
class BackfillCostModel:
    """Cost of retrieving buffered records in a batch (Phase A hypothesis, to
    be calibrated on the bench test). Conservative: each record costs as
    much as a live sample payload; records are packed into messages of up to
    `records_per_message`; the session is already open because the request
    follows the live sample that raised the alert (no extra RRC setup);
    each message can be retransmitted with the nominal-link probability."""

    record_bytes: int = 64
    records_per_message: int = 16
    retransmission_probability: float = 0.04
    max_retransmissions: int = 3

    def cost(self, n_records: int, rng: np.random.Generator) -> int:
        total = 0
        remaining = n_records
        while remaining > 0:
            batch = min(remaining, self.records_per_message)
            retransmissions = 0
            while retransmissions < self.max_retransmissions and rng.random() < self.retransmission_probability:
                retransmissions += 1
            total += batch * self.record_bytes * (1 + retransmissions)
            remaining -= batch
        return total


@dataclass(frozen=True)
class PhaseAVariant:
    name: str
    adaptive: bool
    basal_minutes: int
    backfill: bool = False
    evidence_cap: bool = False


PHASE_A_VARIANTS = [
    PhaseAVariant("adaptive_b60", True, 60),
    PhaseAVariant("adaptive_b40", True, 40),
    PhaseAVariant("adaptive_b30", True, 30),
    PhaseAVariant("adaptive_b20", True, 20),
    PhaseAVariant("adaptive_b15", True, 15),
    PhaseAVariant("adaptive_b15_cap", True, 15, evidence_cap=True),
    PhaseAVariant("adaptive_b60_cap", True, 60, evidence_cap=True),
    PhaseAVariant("adaptive_b30_cap", True, 30, evidence_cap=True),
    PhaseAVariant("adaptive_b60_bf", True, 60, backfill=True),
    PhaseAVariant("adaptive_b30_bf", True, 30, backfill=True),
    PhaseAVariant("adaptive_b60_bf_cap", True, 60, backfill=True, evidence_cap=True),
    PhaseAVariant("adaptive_b30_bf_cap", True, 30, backfill=True, evidence_cap=True),
    PhaseAVariant("fixed_60_bf", False, 60, backfill=True),
    PhaseAVariant("fixed_30_bf", False, 30, backfill=True),
]


def _score_with_weighted_fusion(rows: pd.DataFrame, model: FrozenSupervisedModel | None, emitted: bool) -> np.ndarray:
    if emitted:
        rows = _rescore_received(rows, model)
        return rows.set_index("timestamp")["fused_weighted_probability"]
    return pd.Series(_fused_weighted(rows["risk_probability"], rows["supervised_probability"]), index=rows["timestamp"].to_numpy())


def run_variant(
    variant: PhaseAVariant,
    df: pd.DataFrame,
    model: FrozenSupervisedModel | None,
    config,
    emitted: bool,
    first_emit_time: pd.Timestamp | None,
    threshold: float,
    rng: np.random.Generator,
    cost_model: BackfillCostModel = BackfillCostModel(),
) -> tuple[pd.DataFrame, dict]:
    """Runs one Phase A policy through the closed loop and returns the
    evaluation frame (with `received`/`known_at`) and backfill accounting."""
    policy = replace(config.policy, basal_minutes=variant.basal_minutes)
    variant_config = replace(config, policy=policy)
    if not variant.adaptive:
        orchestrator = FixedCadenceOrchestrator(policy=policy, thresholds=config.thresholds)
    elif variant.evidence_cap:
        orchestrator = EvidenceCapOrchestrator(policy=policy, thresholds=config.thresholds, cap_minutes=EVIDENCE_CAP_MINUTES)
    else:
        orchestrator = PolicyOrchestrator(policy=policy, thresholds=config.thresholds)
    runner = SimulationRunner(
        config=variant_config,
        decision_engine=DecisionEngine(thresholds=config.thresholds, fusion_strategy=WeightedProbabilityFusion()),
        orchestrator=orchestrator,
        transport=MockTransport(ble_available=True),
    )

    state = OnlineFeatureState() if emitted else None
    live_times: set = set()
    backfilled: dict = {}
    events: list[tuple[pd.Timestamp, int]] = []
    memory = {"previous_flag": False, "backfilled_until": df["timestamp"].iloc[0] - pd.Timedelta(days=1)}
    window_length = pd.Timedelta(hours=BACKFILL_HOURS)

    def scorer(record: dict) -> dict:
        record = state.update(record)
        record["risk_probability"] = score_rule_based_record(record)
        record["supervised_probability"] = model.predict_record(record)
        return record

    def on_decision(timestamp: pd.Timestamp, record: dict, decision) -> None:
        live_times.add(timestamp)
        flag = decision.decision_probability >= threshold
        if variant.backfill and flag:
            # While the alert is active, every flagged live sample pulls the
            # buffered records not yet received since the previous retrieval
            # (at most BACKFILL_HOURS back). At alert onset this recovers the
            # run-up to the alert; afterwards it fills the gaps of a sparse
            # live cadence ("log densely, transmit sparsely, backfill on alert").
            start = max(timestamp - window_length, memory["backfilled_until"])
            window = df[(df["timestamp"] >= start) & (df["timestamp"] < timestamp)]
            missing = window[~window["timestamp"].isin(live_times) & ~window["timestamp"].isin(backfilled.keys())]
            for sample_time in missing["timestamp"]:
                backfilled[sample_time] = timestamp
            if len(missing):
                events.append((timestamp, int(len(missing))))
            memory["backfilled_until"] = timestamp
            if state is not None and len(missing):
                state.ingest_past(missing.to_dict("records"))
        memory["previous_flag"] = flag

    timeline, *_ = runner.run(
        df,
        first_emit_time=first_emit_time,
        online_scorer=scorer if emitted else None,
        on_decision=on_decision,
    )
    evaluation = timeline.copy()
    evaluation["observed"] = evaluation["observed"].astype(int)
    evaluation["received"] = evaluation["observed"]
    evaluation["known_at"] = evaluation["timestamp"]
    if backfilled:
        mask = evaluation["timestamp"].isin(backfilled.keys())
        evaluation.loc[mask, "received"] = 1
        evaluation.loc[mask, "known_at"] = evaluation.loc[mask, "timestamp"].map(backfilled)
        received_times = evaluation.loc[evaluation["received"] == 1, "timestamp"]
        union = df[df["timestamp"].isin(received_times)].copy()
        scored = _score_with_weighted_fusion(union, model, emitted)
        evaluation.loc[mask, "decision_probability"] = evaluation.loc[mask, "timestamp"].map(scored).to_numpy()

    backfill_records = int(sum(n for _, n in events))
    backfill_bytes = int(sum(cost_model.cost(n, rng) for _, n in events))
    accounting = {
        "backfill_events": len(events),
        "backfill_records": backfill_records,
        "backfill_bytes": backfill_bytes,
    }
    return evaluation, accounting


def _phase_a_rows(protocol: Protocol, df: pd.DataFrame, model, base: dict, settings: ComparisonSettings, episodes: list, config, offset: int, seed: int) -> list[dict]:
    emitted = protocol.feature_mode == "emitted"
    t0 = df["timestamp"].iloc[0]
    first_emit_time = t0 + pd.Timedelta(minutes=offset) if offset else None
    rows = []
    for index, variant in enumerate(PHASE_A_VARIANTS):
        rng = np.random.default_rng([seed, 31337, index])
        evaluation, accounting = run_variant(
            variant, df, model, config, emitted, first_emit_time, settings.prediction_threshold, rng
        )
        cost = _cost_summary(evaluation, settings)
        live_bytes = cost["communication_bytes"]
        cost["communication_bytes"] = live_bytes + accounting["backfill_bytes"]
        rows.append(
            {
                **base,
                "policy_name": variant.name,
                "probability_source": "decision_probability",
                "fusion_strategy": "weighted",
                "cadence_min": variant.basal_minutes,
                **cost,
                "live_bytes": live_bytes,
                **accounting,
                **_mode_stats(evaluation["observation_mode"]),
                **_detection_counts(evaluation, "decision_probability", settings.prediction_threshold),
                **_episode_metrics(evaluation, "decision_probability", settings.prediction_threshold, episodes),
            }
        )
    return rows


# --- Aggregation -----------------------------------------------------------------

KEY = ["policy_name", "probability_source", "fusion_strategy"]


def bootstrap_ci(values, n_resamples: int = 5000, seed: int = 0) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if len(values) == 0:
        return np.nan, np.nan, np.nan
    if len(values) == 1:
        return float(values[0]), float(values[0]), float(values[0])
    rng = np.random.default_rng(seed)
    means = rng.choice(values, size=(n_resamples, len(values)), replace=True).mean(axis=1)
    return float(values.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _summarize(per_replicate: pd.DataFrame, group_cols: list[str], metrics: list[str]) -> pd.DataFrame:
    out = []
    for key, group in per_replicate.groupby(group_cols, dropna=False):
        key = key if isinstance(key, tuple) else (key,)
        row = dict(zip(group_cols, key))
        row["replicates"] = int(group["replicate"].nunique())
        for metric in metrics:
            mean, lo, hi = bootstrap_ci(group[metric].to_numpy())
            row[f"{metric}_mean"] = mean
            row[f"{metric}_ci_low"] = lo
            row[f"{metric}_ci_high"] = hi
            replicate0 = group.loc[group["replicate"] == 0, metric]
            row[f"{metric}_rep0"] = float(replicate0.iloc[0]) if len(replicate0) else np.nan
        out.append(row)
    return pd.DataFrame(out)


def macro_seven(runs: pd.DataFrame) -> pd.DataFrame:
    """v1-style table (mean over the 7 scenarios, theft-free scenarios scored 0)."""
    per_rep = runs.groupby(KEY + ["replicate"], as_index=False)[["f1", "recall", "precision", "communication_bytes"]].mean()
    return _summarize(per_rep, KEY, ["f1", "recall", "precision", "communication_bytes"])


EPISODE_SUM_COLUMNS = ["episodes", "episodes_detected", "delay_sum_min", "undetected_theft_min", "theft_received", "episodes_detected_live", "delay_live_sum_min"]


def _add_episode_rates(per_rep: pd.DataFrame, n_scenarios: int) -> pd.DataFrame:
    per_rep["episode_detection_rate"] = per_rep["episodes_detected"] / per_rep["episodes"].replace(0, np.nan)
    per_rep["mean_delay_min"] = per_rep["delay_sum_min"] / per_rep["episodes_detected"].replace(0, np.nan)
    per_rep["undetected_theft_min_per_scenario"] = per_rep["undetected_theft_min"] / n_scenarios
    per_rep["evidence_received"] = per_rep["theft_received"] / (per_rep["tp"] + per_rep["fn"]).replace(0, np.nan)
    per_rep["episode_detection_live_rate"] = per_rep["episodes_detected_live"] / per_rep["episodes"].replace(0, np.nan)
    per_rep["mean_delay_live_min"] = per_rep["delay_live_sum_min"] / per_rep["episodes_detected_live"].replace(0, np.nan)
    return per_rep


EPISODE_METRICS = [
    "episode_detection_rate", "mean_delay_min", "delay_max_min", "undetected_theft_min_per_scenario",
    "evidence_received", "episode_detection_live_rate", "mean_delay_live_min",
]


def theft_macro4(runs: pd.DataFrame) -> pd.DataFrame:
    """Mean over the four theft-bearing scenarios (same aggregation as the
    'Mean, 4 theft-bearing scenarios' row of the submitted Table 5)."""
    theft = runs[runs["scenario"].isin(THEFT_SCENARIOS)]
    per_rep = theft.groupby(KEY + ["replicate"], as_index=False)[["f1", "recall", "precision", "communication_bytes"]].mean()
    return _summarize(per_rep, KEY, ["f1", "recall", "precision", "communication_bytes"])


def theft_pooled(runs: pd.DataFrame) -> pd.DataFrame:
    """Micro-averaged detection over the four theft-bearing scenarios, plus
    episode-level metrics pooled over the same scenarios."""
    theft = runs[runs["scenario"].isin(THEFT_SCENARIOS)]
    per_rep = theft.groupby(KEY + ["replicate"], as_index=False)[["tp", "fp", "fn", "communication_bytes"] + EPISODE_SUM_COLUMNS].sum()
    per_rep = per_rep.merge(
        theft.groupby(KEY + ["replicate"], as_index=False)["delay_max_min"].max(), on=KEY + ["replicate"]
    )
    per_rep = _add_episode_rates(per_rep, len(THEFT_SCENARIOS))
    per_rep["precision"] = per_rep["tp"] / (per_rep["tp"] + per_rep["fp"]).replace(0, np.nan)
    per_rep["recall"] = per_rep["tp"] / (per_rep["tp"] + per_rep["fn"]).replace(0, np.nan)
    per_rep["f1"] = 2 * per_rep["tp"] / (2 * per_rep["tp"] + per_rep["fp"] + per_rep["fn"]).replace(0, np.nan)
    per_rep = per_rep.fillna({"precision": 0.0, "recall": 0.0, "f1": 0.0})
    per_rep["communication_bytes"] = per_rep["communication_bytes"] / len(THEFT_SCENARIOS)
    return _summarize(per_rep, KEY, ["f1", "recall", "precision", "communication_bytes"] + EPISODE_METRICS)


def theft_free(runs: pd.DataFrame) -> pd.DataFrame:
    """False-alarm behavior on the three theft-free scenarios (mean per scenario)."""
    clean = runs[runs["scenario"].isin(NO_THEFT_SCENARIOS)].copy()
    metrics = ["fpr", "fp", "communication_bytes"]
    for column in ["share_elevated", "share_aggressive", "escalations", "backfill_events", "backfill_bytes"]:
        if column in clean.columns:
            metrics.append(column)
    per_rep = clean.groupby(KEY + ["replicate"], as_index=False)[metrics].mean()
    return _summarize(per_rep, KEY, metrics)


def per_scenario(runs: pd.DataFrame) -> pd.DataFrame:
    metrics = ["f1", "recall", "precision", "communication_bytes", "fpr"]
    for column in ["share_elevated", "share_aggressive"]:
        if column in runs.columns:
            metrics.append(column)
    per_rep = runs[KEY + ["scenario", "replicate"] + metrics]
    return _summarize(per_rep, KEY + ["scenario"], metrics)


def paired_against_fixed(runs: pd.DataFrame, fixed_source: str = "fused_weighted_probability", adaptive_key: tuple = ADAPTIVE_KEY) -> pd.DataFrame:
    """Adaptive (weighted, decision probability) vs every fixed cadence, paired
    by realization, on the theft-bearing scenarios (pooled per replicate).
    Wilcoxon signed-rank on the per-replicate differences, Holm-corrected."""
    theft = runs[runs["scenario"].isin(THEFT_SCENARIOS)]
    pooled = theft.groupby(KEY + ["replicate"], as_index=False)[["tp", "fp", "fn", "communication_bytes"] + EPISODE_SUM_COLUMNS].sum()
    pooled = _add_episode_rates(pooled, len(THEFT_SCENARIOS))
    pooled["f1"] = 2 * pooled["tp"] / (2 * pooled["tp"] + pooled["fp"] + pooled["fn"]).replace(0, np.nan)
    pooled["recall"] = pooled["tp"] / (pooled["tp"] + pooled["fn"]).replace(0, np.nan)
    pooled = pooled.fillna({"f1": 0.0, "recall": 0.0})
    pooled["communication_bytes"] = pooled["communication_bytes"] / len(THEFT_SCENARIOS)

    def _select(policy: str, source: str, fusion: str) -> pd.DataFrame:
        mask = (pooled["policy_name"] == policy) & (pooled["probability_source"] == source) & (pooled["fusion_strategy"] == fusion)
        return pooled[mask].set_index("replicate").sort_index()

    adaptive = _select(*adaptive_key)
    rows = []
    for policy_name in FIXED_POLICIES:
        fixed = _select(policy_name, fixed_source, "not_applicable")
        common = adaptive.index.intersection(fixed.index)
        if len(common) == 0:
            continue
        row = {"policy": adaptive_key[0], "fixed_policy": policy_name, "fixed_source": fixed_source, "pairs": int(len(common))}
        for metric in ["f1", "recall", "episode_detection_rate", "mean_delay_min", "undetected_theft_min_per_scenario", "evidence_received", "episode_detection_live_rate", "mean_delay_live_min", "communication_bytes"]:
            diff = adaptive.loc[common, metric].to_numpy(dtype=float) - fixed.loc[common, metric].to_numpy(dtype=float)
            if np.isnan(diff).all():
                continue
            mean, lo, hi = bootstrap_ci(diff)
            row[f"adaptive_{metric}"] = float(adaptive.loc[common, metric].mean())
            row[f"fixed_{metric}"] = float(fixed.loc[common, metric].mean())
            row[f"diff_{metric}_mean"] = mean
            row[f"diff_{metric}_ci_low"] = lo
            row[f"diff_{metric}_ci_high"] = hi
            if metric != "communication_bytes":
                valid = diff[~np.isnan(diff)]
                if len(valid) >= 2 and np.any(valid != 0):
                    row[f"p_{metric}"] = float(wilcoxon(valid).pvalue)
                else:
                    row[f"p_{metric}"] = 1.0
        rows.append(row)
    table = pd.DataFrame(rows)
    for metric in ["f1", "recall", "episode_detection_rate", "mean_delay_min", "undetected_theft_min_per_scenario", "evidence_received", "episode_detection_live_rate", "mean_delay_live_min"]:
        column = f"p_{metric}"
        if column in table.columns and not table.empty:
            table[f"p_{metric}_holm"] = _holm(table[column].to_numpy())
    return table


def _holm(p_values: np.ndarray) -> np.ndarray:
    p_values = np.asarray(p_values, dtype=float)
    order = np.argsort(p_values)
    m = len(p_values)
    adjusted = np.empty(m)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (m - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def protocol_record(protocol: Protocol) -> dict:
    return asdict(protocol)
