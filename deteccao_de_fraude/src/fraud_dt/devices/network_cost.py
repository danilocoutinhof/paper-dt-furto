from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class NbIotLinkProfile:
    """Parametrized NB-IoT/BLE communication-cost model.

    This replaces a flat "bytes per observed sample" proxy, which a reviewer
    correctly pointed out did not reflect any NB-IoT-specific characteristic
    (latency, retransmission, signaling overhead). Device energy consumption
    is deliberately NOT modeled: the forensic device is mains-powered from
    the distribution network itself and is available full-time, so battery
    life is not an operational constraint for this system; the utility's
    actual cost driver is the volume/cost of transmitted data, which this
    model targets instead.

    The numeric defaults are engineering approximations grounded in reported
    NB-IoT field/measurement studies rather than a carrier-specific claim:
    `base_latency_ms` (1600 ms) sits within the <2 s outdoor / <8 s deep-indoor
    round-trip latency range measured on a commercial NB-IoT network for a
    smart-grid control use case (Sultania and Famaey, "Real-Time Demand
    Response Using NB-IoT," IEEE Internet of Things Journal, 2020);
    `rrc_setup_overhead_bytes` represents a legacy (non-EDT) control-plane
    connection setup, consistent with the small-message regime (this
    system's payload is 64 B) for which Release-15 Early Data Transmission
    is reported to roughly halve transmission delay and reduce overhead
    (Stusek et al., "Exploiting NB-IoT Network Performance and Capacity for
    Smart-Metering Use-Cases," ICUMT, 2023); the retransmission-probability
    asymmetry between nominal and degraded link states reflects the
    coverage-dependent repetition behavior characterized by systematic QoS
    measurements of commercial NB-IoT deployments (Matz et al., "A
    Systematic Analysis of Narrowband IoT Quality of Service," Sensors,
    2020). The energy-latency Pareto-front methodology used by Sultania and
    Famaey ("Optimizing the Energy-Latency Tradeoff in NB-IoT With PSM and
    eDRX," IEEE Internet of Things Journal, 2021) is mirrored, in spirit, by
    the detection-vs-communication-cost Pareto analysis in
    `scripts/run_policy_optimization.py`.
    """

    payload_bytes_per_sample: int = 64
    rrc_setup_overhead_bytes: int = 40
    connection_reuse_window_minutes: int = 15
    base_latency_ms: float = 1600.0
    retransmission_latency_penalty_ms: float = 900.0
    nominal_link_retransmission_probability: float = 0.04
    degraded_link_retransmission_probability: float = 0.35
    max_retransmissions: int = 3
    ble_base_latency_ms: float = 120.0
    ble_overhead_bytes: int = 20


def evaluate_single_transmission(
    *,
    timestamp: pd.Timestamp,
    link_ok: bool,
    heartbeat_ok: bool,
    last_nbiot_transmission_time: pd.Timestamp | None,
    profile: NbIotLinkProfile,
    rng: np.random.Generator,
    ble_available: bool,
) -> dict:
    """Cost/latency outcome of one telemetry/command transmission attempt.

    Returns a dict with transport, byte accounting, retransmissions, latency,
    and the updated `last_nbiot_transmission_time` state (None when the
    transmission used BLE, since BLE fallback does not consume the NB-IoT
    connected-mode timer).
    """
    link_degraded = not (bool(link_ok) and bool(heartbeat_ok))

    if not link_degraded:
        transport = "nbiot"
    elif ble_available:
        transport = "ble"
    else:
        transport = "nbiot"

    if transport == "nbiot":
        fresh_connection = (
            last_nbiot_transmission_time is None
            or (timestamp - last_nbiot_transmission_time) > pd.Timedelta(minutes=profile.connection_reuse_window_minutes)
        )
        overhead_bytes = profile.rrc_setup_overhead_bytes if fresh_connection else 0
        retransmission_probability = (
            profile.degraded_link_retransmission_probability if link_degraded else profile.nominal_link_retransmission_probability
        )
        retransmissions = 0
        while retransmissions < profile.max_retransmissions and rng.random() < retransmission_probability:
            retransmissions += 1
        total_bytes = profile.payload_bytes_per_sample * (1 + retransmissions) + overhead_bytes
        latency_ms = profile.base_latency_ms + retransmissions * profile.retransmission_latency_penalty_ms
        updated_last_nbiot_time = timestamp
    else:
        overhead_bytes = profile.ble_overhead_bytes
        retransmissions = 0
        total_bytes = profile.payload_bytes_per_sample + overhead_bytes
        latency_ms = profile.ble_base_latency_ms
        updated_last_nbiot_time = last_nbiot_transmission_time

    return {
        "transport": transport,
        "fallback_used": transport == "ble",
        "overhead_bytes": overhead_bytes,
        "retransmissions": retransmissions,
        "total_bytes": total_bytes,
        "latency_ms": latency_ms,
        "last_nbiot_transmission_time": updated_last_nbiot_time,
    }


def estimate_communication_cost(
    df: pd.DataFrame,
    profile: NbIotLinkProfile,
    seed: int,
    ble_available: bool = True,
) -> pd.DataFrame:
    """Batch version of the per-event transmission cost model, used to cost
    fixed observation policies the same way the adaptive closed loop is
    costed by `MockTransport`. `df` must contain, for the observed rows only,
    `timestamp`, `link_ok`, and `heartbeat_ok`.
    """
    rng = np.random.default_rng(seed)
    last_nbiot_time: pd.Timestamp | None = None
    rows = []
    for _, row in df.iterrows():
        outcome = evaluate_single_transmission(
            timestamp=row["timestamp"],
            link_ok=bool(row["link_ok"]),
            heartbeat_ok=bool(row["heartbeat_ok"]),
            last_nbiot_transmission_time=last_nbiot_time,
            profile=profile,
            rng=rng,
            ble_available=ble_available,
        )
        last_nbiot_time = outcome.pop("last_nbiot_transmission_time")
        rows.append(outcome)
    if not rows:
        return pd.DataFrame(
            columns=["transport", "fallback_used", "overhead_bytes", "retransmissions", "total_bytes", "latency_ms"]
        )
    return pd.DataFrame(rows)
