from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.decision import ContextAwareFusion
from fraud_dt.twin.models import TwinObservation
import pandas as pd


def test_context_aware_fusion_prefers_rule_signal_when_alarm_context_is_present() -> None:
    fusion = ContextAwareFusion()
    observation = TwinObservation(
        event_index=0,
        dev_eui="dev",
        timestamp=pd.Timestamp("2026-01-01T18:00:00"),
        relative_divergence=0.11,
        rolling_divergence_mean=0.07,
        rolling_divergence_max=0.14,
        slot_recurrence=0.10,
        alarm_score=1.0,
        operational_penalty=0.0,
        hour=18,
        day_of_week=3,
        link_ok=1,
        heartbeat_ok=1,
        risk_probability=0.80,
        supervised_probability=0.40,
        theft_active=1,
    )
    probability, source = fusion.fuse(observation)
    assert round(probability, 4) == 0.70
    assert source == "context_rule_dominant"


def test_context_aware_fusion_prefers_supervised_signal_in_recurrent_evening_pattern() -> None:
    fusion = ContextAwareFusion()
    observation = TwinObservation(
        event_index=0,
        dev_eui="dev",
        timestamp=pd.Timestamp("2026-01-01T20:00:00"),
        relative_divergence=0.04,
        rolling_divergence_mean=0.03,
        rolling_divergence_max=0.05,
        slot_recurrence=0.50,
        alarm_score=0.0,
        operational_penalty=0.0,
        hour=20,
        day_of_week=3,
        link_ok=1,
        heartbeat_ok=1,
        risk_probability=0.30,
        supervised_probability=0.70,
        theft_active=1,
    )
    probability, source = fusion.fuse(observation)
    assert round(probability, 4) == 0.56
    assert source == "context_supervised_dominant"
