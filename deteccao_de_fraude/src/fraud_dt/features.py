from __future__ import annotations

import pandas as pd


def load_input_dataset(input_dir):
    forensic_df = pd.read_csv(input_dir / "forensic_measurements.csv", parse_dates=["timestamp"])
    billing_df = pd.read_csv(input_dir / "billing_measurements.csv", parse_dates=["timestamp"])
    alarm_df = pd.read_csv(input_dir / "alarm_events.csv", parse_dates=["timestamp"])
    return forensic_df, billing_df, alarm_df


def build_feature_dataset(forensic_df: pd.DataFrame, billing_df: pd.DataFrame, alarm_df: pd.DataFrame) -> pd.DataFrame:
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
