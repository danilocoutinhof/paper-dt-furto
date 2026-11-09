from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.config import build_config
from fraud_dt.control import PolicyOrchestrator
from fraud_dt.decision import DecisionEngine
from fraud_dt.devices import MockTransport
from fraud_dt.features import build_feature_dataset, load_input_dataset
from fraud_dt.risk import score_rule_based_risk, train_supervised_baseline
from fraud_dt.runtime import SimulationRunner
from fraud_dt.schemas import Scenario
from fraud_dt.synthetic import generate_synthetic_dataset


def test_closed_loop_runtime_generates_transport_and_state_artifacts(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    generate_synthetic_dataset(raw_dir, days=2, scenario=Scenario.INTERMITTENT_EVENING, seed=7)
    forensic_df, billing_df, alarm_df = load_input_dataset(raw_dir)
    merged_df = build_feature_dataset(forensic_df, billing_df, alarm_df)
    scored_df = score_rule_based_risk(merged_df)
    supervised_df, _ = train_supervised_baseline(scored_df)
    config = build_config(tmp_path)

    runner = SimulationRunner(
        config=config,
        decision_engine=DecisionEngine(config.thresholds),
        orchestrator=PolicyOrchestrator(config.policy, config.thresholds),
        transport=MockTransport(ble_available=True),
    )
    adaptive_df, decision_df, state_df, command_df, transport_df = runner.run(supervised_df)

    assert not adaptive_df.empty
    assert not decision_df.empty
    assert not state_df.empty
    assert not command_df.empty
    assert not transport_df.empty
    assert "observed" in adaptive_df.columns
    assert int(adaptive_df["observed"].sum()) < len(adaptive_df)
    assert "selected_transport" in transport_df.columns
