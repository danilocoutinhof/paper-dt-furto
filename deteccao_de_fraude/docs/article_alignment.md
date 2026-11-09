# Article Alignment

## Why this repository exists

The article argues that a digital twin should actively control observation density according to theft risk. This repository exists to make that claim testable.

## Direct mapping from implementation to manuscript

- Manuscript architecture section -> `docs/architecture.md`
- Framework positioning -> `docs/framework_overview.md`
- Data model section -> `docs/data_model.md`
- Reproducibility section -> `docs/reproducibility.md`
- Results mapping -> `docs/manuscript_results_mapping.md`
- Experimental methodology -> synthetic scenarios and pipeline outputs
- Twin state -> `src/fraud_dt/twin/state.py`
- Decision engine -> `src/fraud_dt/decision/engine.py`
- Probability fusion -> `src/fraud_dt/decision/fusion.py`
- Policy orchestration -> `src/fraud_dt/control/orchestrator.py`
- Command-plan representation -> `src/fraud_dt/actions/commands.py`
- Closed-loop runtime -> `src/fraud_dt/runtime/simulator.py`

## Current scientific scope

This implementation supports:

- reproducible synthetic experiments
- explicit digital twin state and event-by-event state history
- explainable rule-based and supervised baselines
- multiple fusion strategies for adaptive control
- formal command-plan outputs
- local closed-loop simulation with mock device and transport
- comparison between fixed and adaptive observation strategies
- auditable exported outputs for the manuscript
- manifest-based execution traceability

## Planned scientific evolution

- stronger device-network failure models
- integration with real firmware traces
- stronger label curation
- online ingestion from brokers and local contingency channels
