from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any

import numpy as np
import pandas as pd

from fraud_dt.actions import TelemetryReconfigurationDecision

from .network_cost import NbIotLinkProfile, evaluate_single_transmission


@dataclass(frozen=True)
class TransportDelivery:
    command_id: str
    timestamp: pd.Timestamp
    selected_transport: str
    delivered: bool
    ack_status: str
    fallback_used: bool
    payload_bytes: int
    overhead_bytes: int
    retransmissions: int
    total_bytes: int
    latency_ms: float

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MockTransport:
    ble_available: bool = True
    link_profile: NbIotLinkProfile = field(default_factory=NbIotLinkProfile)
    cost_model_seed: int = 42
    _rng: np.random.Generator = field(init=False, repr=False)
    _last_nbiot_transmission_time: pd.Timestamp | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = np.random.default_rng(self.cost_model_seed)

    def deliver(
        self, command: TelemetryReconfigurationDecision, *, timestamp: pd.Timestamp, link_ok: int, heartbeat_ok: int
    ) -> tuple[TelemetryReconfigurationDecision, TransportDelivery]:
        outcome = evaluate_single_transmission(
            timestamp=timestamp,
            link_ok=bool(int(link_ok)),
            heartbeat_ok=bool(int(heartbeat_ok)),
            last_nbiot_transmission_time=self._last_nbiot_transmission_time,
            profile=self.link_profile,
            rng=self._rng,
            ble_available=self.ble_available,
        )
        self._last_nbiot_transmission_time = outcome["last_nbiot_transmission_time"]

        ack_status = "applied_local_mock"
        delivered_command = replace(
            command,
            transport_preference=outcome["transport"],
            ack_status=ack_status,
            applied=True,
        )
        delivery = TransportDelivery(
            command_id=command.command_id,
            timestamp=timestamp,
            selected_transport=outcome["transport"],
            delivered=True,
            ack_status=ack_status,
            fallback_used=outcome["fallback_used"],
            payload_bytes=self.link_profile.payload_bytes_per_sample,
            overhead_bytes=outcome["overhead_bytes"],
            retransmissions=outcome["retransmissions"],
            total_bytes=outcome["total_bytes"],
            latency_ms=outcome["latency_ms"],
        )
        return delivered_command, delivery
