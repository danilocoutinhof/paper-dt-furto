from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from fraud_dt.actions import TelemetryReconfigurationDecision


@dataclass
class MockForensicDevice:
    dev_eui: str
    initial_capture_period_minutes: int
    current_capture_period_minutes: int | None = None
    next_emit_time: pd.Timestamp | None = None
    last_emit_time: pd.Timestamp | None = None

    def __post_init__(self) -> None:
        if self.current_capture_period_minutes is None:
            self.current_capture_period_minutes = self.initial_capture_period_minutes

    def should_emit(self, timestamp: pd.Timestamp) -> bool:
        if self.next_emit_time is None:
            return True
        return timestamp >= self.next_emit_time

    def mark_emitted(self, timestamp: pd.Timestamp) -> None:
        self.last_emit_time = timestamp
        self.next_emit_time = timestamp + pd.Timedelta(minutes=int(self.current_capture_period_minutes))

    def apply_command(self, command: TelemetryReconfigurationDecision) -> None:
        self.current_capture_period_minutes = int(command.capture_period_minutes)
        if self.last_emit_time is not None:
            self.next_emit_time = self.last_emit_time + pd.Timedelta(minutes=self.current_capture_period_minutes)
