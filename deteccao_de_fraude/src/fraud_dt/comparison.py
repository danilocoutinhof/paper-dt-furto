from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from .devices import NbIotLinkProfile, estimate_communication_cost


@dataclass(frozen=True)
class ComparisonSettings:
    payload_bytes_per_sample: int = 64
    prediction_threshold: float = 0.50
    critical_slot_tolerance_hours: float = 2.0
    link_profile: NbIotLinkProfile = field(default_factory=NbIotLinkProfile)
    cost_model_seed: int = 42
    """`link_profile`/`cost_model_seed` drive the same NB-IoT/BLE cost model
    used by the closed-loop `MockTransport`, so that fixed and adaptive
    policies are costed on a like-for-like basis (latency, retransmission,
    and signaling overhead), rather than the flat bytes-per-sample proxy a
    reviewer flagged as unrepresentative of NB-IoT."""
    """Standard deviation (in hours) of the Gaussian-decay relaxed critical-slot
    metric. The binary critical-slot-hit metric is too rigid: a one-hour
    temporal displacement between the predicted and the true busiest theft
    hour zeroes the metric even when the aggregate F1-score is high (e.g.
    0.8889). The relaxed score follows the temporal-tolerance evaluation
    principle formalized for time-series event detection by Salles et al.
    ("SoftED: Metrics for Soft Evaluation of Time Series Event Detection,"
    2023) and by Scharwächter et al. ("Statistical Evaluation of Anomaly
    Detectors for Sequences," 2020), and is reported alongside — not instead
    of — the binary metric, since Scharwächter et al. show that
    temporally-tolerant metrics can overestimate detector quality if used in
    isolation."""


def _circular_hour_distance(hour_a: int, hour_b: int) -> float:
    raw_distance = abs(hour_a - hour_b)
    return min(raw_distance, 24 - raw_distance)


def _mark_observed(df: pd.DataFrame) -> pd.DataFrame:
    if "observed" in df.columns:
        out = df.sort_values("timestamp").copy()
        out["observed"] = out["observed"].astype(int)
        return out

    df = df.sort_values("timestamp").copy()
    observed = []
    next_allowed_time = None
    for _, row in df.iterrows():
        ts = row["timestamp"]
        capture_period = int(row["capture_period_minutes"])
        if next_allowed_time is None or ts >= next_allowed_time:
            observed.append(1)
            next_allowed_time = ts + pd.Timedelta(minutes=capture_period)
        else:
            observed.append(0)
    df["observed"] = observed
    return df


def evaluate_policy(
    df: pd.DataFrame,
    probability_column: str,
    settings: ComparisonSettings,
) -> tuple[pd.DataFrame, dict]:
    eval_df = _mark_observed(df)
    eval_df["predicted_suspicious"] = (
        (eval_df[probability_column] >= settings.prediction_threshold) & (eval_df["observed"] == 1)
    ).astype(int)

    y_true = eval_df["theft_active"].astype(int)
    y_pred = eval_df["predicted_suspicious"].astype(int)
    observed_samples = int(eval_df["observed"].sum())

    observed_rows = eval_df.loc[eval_df["observed"] == 1, ["timestamp", "link_ok", "heartbeat_ok"]]
    transport_costs = estimate_communication_cost(
        observed_rows, settings.link_profile, seed=settings.cost_model_seed
    )
    if transport_costs.empty:
        communication_bytes = 0
        mean_latency_ms = 0.0
        total_retransmissions = 0
        ble_fallback_ratio = 0.0
    else:
        communication_bytes = int(transport_costs["total_bytes"].sum())
        mean_latency_ms = float(transport_costs["latency_ms"].mean())
        total_retransmissions = int(transport_costs["retransmissions"].sum())
        ble_fallback_ratio = float(transport_costs["fallback_used"].mean())

    theft_by_hour = eval_df.groupby("hour")["theft_active"].sum()
    pred_by_hour = eval_df.groupby("hour")["predicted_suspicious"].sum()
    true_critical_hour = int(theft_by_hour.idxmax()) if theft_by_hour.sum() > 0 else -1
    predicted_critical_hour = int(pred_by_hour.idxmax()) if pred_by_hour.sum() > 0 else -1
    critical_slot_hit = int(true_critical_hour == predicted_critical_hour)

    if true_critical_hour == -1 or predicted_critical_hour == -1:
        critical_slot_score_relaxed = float(critical_slot_hit)
    else:
        hour_distance = _circular_hour_distance(true_critical_hour, predicted_critical_hour)
        critical_slot_score_relaxed = math.exp(
            -(hour_distance**2) / (2.0 * settings.critical_slot_tolerance_hours**2)
        )

    summary = {
        "policy_name": str(eval_df["policy_name"].iloc[0]),
        "probability_source": probability_column,
        "samples": len(eval_df),
        "observed_samples": observed_samples,
        "observed_ratio": observed_samples / max(len(eval_df), 1),
        "communication_bytes": communication_bytes,
        "mean_latency_ms": mean_latency_ms,
        "total_retransmissions": total_retransmissions,
        "ble_fallback_ratio": ble_fallback_ratio,
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "critical_slot_true": true_critical_hour,
        "critical_slot_pred": predicted_critical_hour,
        "critical_slot_hit": critical_slot_hit,
        "critical_slot_score_relaxed": critical_slot_score_relaxed,
        "false_alert_rate": float(((y_pred == 1) & (y_true == 0)).sum() / max((y_true == 0).sum(), 1)),
    }
    return eval_df, summary
