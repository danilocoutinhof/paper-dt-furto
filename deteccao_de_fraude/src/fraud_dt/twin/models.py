from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class TwinObservation:
    event_index: int
    dev_eui: str
    timestamp: pd.Timestamp
    relative_divergence: float
    rolling_divergence_mean: float
    rolling_divergence_max: float
    slot_recurrence: float
    alarm_score: float
    operational_penalty: float
    hour: int
    day_of_week: int
    link_ok: int
    heartbeat_ok: int
    risk_probability: float
    supervised_probability: float | None
    theft_active: int | None

    @classmethod
    def from_record(cls, event_index: int, record: dict[str, Any]) -> "TwinObservation":
        supervised = record.get("supervised_probability")
        return cls(
            event_index=event_index,
            dev_eui=str(record["dev_eui"]),
            timestamp=pd.Timestamp(record["timestamp"]),
            relative_divergence=float(record["relative_divergence"]),
            rolling_divergence_mean=float(record["rolling_divergence_mean"]),
            rolling_divergence_max=float(record["rolling_divergence_max"]),
            slot_recurrence=float(record["slot_recurrence"]),
            alarm_score=float(record["alarm_score"]),
            operational_penalty=float(record["operational_penalty"]),
            hour=int(record["hour"]),
            day_of_week=int(record["day_of_week"]),
            link_ok=int(record["link_ok"]),
            heartbeat_ok=int(record["heartbeat_ok"]),
            risk_probability=float(record["risk_probability"]),
            supervised_probability=None if supervised is None or pd.isna(supervised) else float(supervised),
            theft_active=None if "theft_active" not in record or pd.isna(record["theft_active"]) else int(record["theft_active"]),
        )


@dataclass(frozen=True)
class TwinDecision:
    event_index: int
    dev_eui: str
    timestamp: pd.Timestamp
    rule_probability: float
    supervised_probability: float | None
    decision_probability: float
    probability_source: str
    risk_class: str
    rationale: str

    def to_record(self) -> dict[str, Any]:
        return {
            "event_index": self.event_index,
            "dev_eui": self.dev_eui,
            "timestamp": self.timestamp,
            "rule_probability": self.rule_probability,
            "supervised_probability": self.supervised_probability,
            "decision_probability": self.decision_probability,
            "probability_source": self.probability_source,
            "risk_class": self.risk_class,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class TwinStateSnapshot:
    event_index: int
    dev_eui: str
    timestamp: pd.Timestamp
    current_mode: str
    capture_period_minutes: int
    mode_dwell_events: int
    last_rule_probability: float
    last_supervised_probability: float | None
    last_decision_probability: float
    last_probability_source: str
    last_risk_class: str
    last_rationale: str
    last_command_id: str
    last_command_action: str
    last_command_reason: str

    def to_record(self) -> dict[str, Any]:
        return {
            "event_index": self.event_index,
            "dev_eui": self.dev_eui,
            "timestamp": self.timestamp,
            "current_mode": self.current_mode,
            "capture_period_minutes": self.capture_period_minutes,
            "mode_dwell_events": self.mode_dwell_events,
            "last_rule_probability": self.last_rule_probability,
            "last_supervised_probability": self.last_supervised_probability,
            "last_decision_probability": self.last_decision_probability,
            "last_probability_source": self.last_probability_source,
            "last_risk_class": self.last_risk_class,
            "last_rationale": self.last_rationale,
            "last_command_id": self.last_command_id,
            "last_command_action": self.last_command_action,
            "last_command_reason": self.last_command_reason,
        }
