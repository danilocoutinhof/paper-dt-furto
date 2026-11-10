from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np
import pandas as pd

from fraud_dt.config import ObservationPolicy, Thresholds
from fraud_dt.control import EvidenceCapOrchestrator
from fraud_dt.features import OnlineFeatureState, build_feature_dataset, recompute_features_on_received
from fraud_dt.revalidation import (
    STAGES,
    BackfillCostModel,
    _episode_metrics,
    run_realization,
    train_global_model,
)
from fraud_dt.schemas import Scenario
from fraud_dt.synthetic import generate_synthetic_frames
from fraud_dt.twin import ForensicTwin, TwinDecision


def _decision(ts: pd.Timestamp, probability: float) -> TwinDecision:
    return TwinDecision(0, "dev", ts, probability, probability, probability, "test", "high", "test")


def test_evidence_cap_falls_back_to_moderate_and_resets_on_basal() -> None:
    orchestrator = EvidenceCapOrchestrator(policy=ObservationPolicy(), thresholds=Thresholds(), cap_minutes=60)
    twin = ForensicTwin(dev_eui="dev")
    t0 = pd.Timestamp("2026-01-01 18:00")
    modes = []
    for step in range(20):  # 5-min steps with high risk
        command = orchestrator.build_command(twin, _decision(t0 + pd.Timedelta(minutes=5 * step), 0.9))
        twin.apply_command(command)
        modes.append(command.selected_mode)
    assert modes[:12] == ["aggressive"] * 12
    assert set(modes[12:]) == {"moderate"}
    for step in range(20, 30):  # risk drops: back to basal, cap released
        command = orchestrator.build_command(twin, _decision(t0 + pd.Timedelta(minutes=5 * step), 0.05))
        twin.apply_command(command)
    assert command.selected_mode == "basal"
    command = orchestrator.build_command(twin, _decision(t0 + pd.Timedelta(minutes=200), 0.9))
    assert command.selected_mode == "aggressive"


def test_backfill_cost_without_retransmissions_is_linear() -> None:
    model = BackfillCostModel(retransmission_probability=0.0)
    rng = np.random.default_rng(0)
    assert model.cost(0, rng) == 0
    assert model.cost(23, rng) == 23 * 64


def test_online_state_with_late_samples_matches_batch_on_union() -> None:
    frames = list(generate_synthetic_frames(days=2, scenario=Scenario.PEAK_THEFT, seed=3))
    for frame in frames:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    merged = build_feature_dataset(*frames, fix_slot_recurrence=True)
    live = merged.iloc[::12]  # hourly live samples
    cutoff = 300
    late = merged.iloc[cutoff - 23 : cutoff]
    late = late[~late["timestamp"].isin(live["timestamp"])]
    state = OnlineFeatureState()
    outputs = {}
    for record in live.to_dict("records"):
        if record["timestamp"] == merged["timestamp"].iloc[cutoff]:
            state.ingest_past(late.to_dict("records"))
        outputs[record["timestamp"]] = state.update(record)
    union = recompute_features_on_received(pd.concat([live[live["timestamp"] <= merged["timestamp"].iloc[cutoff]], late]))
    expected = union.set_index("timestamp").loc[merged["timestamp"].iloc[cutoff]]
    got = outputs[merged["timestamp"].iloc[cutoff]]
    for column in ["rolling_divergence_mean", "rolling_divergence_max"]:
        assert abs(got[column] - expected[column]) < 1e-12


def test_episode_metrics_separate_live_and_late_detection() -> None:
    times = pd.date_range("2026-01-01", periods=24, freq="5min")
    df = pd.DataFrame({"timestamp": times, "theft_active": [0] * 4 + [1] * 6 + [0] * 14})
    df["p"] = 0.0
    df["received"] = 0
    df["known_at"] = df["timestamp"]
    df.loc[5, ["p", "received"]] = [0.9, 1]
    df.loc[5, "known_at"] = times[20]  # documented by backfill, 80 min later
    episodes = [(times[4], times[10])]
    metrics = _episode_metrics(df, "p", 0.5, episodes)
    assert metrics["episodes_detected"] == 1 and metrics["episodes_detected_live"] == 0
    assert metrics["delay_sum_min"] == 80.0 and metrics["undetected_theft_min"] == 30.0


def test_phase_a_baseline_variant_reproduces_standard_adaptive() -> None:
    protocol = STAGES["E5"]
    model = train_global_model(protocol, train_replicates=1, days=2, n_jobs=1)
    rows = pd.DataFrame(run_realization(protocol, 2, 1, model, 2))
    weighted = rows[(rows["probability_source"] == "decision_probability") & (rows["fusion_strategy"] == "weighted")].set_index("policy_name")
    columns = ["communication_bytes", "tp", "fp", "fn", "episodes_detected", "delay_sum_min"]
    pd.testing.assert_series_equal(weighted.loc["adaptive", columns], weighted.loc["adaptive_b60", columns], check_names=False)
