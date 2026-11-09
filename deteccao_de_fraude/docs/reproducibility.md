# Reproducibility

## Goal

This repository is designed so that the experimental results reported in the manuscript can be regenerated locally with a Python environment, `requirements.txt`, and command-line scripts only.

## Reproducibility artifacts

### Single run

A single run now generates:

- `outputs/run_manifest.json`
- `outputs/run_summary.md`
- CSV artifacts for data, state, decisions, commands, transport, and policy comparison
- plots for risk, modes, policy comparison, and fusion comparison
- SQLite persistence database

### Campaign

A campaign run now generates:

- `outputs/campaign/campaign_manifest.json`
- `outputs/campaign/campaign_summary.md`
- `outputs/campaign/campaign_policy_aggregate.csv`
- `outputs/campaign/campaign_fusion_strategy_aggregate.csv`
- `outputs/campaign/campaign_tables.tex`

## What the manifest records

The manifests capture:

- project path
- input and output paths
- configuration values
- Python version
- platform information
- core package versions
- key experiment parameters such as seed, scenarios, and number of runs

## Recommended replication workflow

1. Create a fresh virtual environment.
2. Install dependencies from `requirements.txt`.
3. Generate synthetic data.
4. Run the single scenario pipeline.
5. Run the multi-scenario campaign.
6. Inspect the generated manifests and summaries.
7. Use `campaign_tables.tex` as a seed for the article tables.

## Regression stance

The test suite includes light regression checks on properties that matter to the paper, such as communication-cost ordering and minimum acceptable F1 under the adaptive weighted strategy. These are not intended to freeze exact floating-point outputs forever, but to detect structural regressions in the framework.
