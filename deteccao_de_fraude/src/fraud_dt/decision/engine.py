from __future__ import annotations

from dataclasses import dataclass, field

from fraud_dt.config import Thresholds
from fraud_dt.twin.models import TwinDecision, TwinObservation

from .fusion import ProbabilityFusionStrategy, WeightedProbabilityFusion


@dataclass
class DecisionEngine:
    thresholds: Thresholds
    fusion_strategy: ProbabilityFusionStrategy = field(default_factory=WeightedProbabilityFusion)

    def evaluate(self, observation: TwinObservation) -> TwinDecision:
        decision_probability, probability_source = self.fusion_strategy.fuse(observation)
        rationale_parts = []

        if observation.relative_divergence >= self.thresholds.divergence_ratio_flag:
            rationale_parts.append("divergence_flag")
        if observation.rolling_divergence_mean >= 0.06:
            rationale_parts.append("rolling_mean")
        if observation.rolling_divergence_max >= 0.12:
            rationale_parts.append("rolling_max")
        if observation.slot_recurrence >= 0.25:
            rationale_parts.append("slot_recurrence")
        if observation.alarm_score > 0:
            rationale_parts.append("alarm_context")
        if observation.operational_penalty > 0:
            rationale_parts.append("operational_penalty")
        if observation.supervised_probability is not None:
            rationale_parts.append("supervised_support")
        rationale_parts.append(f"fusion={self.fusion_strategy.strategy_name}")
        if not rationale_parts:
            rationale_parts.append("baseline_context")

        if decision_probability >= self.thresholds.high_risk:
            risk_class = "high"
        elif decision_probability >= self.thresholds.moderate_risk:
            risk_class = "moderate"
        else:
            risk_class = "low"

        return TwinDecision(
            event_index=observation.event_index,
            dev_eui=observation.dev_eui,
            timestamp=observation.timestamp,
            rule_probability=observation.risk_probability,
            supervised_probability=observation.supervised_probability,
            decision_probability=decision_probability,
            probability_source=probability_source,
            risk_class=risk_class,
            rationale=",".join(rationale_parts),
        )
