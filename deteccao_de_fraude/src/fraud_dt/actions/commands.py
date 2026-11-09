from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import pandas as pd


@dataclass(frozen=True)
class TelemetryReconfigurationDecision:
    target_dev_eui: str
    issued_at: pd.Timestamp
    selected_mode: str
    capture_period_minutes: int
    probability_value: float
    probability_source: str
    reason: str
    action: str
    command_id: str = field(default_factory=lambda: uuid4().hex)
    transport_preference: str = "auto"
    priority: str = "normal"
    expires_at: pd.Timestamp | None = None
    applied: bool = True
    ack_status: str = "applied_local_mock"

    def to_record(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "target_dev_eui": self.target_dev_eui,
            "issued_at": self.issued_at,
            "selected_mode": self.selected_mode,
            "capture_period_minutes": self.capture_period_minutes,
            "probability_value": self.probability_value,
            "probability_source": self.probability_source,
            "reason": self.reason,
            "action": self.action,
            "transport_preference": self.transport_preference,
            "priority": self.priority,
            "expires_at": self.expires_at,
            "applied": self.applied,
            "ack_status": self.ack_status,
        }
