from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import DEFAULT_DEV_EUI
from .schemas import Scenario

# --- Native temporal resolution -------------------------------------------------
# The native tick is set to the finest granularity offered to the observation
# policy (the "aggressive" capture period, 5 minutes). This is a deliberate fix
# for a methodological flaw identified during peer review: with a 15-minute
# native resolution, a 5-minute "aggressive" observation mode and a 15-minute
# "moderate" mode were operationally indistinguishable (the forensic-device
# emission gate can never observe faster than the data actually exists).
# basal (60 min), moderate (15 min) and aggressive (5 min) are now exact
# multiples of the native tick, so each mode induces a genuinely different
# observation density.
NATIVE_INTERVAL_MINUTES = 5
INTERVAL_HOURS = NATIVE_INTERVAL_MINUTES / 60.0
NOMINAL_VOLTAGE = 220.0

# --- Metrological noise and realism parameters ----------------------------------
# These parameters were introduced to address a second methodological flaw
# identified during peer review: in the original generator, the divergence
# between the forensic and billing meters was an almost-deterministic function
# of the synthetic theft ratio, which was at the same time the only feature
# used for detection. This made the classification problem artificially easy
# (near-perfect precision/recall/F1/AUROC) and is not representative of a real
# metering environment. The parameters below add independent, theft-unrelated
# sources of divergence and communication degradation.
SENSOR_NOISE_RELATIVE_STD = 0.012
"""Independent per-meter metrological noise (~1.2% relative std), applied
separately to the forensic and billing readings, unrelated to theft."""

COMMUNICATION_GLITCH_PROBABILITY = 0.03
"""Per-tick probability of a transient reporting glitch (stale/erroneous
telemetry) affecting either meter, independent of theft activity."""

COMMUNICATION_GLITCH_RELATIVE_MAGNITUDE = 0.09
"""Relative magnitude of a communication glitch, comparable in size to a
low-severity ('stealth') theft event, so that noise and weak fraud are not
trivially separable."""

BENIGN_LOAD_SURGE_PROBABILITY = 0.015
"""Per-tick probability of a legitimate but erratic load surge (e.g. a large
appliance motor start), independent of theft, that can transiently raise
current/power and occasionally cross alarm thresholds."""

CONTRACTED_DEMAND_LIMIT_W = 1650.0
"""Physical over-demand threshold used for `alarm_out_of_bounds_power`.
Deliberately defined from the forensic meter alone (never from the
forensic-vs-billing gap) so that this alarm cannot leak the detection label,
unlike the original implementation."""

BYPASS_ARTIFACT_PROBABILITY = 0.25
"""Probability that a high-severity ('full_diversion') theft tick also
produces a transient electrical artifact (e.g. current imbalance from a
bypass connection), modeled as a probabilistic, non-deterministic nudge to
the overcurrent alarm rather than a guaranteed signal."""


def _base_load_profile(hour: int) -> float:
    if 0 <= hour < 6:
        return 350.0
    if 6 <= hour < 12:
        return 700.0
    if 12 <= hour < 18:
        return 950.0
    return 1400.0


def _theft_active(timestamp: pd.Timestamp, scenario: Scenario, rng: np.random.Generator) -> int:
    hour = timestamp.hour
    if scenario == Scenario.NORMAL:
        return 0
    if scenario == Scenario.PERSISTENT_THEFT:
        return 1
    if scenario == Scenario.PEAK_THEFT:
        return int(18 <= hour < 22)
    if scenario == Scenario.NIGHT_THEFT:
        return int(0 <= hour < 5)
    if scenario == Scenario.INTERMITTENT_EVENING:
        if 18 <= hour < 22:
            return int(rng.random() > 0.45)
        return 0
    if scenario == Scenario.DISTURBANCE_WITHOUT_THEFT:
        return 0
    if scenario == Scenario.DEGRADED_LINK_NO_THEFT:
        return 0
    return 0


def _fraud_profile_and_ratio(scenario: Scenario, hour: int, rng: np.random.Generator) -> tuple[str, float]:
    """Assigns a fraud modus operandi and severity for an active theft tick.

    Real fraud behavior is heterogeneous: some customers divert a small,
    stable fraction of consumption at all times (hard to detect), some divert
    heavily but only in short windows, and some vary the diverted fraction
    with the hour of day. Using a single random ratio per tick (as in the
    original generator) collapses this heterogeneity and makes every theft
    instance about equally easy to detect. This function draws a discrete
    fraud profile per tick so that detection difficulty is heterogeneous
    within and across scenarios, which is required to obtain a non-trivial
    (non-perfect) classification problem.
    """
    if scenario == Scenario.PERSISTENT_THEFT:
        weights = {"partial_constant": 0.55, "partial_variable": 0.35, "stealth": 0.10}
    elif scenario == Scenario.INTERMITTENT_EVENING:
        weights = {"stealth": 0.40, "partial_variable": 0.40, "full_diversion": 0.20}
    else:
        weights = {"partial_variable": 0.55, "stealth": 0.25, "full_diversion": 0.20}

    profiles = list(weights.keys())
    probabilities = np.array(list(weights.values()))
    profile = rng.choice(profiles, p=probabilities / probabilities.sum())

    if profile == "stealth":
        ratio = float(rng.uniform(0.05, 0.11))
    elif profile == "partial_constant":
        ratio = float(rng.uniform(0.15, 0.25))
    elif profile == "partial_variable":
        peak_hour_factor = 1.15 if 18 <= hour < 22 else 0.85
        ratio = float(np.clip(rng.uniform(0.14, 0.30) * peak_hour_factor, 0.08, 0.40))
    else:  # full_diversion
        ratio = float(rng.uniform(0.55, 0.88))

    return str(profile), ratio


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _build_meter_state(active_power: float, voltage_rms: float, power_factor: float) -> dict[str, float]:
    power_factor = _clamp(power_factor, 0.72, 0.99)
    apparent_power = active_power / power_factor
    reactive_power = max(0.0, (apparent_power**2 - active_power**2) ** 0.5)
    current_rms = apparent_power / max(voltage_rms, 1.0)
    return {
        "active_power": active_power,
        "reactive_power": reactive_power,
        "apparent_power": apparent_power,
        "current_rms": current_rms,
        "power_factor": power_factor,
    }


def generate_synthetic_dataset(
    output_dir: Path,
    days: int = 7,
    scenario: Scenario = Scenario.INTERMITTENT_EVENING,
    seed: int = 42,
    dev_eui: str = DEFAULT_DEV_EUI,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    periods = int(days * 24 * 60 / NATIVE_INTERVAL_MINUTES)
    timestamps = pd.date_range("2026-01-01", periods=periods, freq=f"{NATIVE_INTERVAL_MINUTES}min")

    link_failure_probability = 0.03
    heartbeat_failure_probability = 0.02
    glitch_probability = COMMUNICATION_GLITCH_PROBABILITY
    if scenario == Scenario.DEGRADED_LINK_NO_THEFT:
        link_failure_probability = 0.28
        heartbeat_failure_probability = 0.22
        glitch_probability = COMMUNICATION_GLITCH_PROBABILITY * 2.5

    # Day-level activation mask for scenarios whose theft window is otherwise
    # a fixed, fully deterministic hour-of-day rule (peak_theft, night_theft).
    # Without this, theft occurs on 100% of days at exactly the same hours,
    # which lets the classifier learn a near-perfect rule from calendar/hour
    # features alone (via slot_recurrence), independent of any electrical
    # evidence. Making the daily occurrence probabilistic (rather than
    # certain) forces the decision layer to still rely on power-divergence
    # evidence, and keeps the classification problem non-trivial even after
    # the forensic-vs-billing divergence itself was made noisier.
    day_theft_active_mask = rng.random(days) < 0.82

    forensic_rows = []
    billing_rows = []
    alarm_rows = []

    forensic_active_energy = 0.0
    forensic_reactive_energy = 0.0
    billing_active_energy = 0.0
    billing_reactive_energy = 0.0

    for ts in timestamps:
        hour = ts.hour
        base_power = _base_load_profile(hour)
        daily_noise = rng.normal(0.0, 70.0)
        active_power = max(120.0, base_power + daily_noise)

        voltage_rms = NOMINAL_VOLTAGE + rng.normal(0.0, 4.0)
        power_factor = _clamp(0.92 + rng.normal(0.0, 0.025), 0.80, 0.99)

        if scenario == Scenario.DISTURBANCE_WITHOUT_THEFT and rng.random() > 0.97:
            voltage_rms += rng.normal(18.0, 4.0)
            power_factor = _clamp(power_factor - abs(rng.normal(0.18, 0.04)), 0.72, 0.95)

        # Legitimate but erratic load behavior, independent of theft: an
        # occasional appliance-driven surge affects the forensic reading only
        # (it is a real physical event seen by both meters, but it does not
        # by itself create forensic-vs-billing divergence).
        benign_surge = rng.random() < BENIGN_LOAD_SURGE_PROBABILITY
        if benign_surge:
            active_power += abs(rng.normal(260.0, 90.0))

        theft_active = _theft_active(ts, scenario, rng)
        if theft_active and scenario in (Scenario.PEAK_THEFT, Scenario.NIGHT_THEFT):
            day_index = min(int((ts.normalize() - timestamps[0].normalize()).days), days - 1)
            if not day_theft_active_mask[day_index]:
                theft_active = 0
        theft_ratio = 0.0
        fraud_profile = "none"
        bypass_artifact = False
        if theft_active:
            fraud_profile, theft_ratio = _fraud_profile_and_ratio(scenario, hour, rng)
            if fraud_profile == "full_diversion" and rng.random() < BYPASS_ARTIFACT_PROBABILITY:
                bypass_artifact = True

        forensic_active_power = active_power * (1.0 + rng.normal(0.0, SENSOR_NOISE_RELATIVE_STD))
        billing_active_power = active_power * (1.0 - theft_ratio) * (1.0 + rng.normal(0.0, SENSOR_NOISE_RELATIVE_STD))

        # Communication/reporting glitches: a transient, theft-unrelated
        # perturbation applied at random to either meter. This is what makes
        # "divergence" an unreliable single-tick signal and forces the
        # decision layer to rely on persistence/recurrence rather than a
        # single-sample threshold.
        if rng.random() < glitch_probability:
            glitch_magnitude = rng.normal(0.0, COMMUNICATION_GLITCH_RELATIVE_MAGNITUDE)
            if rng.random() < 0.5:
                forensic_active_power *= (1.0 + glitch_magnitude)
            else:
                billing_active_power *= (1.0 - glitch_magnitude)

        forensic_active_power = max(60.0, forensic_active_power)
        billing_active_power = max(0.0, billing_active_power)

        forensic_state = _build_meter_state(active_power=forensic_active_power, voltage_rms=voltage_rms, power_factor=power_factor)
        billing_power_factor = _clamp(power_factor + rng.normal(0.0, 0.01), 0.78, 0.99)
        billing_state = _build_meter_state(
            active_power=billing_active_power,
            voltage_rms=voltage_rms,
            power_factor=billing_power_factor,
        )

        forensic_active_energy += forensic_state["active_power"] * INTERVAL_HOURS
        forensic_reactive_energy += forensic_state["reactive_power"] * INTERVAL_HOURS
        billing_active_energy += billing_state["active_power"] * INTERVAL_HOURS
        billing_reactive_energy += billing_state["reactive_power"] * INTERVAL_HOURS

        alarm_overvoltage = int(voltage_rms > 242.0)
        alarm_undervoltage = int(voltage_rms < 198.0)
        alarm_overcurrent = int(forensic_state["current_rms"] > 6.0)
        if bypass_artifact and not alarm_overcurrent:
            alarm_overcurrent = int(rng.random() < 0.6)
        alarm_last_gasp = int(voltage_rms < 95.0)
        # Physical over-demand alarm, defined only from the forensic meter's
        # own active power against a contracted ceiling. Unlike the original
        # implementation, this alarm is NOT derived from the forensic-vs-
        # billing gap, so it cannot leak the detection label into the
        # feature set.
        alarm_out_of_bounds_power = int(forensic_state["active_power"] > CONTRACTED_DEMAND_LIMIT_W)

        link_ok = int(rng.random() > link_failure_probability)
        heartbeat_ok = int(rng.random() > heartbeat_failure_probability)

        forensic_rows.append(
            {
                "timestamp": ts.isoformat(),
                "dev_eui": dev_eui,
                "voltage_rms": round(voltage_rms, 3),
                "current_rms": round(forensic_state["current_rms"], 3),
                "active_power": round(forensic_state["active_power"], 3),
                "reactive_power": round(forensic_state["reactive_power"], 3),
                "apparent_power": round(forensic_state["apparent_power"], 3),
                "power_factor": round(forensic_state["power_factor"], 4),
                "active_energy": round(forensic_active_energy, 3),
                "reactive_energy": round(forensic_reactive_energy, 3),
                "link_ok": link_ok,
                "heartbeat_ok": heartbeat_ok,
            }
        )
        billing_rows.append(
            {
                "timestamp": ts.isoformat(),
                "dev_eui": dev_eui,
                "billing_voltage_rms": round(voltage_rms, 3),
                "billing_current_rms": round(billing_state["current_rms"], 3),
                "billing_active_power": round(billing_state["active_power"], 3),
                "billing_reactive_power": round(billing_state["reactive_power"], 3),
                "billing_apparent_power": round(billing_state["apparent_power"], 3),
                "billing_power_factor": round(billing_state["power_factor"], 4),
                "billing_active_energy": round(billing_active_energy, 3),
                "billing_reactive_energy": round(billing_reactive_energy, 3),
            }
        )
        alarm_rows.append(
            {
                "timestamp": ts.isoformat(),
                "dev_eui": dev_eui,
                "alarm_overvoltage": alarm_overvoltage,
                "alarm_undervoltage": alarm_undervoltage,
                "alarm_overcurrent": alarm_overcurrent,
                "alarm_last_gasp": alarm_last_gasp,
                "alarm_out_of_bounds_power": alarm_out_of_bounds_power,
                "scenario_label": scenario.value,
                "theft_active": theft_active,
                "theft_ratio": round(theft_ratio, 4),
                "fraud_profile": fraud_profile,
            }
        )

    forensic_df = pd.DataFrame(forensic_rows)
    billing_df = pd.DataFrame(billing_rows)
    alarm_df = pd.DataFrame(alarm_rows)

    forensic_path = output_dir / "forensic_measurements.csv"
    billing_path = output_dir / "billing_measurements.csv"
    alarm_path = output_dir / "alarm_events.csv"

    forensic_df.to_csv(forensic_path, index=False)
    billing_df.to_csv(billing_path, index=False)
    alarm_df.to_csv(alarm_path, index=False)

    return {
        "forensic": forensic_path,
        "billing": billing_path,
        "alarms": alarm_path,
    }
