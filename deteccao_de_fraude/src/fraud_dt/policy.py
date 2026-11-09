from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import ObservationPolicy, Thresholds


@dataclass(frozen=True)
class PolicyFrameNames:
    ADAPTIVE: str = "adaptive"
    FIXED_LONG: str = "fixed_long"
    FIXED_SHORT: str = "fixed_short"
    FIXED_DENSE: str = "fixed_dense"


def apply_adaptive_policy(
    df: pd.DataFrame,
    thresholds: Thresholds,
    policy: ObservationPolicy,
) -> pd.DataFrame:
    df = df.copy()
    modes = []
    capture_periods = []
    previous_mode = "basal"
    dwell = 0
    probability_column = "decision_probability" if "decision_probability" in df.columns else "risk_probability"

    for _, row in df.iterrows():
        risk = float(row[probability_column])
        if previous_mode == "aggressive" and risk > thresholds.moderate_risk and dwell < 3:
            mode = "aggressive"
            dwell += 1
        elif previous_mode == "moderate" and risk > (thresholds.moderate_risk * 0.8) and dwell < 2:
            mode = "moderate"
            dwell += 1
        else:
            if risk >= thresholds.high_risk:
                mode = "aggressive"
            elif risk >= thresholds.moderate_risk:
                mode = "moderate"
            else:
                mode = "basal"
            dwell = 1

        if mode != previous_mode:
            dwell = 1
        previous_mode = mode
        modes.append(mode)

        if mode == "aggressive":
            capture_periods.append(policy.aggressive_minutes)
        elif mode == "moderate":
            capture_periods.append(policy.moderate_minutes)
        else:
            capture_periods.append(policy.basal_minutes)

    df["policy_name"] = PolicyFrameNames.ADAPTIVE
    df["observation_mode"] = modes
    df["capture_period_minutes"] = capture_periods
    return df


def apply_fixed_long_policy(df: pd.DataFrame, policy: ObservationPolicy) -> pd.DataFrame:
    out = df.copy()
    out["policy_name"] = PolicyFrameNames.FIXED_LONG
    out["observation_mode"] = "fixed_long"
    out["capture_period_minutes"] = policy.fixed_long_minutes
    return out


def apply_fixed_short_policy(df: pd.DataFrame, policy: ObservationPolicy) -> pd.DataFrame:
    out = df.copy()
    out["policy_name"] = PolicyFrameNames.FIXED_SHORT
    out["observation_mode"] = "fixed_short"
    out["capture_period_minutes"] = policy.fixed_short_minutes
    return out


def apply_fixed_dense_policy(df: pd.DataFrame, policy: ObservationPolicy) -> pd.DataFrame:
    """Reports at the native acquisition resolution (see
    `ObservationPolicy.fixed_dense_minutes`): the true dense-monitoring
    ceiling, distinct from `fixed_short`."""
    out = df.copy()
    out["policy_name"] = PolicyFrameNames.FIXED_DENSE
    out["observation_mode"] = "fixed_dense"
    out["capture_period_minutes"] = policy.fixed_dense_minutes
    return out
