from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.config import ObservationPolicy, Thresholds
from fraud_dt.control import PolicyOrchestrator
from fraud_dt.twin import ForensicTwin
from fraud_dt.twin.models import TwinDecision
import pandas as pd


def _decision(probability: float, risk_class: str = "moderate") -> TwinDecision:
    return TwinDecision(
        event_index=0,
        dev_eui="dev",
        timestamp=pd.Timestamp("2026-01-01T18:00:00"),
        rule_probability=probability,
        supervised_probability=probability,
        decision_probability=probability,
        probability_source="weighted_rule_supervised",
        risk_class=risk_class,
        rationale="divergence_flag,supervised_support",
    )


def test_policy_orchestrator_reconfigures_on_first_event() -> None:
    twin = ForensicTwin(dev_eui="dev", initial_capture_period_minutes=60)
    orchestrator = PolicyOrchestrator(ObservationPolicy(), Thresholds())
    command = orchestrator.build_command(twin, _decision(0.65, "high"))
    assert command.action == "reconfigure"
    assert command.selected_mode == "aggressive"
    assert command.capture_period_minutes == 5


def test_policy_orchestrator_maintains_mode_when_context_is_stable() -> None:
    twin = ForensicTwin(dev_eui="dev", initial_capture_period_minutes=15)
    twin.current_mode = "moderate"
    twin.current_capture_period_minutes = 15
    twin.mode_dwell_events = 1
    twin.last_command_id = "existing"
    orchestrator = PolicyOrchestrator(ObservationPolicy(), Thresholds())
    command = orchestrator.build_command(twin, _decision(0.42, "moderate"))
    assert command.action == "maintain"
    assert command.selected_mode == "moderate"
