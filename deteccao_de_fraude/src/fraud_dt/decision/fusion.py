from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fraud_dt.twin.models import TwinObservation


class ProbabilityFusionStrategy(Protocol):
    strategy_name: str

    def fuse(self, observation: TwinObservation) -> tuple[float, str]:
        ...


@dataclass(frozen=True)
class WeightedProbabilityFusion:
    rule_weight: float = 0.6
    supervised_weight: float = 0.4
    strategy_name: str = "weighted"

    def fuse(self, observation: TwinObservation) -> tuple[float, str]:
        rule_probability = observation.risk_probability
        supervised_probability = observation.supervised_probability
        if supervised_probability is None:
            return rule_probability, "rule_only"
        fused_probability = (rule_probability * self.rule_weight) + (supervised_probability * self.supervised_weight)
        return min(max(fused_probability, 0.0), 0.99), "weighted_rule_supervised"


@dataclass(frozen=True)
class ConservativeMaxFusion:
    strategy_name: str = "conservative_max"

    def fuse(self, observation: TwinObservation) -> tuple[float, str]:
        probabilities = [observation.risk_probability]
        if observation.supervised_probability is not None:
            probabilities.append(observation.supervised_probability)
        return min(max(max(probabilities), 0.0), 0.99), "max_rule_supervised"


@dataclass(frozen=True)
class ContextAwareFusion:
    rule_dominant_weight: float = 0.75
    supervised_dominant_weight: float = 0.65
    balanced_rule_weight: float = 0.55
    strategy_name: str = "context_aware"

    def fuse(self, observation: TwinObservation) -> tuple[float, str]:
        rule_probability = observation.risk_probability
        supervised_probability = observation.supervised_probability
        if supervised_probability is None:
            return rule_probability, "rule_only"

        if observation.alarm_score > 0 or observation.rolling_divergence_max >= 0.12 or observation.operational_penalty > 0.0:
            fused_probability = (rule_probability * self.rule_dominant_weight) + (supervised_probability * (1.0 - self.rule_dominant_weight))
            source = "context_rule_dominant"
        elif observation.slot_recurrence >= 0.25 and observation.hour in {18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5}:
            fused_probability = (rule_probability * (1.0 - self.supervised_dominant_weight)) + (supervised_probability * self.supervised_dominant_weight)
            source = "context_supervised_dominant"
        else:
            fused_probability = (rule_probability * self.balanced_rule_weight) + (supervised_probability * (1.0 - self.balanced_rule_weight))
            source = "context_balanced"

        return min(max(fused_probability, 0.0), 0.99), source


def build_fusion_strategies() -> dict[str, ProbabilityFusionStrategy]:
    return {
        "weighted": WeightedProbabilityFusion(),
        "conservative_max": ConservativeMaxFusion(),
        "context_aware": ContextAwareFusion(),
    }
