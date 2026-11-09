from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.actions import TelemetryReconfigurationDecision
from fraud_dt.devices import MockForensicDevice
import pandas as pd


def test_mock_forensic_device_respects_reconfigured_capture_period() -> None:
    device = MockForensicDevice(dev_eui="dev", initial_capture_period_minutes=60)
    t0 = pd.Timestamp("2026-01-01T00:00:00")
    assert device.should_emit(t0) is True
    device.mark_emitted(t0)
    assert device.should_emit(t0 + pd.Timedelta(minutes=15)) is False

    command = TelemetryReconfigurationDecision(
        target_dev_eui="dev",
        issued_at=t0,
        selected_mode="aggressive",
        capture_period_minutes=5,
        probability_value=0.9,
        probability_source="weighted_rule_supervised",
        reason="test",
        action="reconfigure",
    )
    device.apply_command(command)
    assert device.should_emit(t0 + pd.Timedelta(minutes=5)) is True


def test_aggressive_and_moderate_modes_are_operationally_distinguishable_at_native_resolution() -> None:
    """Regression guard for a methodological flaw found during peer review:
    with a 15-minute native data resolution, a 5-minute ('aggressive') and a
    15-minute ('moderate') capture period produced an identical emission
    pattern, because the device could never observe faster than data
    actually existed. The native resolution used across the project is now
    5 minutes (see `synthetic.NATIVE_INTERVAL_MINUTES`), so this test drives
    the device with 5-minute-spaced native ticks and asserts that the
    aggressive and moderate modes now emit at genuinely different densities.
    """
    native_ticks = [pd.Timestamp("2026-01-01T00:00:00") + pd.Timedelta(minutes=5 * i) for i in range(12)]

    aggressive_device = MockForensicDevice(dev_eui="dev", initial_capture_period_minutes=5)
    moderate_device = MockForensicDevice(dev_eui="dev", initial_capture_period_minutes=15)
    basal_device = MockForensicDevice(dev_eui="dev", initial_capture_period_minutes=60)

    def _count_emissions(device: MockForensicDevice) -> int:
        emitted = 0
        for ts in native_ticks:
            if device.should_emit(ts):
                emitted += 1
                device.mark_emitted(ts)
        return emitted

    aggressive_emissions = _count_emissions(aggressive_device)
    moderate_emissions = _count_emissions(moderate_device)
    basal_emissions = _count_emissions(basal_device)

    assert aggressive_emissions == 12  # every native tick
    assert moderate_emissions == 4  # every 3rd native tick (15 min / 5 min)
    assert basal_emissions == 1  # every 12th native tick (60 min / 5 min)
    assert aggressive_emissions > moderate_emissions > basal_emissions
