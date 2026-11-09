# Digital Twin for Energy Theft Risk Classification

This repository contains a reproducible prototype implementation for the paper:

`Energy theft probability classification with adaptive observation windows in a digital twin for NB-IoT forensic telemetry`

The implementation is intentionally pragmatic:

- Python only
- installable via `requirements.txt`
- no IDE-specific workflow required
- runnable from the command line
- synthetic data generation aligned with the firmware domain model
- SQLite used by default to reduce setup friction
- explicit digital-twin state, decision, orchestration, and command-plan layers

## Scientific objective

The software implements the software layer of an application-aware digital-twin prototype that:

- ingests forensic and billing measurements;
- computes divergence and contextual features;
- estimates theft-risk probability with explainable rule-based and supervised baselines;
- fuses decision signals into a twin-level decision probability;
- maintains explicit twin state over time;
- generates telemetry reconfiguration decisions through a policy orchestrator;
- compares fixed-long, fixed-short, and adaptive observation policies;
- stores results and produces outputs that can be used directly in the article.

## Repository structure

- `src/fraud_dt/`: core package
- `src/fraud_dt/twin/`: explicit digital twin state and observation models
- `src/fraud_dt/decision/`: decision engine and fusion strategies
- `src/fraud_dt/control/`: policy orchestrator
- `src/fraud_dt/actions/`: command-plan representation
- `scripts/`: CLI entry scripts
- `docs/`: architecture, framework overview, installation, article alignment
- `data/`: raw and processed datasets
- `outputs/`: generated reports and figures
- `tests/`: unit and end-to-end validation

## Quick start

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Generate a synthetic dataset.
4. Run the pipeline.
5. Inspect outputs and figures.

Detailed instructions are in [docs/tutorial_install_run.md](docs/tutorial_install_run.md).

## Minimal commands

```powershell
cd C:\projects\artigo_gemeos_digitais_2026\deteccao_de_fraude
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\generate_synthetic_data.py --days 7 --scenario intermittent_evening
python scripts\run_pipeline.py --input-dir data\raw --output-dir outputs
```

## Main outputs

- `outputs/merged_dataset.csv`
- `outputs/risk_scored_dataset.csv`
- `outputs/supervised_scored_dataset.csv`
- `outputs/observation_policy.csv`
- `outputs/twin_decisions.csv`
- `outputs/twin_state_history.csv`
- `outputs/command_plan.csv`
- `outputs/policy_comparison.csv`
- `outputs/model_metrics.csv`
- `outputs/model_comparison.csv` (logistic regression vs. MLP baseline)
- `outputs/feature_importance.csv` (standardized coefficients + permutation importance)
- `outputs/roc_curve_points.csv` and `outputs/roc_curves.png`
- `outputs/run_summary.md`
- `outputs/risk_over_time.png`
- `outputs/observation_modes.png`
- `outputs/policy_comparison.png`
- `outputs/fraud_dt.sqlite3`

## Additional analysis scripts (IEEE Access resubmission)

- `scripts/run_policy_optimization.py`: grid search / empirical Pareto frontier over the fusion weight and hysteresis thresholds (`outputs/policy_pareto_grid.csv`, `outputs/policy_pareto_aggregate.csv`, `outputs/policy_pareto_frontier.csv`).
- `scripts/run_scalability_benchmark.py`: wall-clock/memory scaling benchmark as the number of simulated twins grows (`outputs/scalability_benchmark.csv`).

## Domain alignment with firmware

The synthetic and processed data use field names inspired by the firmware domain and DLMS-facing objects, including:

- `voltage_rms`
- `current_rms`
- `active_power`
- `reactive_power`
- `apparent_power`
- `active_energy`
- `reactive_energy`
- `alarm_overvoltage`
- `alarm_undervoltage`
- `alarm_overcurrent`
- `alarm_last_gasp`
- `alarm_out_of_bounds_power`

## Implementation status

Current version:

- reproducible research prototype
- synthetic-data first
- explicit digital twin state and command plan
- rule-based and supervised explainable baselines
- weighted decision fusion for adaptive control
- adaptive observation policy with hysteresis
- explicit policy comparison
- SQLite persistence
- unit and end-to-end tests with `pytest`

Planned next steps:

- device mocks and closed-loop runtime simulation
- calibration with real traces from the firmware ecosystem
- NB-IoT broker integration
- BLE contingency ingestion path
- API service layer for online operation
