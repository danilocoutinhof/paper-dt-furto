from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.actions import TelemetryReconfigurationDecision
import pandas as pd


def test_command_plan_record_contains_core_fields() -> None:
    command = TelemetryReconfigurationDecision(
        target_dev_eui="dev",
        issued_at=pd.Timestamp("2026-01-01T00:00:00"),
        selected_mode="aggressive",
        capture_period_minutes=5,
        probability_value=0.91,
        probability_source="weighted_rule_supervised",
        reason="risk_class=high",
        action="reconfigure",
    )
    record = command.to_record()
    assert record["selected_mode"] == "aggressive"
    assert record["capture_period_minutes"] == 5
    assert record["action"] == "reconfigure"
    assert record["command_id"]
