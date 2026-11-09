from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.actions import TelemetryReconfigurationDecision
from fraud_dt.devices import MockTransport
import pandas as pd


def test_mock_transport_falls_back_to_ble_when_link_is_degraded() -> None:
    transport = MockTransport(ble_available=True)
    command = TelemetryReconfigurationDecision(
        target_dev_eui="dev",
        issued_at=pd.Timestamp("2026-01-01T00:00:00"),
        selected_mode="moderate",
        capture_period_minutes=15,
        probability_value=0.5,
        probability_source="weighted_rule_supervised",
        reason="test",
        action="reconfigure",
    )
    delivered_command, delivery = transport.deliver(
        command,
        timestamp=pd.Timestamp("2026-01-01T00:00:00"),
        link_ok=0,
        heartbeat_ok=0,
    )
    assert delivered_command.transport_preference == "ble"
    assert delivery.fallback_used is True
    assert delivery.selected_transport == "ble"
