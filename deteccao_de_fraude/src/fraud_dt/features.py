from __future__ import annotations

import pandas as pd


def load_input_dataset(input_dir):
    forensic_df = pd.read_csv(input_dir / "forensic_measurements.csv", parse_dates=["timestamp"])
    billing_df = pd.read_csv(input_dir / "billing_measurements.csv", parse_dates=["timestamp"])
    alarm_df = pd.read_csv(input_dir / "alarm_events.csv", parse_dates=["timestamp"])
    return forensic_df, billing_df, alarm_df


def build_feature_dataset(
    forensic_df: pd.DataFrame,
    billing_df: pd.DataFrame,
    alarm_df: pd.DataFrame,
    fix_slot_recurrence: bool = False,
) -> pd.DataFrame:
    """Merges the three streams and derives the risk features on the native grid.

    `fix_slot_recurrence=False` keeps the v1 computation (needed to reproduce
    the submitted results). In v1 the positional `shift(1)` is applied after
    the per-hour groups are flattened, so the first row of each hour-of-day
    group receives the last expanding mean of the *previous* hour group,
    which includes future samples. `fix_slot_recurrence=True` (revalidation
    stage E2 onward) computes, for each row, the mean of the divergence flag
    over strictly earlier rows of the same hour of day only.
    """
    df = forensic_df.merge(billing_df, on=["timestamp", "dev_eui"], how="inner")
    df = df.merge(alarm_df, on=["timestamp", "dev_eui"], how="left")
    df = df.sort_values("timestamp").reset_index(drop=True)

    df["divergence_power"] = df["active_power"] - df["billing_active_power"]
    df["divergence_energy"] = df["active_energy"] - df["billing_active_energy"]
    df["relative_divergence"] = (df["divergence_power"] / df["active_power"]).clip(lower=0.0)
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["divergence_flag"] = (df["relative_divergence"] > 0.08).astype(int)

    # Rolling windows are defined in real time (not in sample count) so that
    # their meaning is independent of the native acquisition resolution. This
    # matters because the native resolution was changed from 15 to 5 minutes
    # to make the "aggressive"/"moderate"/"basal" observation modes
    # genuinely distinguishable (see synthetic.py); a sample-count window
    # would silently triple in duration under the new resolution.
    time_indexed = df.set_index("timestamp")
    df["rolling_divergence_mean"] = (
        time_indexed["relative_divergence"].rolling("60min", min_periods=1).mean().to_numpy()
    )
    df["rolling_divergence_max"] = (
        time_indexed["relative_divergence"].rolling("120min", min_periods=1).max().to_numpy()
    )

    if fix_slot_recurrence:
        df["slot_recurrence"] = causal_slot_recurrence(df)
    else:
        slot_history = (
            df.groupby("hour")["divergence_flag"]
            .expanding()
            .mean()
            .reset_index(level=0, drop=True)
            .shift(1)
            .fillna(0.0)
        )
        df["slot_recurrence"] = slot_history

    df["alarm_score"] = (
        df[[
            "alarm_overvoltage",
            "alarm_undervoltage",
            "alarm_overcurrent",
            "alarm_last_gasp",
            "alarm_out_of_bounds_power",
        ]]
        .sum(axis=1)
        .astype(float)
    )
    df["operational_penalty"] = ((1 - df["link_ok"]) + (1 - df["heartbeat_ok"])) / 2.0
    return df


ROLLING_MEAN_WINDOW = "60min"
ROLLING_MAX_WINDOW = "120min"


def causal_slot_recurrence(df: pd.DataFrame) -> pd.Series:
    """Mean of `divergence_flag` over strictly earlier rows with the same hour
    of day (0.0 when there is no earlier row). `df` must be time-ordered."""
    return (
        df.groupby("hour")["divergence_flag"]
        .transform(lambda s: s.shift(1).expanding().mean())
        .fillna(0.0)
    )


def recompute_features_on_received(df: pd.DataFrame) -> pd.DataFrame:
    """Recomputes the history-dependent features using only the rows in `df`.

    Used in revalidation stage E4 ("emitted" feature mode): `df` holds only
    the samples a policy actually transmitted, so the rolling windows and the
    hour-of-day recurrence are computed from what reaches the back-office,
    not from the native 5-min grid. Instantaneous fields (divergence, alarms,
    operational penalty) are unchanged, because they belong to the sample
    itself. Same window semantics as `build_feature_dataset` (time-based,
    right-closed) and the causal slot recurrence.
    """
    out = df.sort_values("timestamp").reset_index(drop=True).copy()
    if out.empty:
        return out
    time_indexed = out.set_index("timestamp")
    out["rolling_divergence_mean"] = (
        time_indexed["relative_divergence"].rolling(ROLLING_MEAN_WINDOW, min_periods=1).mean().to_numpy()
    )
    out["rolling_divergence_max"] = (
        time_indexed["relative_divergence"].rolling(ROLLING_MAX_WINDOW, min_periods=1).max().to_numpy()
    )
    out["slot_recurrence"] = causal_slot_recurrence(out).to_numpy()
    return out


class OnlineFeatureState:
    """Incremental version of `recompute_features_on_received` for the closed
    loop: each call receives one emitted sample and returns it with the
    history-dependent features computed from the samples received so far
    (including the current one for the rolling windows; strictly earlier
    ones for the slot recurrence)."""

    def __init__(self) -> None:
        from collections import deque

        self._window: deque = deque()
        self._slot_sum = [0.0] * 24
        self._slot_count = [0] * 24

    def update(self, record: dict) -> dict:
        ts = pd.Timestamp(record["timestamp"])
        divergence = float(record["relative_divergence"])
        self._window.append((ts, divergence))
        max_cutoff = ts - pd.Timedelta(ROLLING_MAX_WINDOW)
        while self._window and self._window[0][0] <= max_cutoff:
            self._window.popleft()
        mean_cutoff = ts - pd.Timedelta(ROLLING_MEAN_WINDOW)
        recent = [value for stamp, value in self._window if stamp > mean_cutoff]

        hour = int(record["hour"])
        count = self._slot_count[hour]
        slot_recurrence = self._slot_sum[hour] / count if count else 0.0
        self._slot_sum[hour] += float(record["divergence_flag"])
        self._slot_count[hour] += 1

        out = dict(record)
        out["rolling_divergence_mean"] = float(sum(recent) / len(recent))
        out["rolling_divergence_max"] = float(max(value for _, value in self._window))
        out["slot_recurrence"] = float(slot_recurrence)
        return out
