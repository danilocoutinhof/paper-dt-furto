# Data Model

## Overview

The data model is aligned with the firmware telemetry domain and uses two measurement streams:

- billing meter
- forensic meter

The forensic stream also includes alarm-related context.

The synthetic generator is designed to preserve metrological consistency between instantaneous and accumulated quantities. For both streams, voltage, current, active power, reactive power, apparent power, power factor, and accumulated energies are generated coherently so that the synthetic traces can support scientifically defensible experiments.

### Post-rejection revisions (native resolution, noise, fraud heterogeneity)

Peer review identified two methodological flaws that have since been corrected in `src/fraud_dt/synthetic.py`:

- The native acquisition grid was **15 minutes**, which made the `aggressive` (5-minute) and `moderate` (15-minute) observation modes operationally indistinguishable (a 5-minute capture period can never be observed faster than data actually exists at 15-minute resolution). The native grid is now **5 minutes** (`NATIVE_INTERVAL_MINUTES`), an exact common denominator of `basal`/`moderate`/`aggressive` (60/15/5 minutes).
- The forensic-vs-billing divergence was, by construction, an almost-deterministic function of the synthetic theft ratio, and was at the same time the only feature used for detection — making the classification problem artificially easy. The generator now adds independent, theft-unrelated noise sources (per-meter metrological noise, communication/reporting glitches, benign load surges), assigns heterogeneous fraud severities/profiles (`stealth`, `partial_constant`, `partial_variable`, `full_diversion`), makes fixed-hour theft windows probabilistic per day rather than certain every day, and redefines `alarm_out_of_bounds_power` from the forensic meter's own reading against a contracted demand ceiling instead of from the forensic-vs-billing gap.

## Forensic measurements

File: `forensic_measurements.csv`

Columns:

- `timestamp`
- `dev_eui`
- `voltage_rms`
- `current_rms`
- `active_power`
- `reactive_power`
- `apparent_power`
- `power_factor`
- `active_energy`
- `reactive_energy`
- `link_ok`
- `heartbeat_ok`

Interpretation:

- `apparent_power` is consistent with the active/reactive power triangle
- `current_rms` is derived from apparent power and voltage
- `active_energy` and `reactive_energy` are accumulated over the native interval grid (5 minutes)

## Billing measurements

File: `billing_measurements.csv`

Columns:

- `timestamp`
- `dev_eui`
- `billing_voltage_rms`
- `billing_current_rms`
- `billing_active_power`
- `billing_reactive_power`
- `billing_apparent_power`
- `billing_power_factor`
- `billing_active_energy`
- `billing_reactive_energy`

Interpretation:

- the billing stream is internally coherent, not just a reduced active-power trace
- when theft is active, billing active power is reduced relative to the forensic stream
- after this reduction, current, reactive power, apparent power, power factor, and accumulated energies are recalculated coherently

## Alarm events

File: `alarm_events.csv`

Columns:

- `timestamp`
- `dev_eui`
- `alarm_overvoltage`
- `alarm_undervoltage`
- `alarm_overcurrent`
- `alarm_last_gasp`
- `alarm_out_of_bounds_power`
- `scenario_label`
- `theft_active`
- `theft_ratio`
- `fraud_profile`

Interpretation:

- alarms are derived from the simulated electrical and operational state; `alarm_out_of_bounds_power` is derived only from the forensic meter's own reading against a contracted demand ceiling, never from the forensic-vs-billing gap, so it cannot leak the detection label
- `theft_active` and `theft_ratio` are scenario-driven synthetic labels used for controlled experiments and supervision bootstrap
- `fraud_profile` (`none`, `stealth`, `partial_constant`, `partial_variable`, `full_diversion`) records the fraud modus operandi assigned to each active theft tick, reflecting the heterogeneity of real fraud behavior (constant partial diversion, time-window-dependent diversion, brief high-severity diversion, and low-severity diversion near the noise floor)

## Labels

The synthetic generator writes scenario-driven labels and theft activity indicators that can be used for initial supervised experiments, campaign analysis, and validation of adaptive observation policies.

## Alignment with firmware project

Names were chosen to remain close to the firmware concepts already present in the project:

- metrology variables reflect the instantaneous meter data domain
- billing and forensic streams remain semantically separable
- alarm names reflect the alarm manager semantics
- time-series windows support the article's adaptive observation policy
