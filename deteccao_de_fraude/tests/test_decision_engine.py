from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.config import Thresholds
from fraud_dt.decision import ConservativeMaxFusion, DecisionEngine, WeightedProbabilityFusion
from fraud_dt.twin.models import TwinObservation
import pandas as pd


def _observation(rule_probability: float, supervised_probability: float | None) -> TwinObservation:
    return TwinObservation(
        event_index=0,
        dev_eui="dev",
        timestamp=pd.Timestamp("2026-01-01T00:00:00"),
        relative_divergence=0.12,
        rolling_divergence_mean=0.09,
        rolling_divergence_max=0.15,
        slot_recurrence=0.4,
        alarm_score=1.0,
        operational_penalty=0.0,
        hour=18,
        day_of_week=3,
        link_ok=1,
        heartbeat_ok=1,
        risk_probability=rule_probability,
        supervised_probability=supervised_probability,
        theft_active=1,
    )


def test_weighted_fusion_is_used_by_default() -> None:
    engine = DecisionEngine(Thresholds(), fusion_strategy=WeightedProbabilityFusion(rule_weight=0.6, supervised_weight=0.4))
    decision = engine.evaluate(_observation(0.7, 0.5))
    assert round(decision.decision_probability, 4) == 0.62
    assert decision.probability_source == "weighted_rule_supervised"
    assert decision.risk_class == "high"


def test_conservative_max_fusion_prefers_highest_signal() -> None:
    engine = DecisionEngine(Thresholds(), fusion_strategy=ConservativeMaxFusion())
    decision = engine.evaluate(_observation(0.31, 0.72))
    assert round(decision.decision_probability, 4) == 0.72
    assert decision.probability_source == "max_rule_supervised"
    assert "supervised_support" in decision.rationale
