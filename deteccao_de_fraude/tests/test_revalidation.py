from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np
import pandas as pd

from fraud_dt.features import (
    OnlineFeatureState,
    build_feature_dataset,
    causal_slot_recurrence,
    load_input_dataset,
    recompute_features_on_received,
)
from fraud_dt.revalidation import STAGES, phase_offset_minutes, run_realization, evaluation_seed, training_seed
from fraud_dt.risk import FrozenSupervisedModel, score_rule_based_record, score_rule_based_risk
from fraud_dt.schemas import Scenario
from fraud_dt.synthetic import generate_synthetic_dataset, generate_synthetic_frames


def _frames_to_merged(frames, fix_slot=False):
    forensic_df, billing_df, alarm_df = (frame.copy() for frame in frames)
    for frame in (forensic_df, billing_df, alarm_df):
        frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    return build_feature_dataset(forensic_df, billing_df, alarm_df, fix_slot_recurrence=fix_slot)


def test_in_memory_generator_matches_csv_generator(tmp_path: Path) -> None:
    generate_synthetic_dataset(tmp_path, days=2, scenario=Scenario.INTERMITTENT_EVENING, seed=11)
    from_csv = build_feature_dataset(*load_input_dataset(tmp_path))
    in_memory = _frames_to_merged(generate_synthetic_frames(days=2, scenario=Scenario.INTERMITTENT_EVENING, seed=11))
    pd.testing.assert_frame_equal(from_csv, in_memory, check_dtype=False)


def test_onset_jitter_off_reproduces_v1_and_on_shifts_onsets() -> None:
    plain = generate_synthetic_frames(days=7, scenario=Scenario.PEAK_THEFT, seed=44)
    jittered = generate_synthetic_frames(days=7, scenario=Scenario.PEAK_THEFT, seed=44, onset_jitter=True)
    alarms = jittered[2].assign(ts=pd.to_datetime(jittered[2]["timestamp"]))
    onsets = alarms[alarms["theft_active"] == 1].groupby(alarms["ts"].dt.date)["ts"].min()
    assert (onsets.dt.minute % 5 == 0).all()
    assert (onsets.dt.minute > 0).any()
    assert int(plain[2]["theft_active"].sum()) == int(jittered[2]["theft_active"].sum())


def test_causal_slot_recurrence_uses_only_earlier_rows() -> None:
    merged = _frames_to_merged(generate_synthetic_frames(days=3, scenario=Scenario.PEAK_THEFT, seed=5), fix_slot=True)
    first_day = merged["timestamp"] < merged["timestamp"].iloc[0] + pd.Timedelta(days=1)
    first_hour_rows = merged.groupby("hour").head(1)
    assert (first_hour_rows["slot_recurrence"] == 0.0).all()
    perturbed = merged.copy()
    perturbed.loc[~first_day, "divergence_flag"] = 1 - perturbed.loc[~first_day, "divergence_flag"]
    recomputed = causal_slot_recurrence(perturbed)
    np.testing.assert_allclose(recomputed[first_day], merged.loc[first_day, "slot_recurrence"])


def test_online_features_match_batch_recomputation_on_received_samples() -> None:
    merged = _frames_to_merged(generate_synthetic_frames(days=2, scenario=Scenario.INTERMITTENT_EVENING, seed=9), fix_slot=True)
    rng = np.random.default_rng(0)
    received = merged.loc[np.sort(rng.choice(len(merged), size=150, replace=False))]
    batch = recompute_features_on_received(received)
    state = OnlineFeatureState()
    online = pd.DataFrame([state.update(record) for record in received.to_dict("records")])
    for column in ["rolling_divergence_mean", "rolling_divergence_max", "slot_recurrence"]:
        np.testing.assert_allclose(online[column].to_numpy(), batch[column].to_numpy(), atol=1e-12)


def test_frozen_model_record_prediction_matches_batch_and_rule_record_matches_batch() -> None:
    frames = [
        _frames_to_merged(generate_synthetic_frames(days=2, scenario=scenario, seed=training_seed(i, 0)), fix_slot=True)
        for i, scenario in enumerate([Scenario.NORMAL, Scenario.PEAK_THEFT])
    ]
    train = score_rule_based_risk(pd.concat(frames, ignore_index=True))
    model = FrozenSupervisedModel().fit(train)
    batch = model.predict_proba(train)
    pipeline = model.pipeline.predict_proba(train[[c for c in train.columns]])[:, 1]
    np.testing.assert_allclose(batch, pipeline, atol=1e-10)
    records = train.head(50).to_dict("records")
    np.testing.assert_allclose([model.predict_record(r) for r in records], batch[:50], atol=1e-10)
    np.testing.assert_allclose([score_rule_based_record(r) for r in records], train["risk_probability"].head(50))


def test_seed_rules_are_disjoint_and_phase_is_on_grid() -> None:
    test_seeds = {evaluation_seed(i, k) for i in range(7) for k in range(100)}
    train_seeds = {training_seed(i, j) for i in range(7) for j in range(100)}
    assert not test_seeds & train_seeds
    offsets = {phase_offset_minutes(seed) for seed in test_seeds}
    assert offsets <= set(range(0, 60, 5)) and len(offsets) > 1


def test_e0_replicate_zero_reproduces_submitted_table5_peak_theft() -> None:
    rows = pd.DataFrame(run_realization(STAGES["E0"], 2, 0, None, 7))
    adaptive = rows[(rows.policy_name == "adaptive") & (rows.probability_source == "decision_probability") & (rows.fusion_strategy == "weighted")].iloc[0]
    dense = rows[(rows.policy_name == "fixed_dense") & (rows.probability_source == "supervised_probability")].iloc[0]
    assert round(adaptive.f1, 4) == 0.9159 and round(adaptive.recall, 4) == 0.8625 and adaptive.communication_bytes == 30324
    assert round(dense.f1, 4) == 0.9264 and round(dense.recall, 4) == 0.9958 and dense.communication_bytes == 134952
