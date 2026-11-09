from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.config import build_config
from fraud_dt.control import PolicyOrchestrator
from fraud_dt.decision import DecisionEngine, WeightedProbabilityFusion
from fraud_dt.synthetic import generate_synthetic_dataset
from fraud_dt.features import build_feature_dataset, load_input_dataset
from fraud_dt.risk import score_rule_based_risk, train_supervised_baseline
from fraud_dt.twin import ForensicTwin


def _build_event_row(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    generate_synthetic_dataset(raw_dir, days=2, seed=7)
    forensic_df, billing_df, alarm_df = load_input_dataset(raw_dir)
    merged_df = build_feature_dataset(forensic_df, billing_df, alarm_df)
    scored_df = score_rule_based_risk(merged_df)
    supervised_df, _ = train_supervised_baseline(scored_df)
    return supervised_df.sort_values("timestamp").iloc[0].to_dict(), build_config(tmp_path)


def test_twin_updates_state_after_command(tmp_path: Path) -> None:
    row, config = _build_event_row(tmp_path)
    twin = ForensicTwin(dev_eui=row["dev_eui"], initial_capture_period_minutes=config.policy.basal_minutes)
    observation = twin.observe(0, row)
    engine = DecisionEngine(config.thresholds)
    decision = engine.evaluate(observation)
    orchestrator = PolicyOrchestrator(config.policy, config.thresholds)
    command = orchestrator.build_command(twin, decision)
    twin.apply_command(command)
    snapshot = twin.snapshot(observation, decision)

    assert snapshot.current_mode == command.selected_mode
    assert snapshot.capture_period_minutes == command.capture_period_minutes
    assert snapshot.last_command_id == command.command_id
    assert snapshot.last_decision_probability == decision.decision_probability
