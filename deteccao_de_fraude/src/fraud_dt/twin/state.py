from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fraud_dt.actions import TelemetryReconfigurationDecision

from .models import TwinDecision, TwinObservation, TwinStateSnapshot


@dataclass
class ForensicTwin:
    dev_eui: str
    initial_mode: str = "basal"
    initial_capture_period_minutes: int = 60
    current_mode: str = field(init=False)
    current_capture_period_minutes: int = field(init=False)
    mode_dwell_events: int = field(default=0, init=False)
    last_command_id: str = field(default="", init=False)
    last_command_action: str = field(default="bootstrap", init=False)
    last_command_reason: str = field(default="twin_initialized", init=False)

    def __post_init__(self) -> None:
        self.current_mode = self.initial_mode
        self.current_capture_period_minutes = self.initial_capture_period_minutes

    def observe(self, event_index: int, record: dict[str, Any]) -> TwinObservation:
        return TwinObservation.from_record(event_index, record)

    def apply_command(self, command: TelemetryReconfigurationDecision) -> None:
        if command.selected_mode == self.current_mode:
            self.mode_dwell_events += 1
        else:
            self.mode_dwell_events = 1

        self.current_mode = command.selected_mode
        self.current_capture_period_minutes = command.capture_period_minutes
        self.last_command_id = command.command_id
        self.last_command_action = command.action
        self.last_command_reason = command.reason

    def snapshot(self, observation: TwinObservation, decision: TwinDecision) -> TwinStateSnapshot:
        return TwinStateSnapshot(
            event_index=observation.event_index,
            dev_eui=self.dev_eui,
            timestamp=observation.timestamp,
            current_mode=self.current_mode,
            capture_period_minutes=self.current_capture_period_minutes,
            mode_dwell_events=self.mode_dwell_events,
            last_rule_probability=decision.rule_probability,
            last_supervised_probability=decision.supervised_probability,
            last_decision_probability=decision.decision_probability,
            last_probability_source=decision.probability_source,
            last_risk_class=decision.risk_class,
            last_rationale=decision.rationale,
            last_command_id=self.last_command_id,
            last_command_action=self.last_command_action,
            last_command_reason=self.last_command_reason,
        )
