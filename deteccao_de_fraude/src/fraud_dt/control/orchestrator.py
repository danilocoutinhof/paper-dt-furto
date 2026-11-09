from __future__ import annotations

from dataclasses import dataclass

from fraud_dt.actions import TelemetryReconfigurationDecision
from fraud_dt.config import ObservationPolicy, Thresholds
from fraud_dt.twin import ForensicTwin, TwinDecision


@dataclass
class PolicyOrchestrator:
    policy: ObservationPolicy
    thresholds: Thresholds

    def _select_mode(self, twin: ForensicTwin, decision: TwinDecision) -> str:
        probability = decision.decision_probability
        if twin.current_mode == "aggressive" and probability > self.thresholds.moderate_risk and twin.mode_dwell_events < 3:
            return "aggressive"
        if twin.current_mode == "moderate" and probability > (self.thresholds.moderate_risk * 0.8) and twin.mode_dwell_events < 2:
            return "moderate"
        if probability >= self.thresholds.high_risk:
            return "aggressive"
        if probability >= self.thresholds.moderate_risk:
            return "moderate"
        return "basal"

    def _capture_period_for_mode(self, mode: str) -> int:
        if mode == "aggressive":
            return self.policy.aggressive_minutes
        if mode == "moderate":
            return self.policy.moderate_minutes
        return self.policy.basal_minutes

    def build_command(self, twin: ForensicTwin, decision: TwinDecision) -> TelemetryReconfigurationDecision:
        selected_mode = self._select_mode(twin, decision)
        capture_period_minutes = self._capture_period_for_mode(selected_mode)
        action = "reconfigure" if (
            selected_mode != twin.current_mode or capture_period_minutes != twin.current_capture_period_minutes or twin.last_command_id == ""
        ) else "maintain"
        reason = (
            f"risk_class={decision.risk_class};source={decision.probability_source};"
            f"probability={decision.decision_probability:.4f};rationale={decision.rationale}"
        )
        return TelemetryReconfigurationDecision(
            target_dev_eui=twin.dev_eui,
            issued_at=decision.timestamp,
            selected_mode=selected_mode,
            capture_period_minutes=capture_period_minutes,
            probability_value=decision.decision_probability,
            probability_source=decision.probability_source,
            reason=reason,
            action=action,
        )
