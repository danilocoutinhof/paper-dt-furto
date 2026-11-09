# Manuscript Results Mapping

## Purpose

This document maps the current implementation outputs to specific manuscript claims and likely tables or figures.

## Claims supported directly by the codebase

### Explicit digital twin

Supported by:

- `src/fraud_dt/twin/`
- `src/fraud_dt/control/`
- `src/fraud_dt/actions/`
- `src/fraud_dt/runtime/`

Recommended evidence in the manuscript:

- architecture figure from `docs/flowcharts.md`
- mention of `twin_state_history.csv`, `twin_decisions.csv`, and `command_plan.csv`

### Closed-loop local prototype

Supported by:

- `MockForensicDevice`
- `MockTransport`
- `SimulationRunner`
- `transport_delivery.csv`

Recommended evidence in the manuscript:

- sequence flowchart from `docs/flowcharts.md`
- note that commands alter future emission density in the local simulator

### Observation-cost vs detection trade-off

Supported by:

- `outputs/policy_comparison.csv`
- `outputs/campaign/campaign_policy_aggregate.csv`
- `outputs/policy_comparison.png`

### Fusion strategy analysis

Supported by:

- `outputs/fusion_strategy_comparison.csv`
- `outputs/campaign/campaign_fusion_strategy_aggregate.csv`
- `outputs/fusion_strategy_comparison.png`

## Recommended figures

- Architecture: `docs/flowcharts.md`
- Policy comparison: `outputs/policy_comparison.png`
- Fusion comparison: `outputs/fusion_strategy_comparison.png`
- Risk trajectories: `outputs/risk_over_time.png`
- Mode transitions: `outputs/observation_modes.png`

## Recommended tables

- Campaign policy aggregate: `outputs/campaign/campaign_policy_aggregate.csv`
- Campaign fusion aggregate: `outputs/campaign/campaign_fusion_strategy_aggregate.csv`
- LaTeX seed: `outputs/campaign/campaign_tables.tex`
