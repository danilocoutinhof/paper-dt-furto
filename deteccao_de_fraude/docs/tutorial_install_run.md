# Installation and Usage Tutorial

## 1. Requirements

- Python 3.11 or newer
- Windows PowerShell or a terminal capable of running Python

No IDE is required.

## 2. Environment setup

```powershell
cd C:\projects\artigo_gemeos_digitais_2026\deteccao_de_fraude
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Generate synthetic data for one scenario

```powershell
python scripts\generate_synthetic_data.py --days 7 --scenario intermittent_evening --seed 42
```

Supported scenarios:

- `normal`
- `persistent_theft`
- `peak_theft`
- `night_theft`
- `intermittent_evening`
- `disturbance_without_theft`

## 4. Run the single-scenario pipeline

```powershell
python scripts\run_pipeline.py --input-dir data\raw --output-dir outputs
```

## 5. Run the full campaign

```powershell
python scripts\run_experiment_campaign.py --days 7 --seed 42
```

This campaign executes all synthetic scenarios and writes aggregate outputs to:

- `outputs/campaign/campaign_policy_comparison.csv`
- `outputs/campaign/campaign_policy_aggregate.csv`
- `outputs/campaign/campaign_fusion_strategy_aggregate.csv`
- `outputs/campaign/campaign_summary.md`

## 6. What the pipeline now does

- loads forensic, billing, and alarm data
- aligns measurements by timestamp
- computes divergence and contextual features
- assigns a rule-based theft-risk probability
- trains an explainable supervised logistic-regression baseline
- executes a closed-loop runtime over the synthetic physical timeline
- lets a mock forensic device emit or suppress future samples according to the current capture period
- builds a `TwinObservation` for each emitted event
- computes a twin-level decision through a `DecisionEngine`
- evaluates multiple fusion strategies for adaptive control:
  - weighted
  - conservative max
  - context aware
- generates a telemetry reconfiguration command through a `PolicyOrchestrator`
- delivers the command through a mock NB-IoT/BLE transport
- updates explicit twin state and future sampling behavior
- compares three observation strategies:
  - fixed long
  - fixed short
  - adaptive
- stores results in CSV and SQLite
- exports markdown summaries and plots

## 7. What to inspect after a run

### `outputs/run_summary.md`
Compact overview of the single-scenario run.

### `outputs/twin_decisions.csv`
Event-level twin decisions for the default adaptive fusion strategy.

### `outputs/fusion_strategy_comparison.csv`
Comparison between adaptive fusion strategies using the same runtime structure.

### `outputs/twin_state_history.csv`
Twin state after each observed event.

### `outputs/command_plan.csv`
Command-plan records emitted by the policy orchestrator.

### `outputs/transport_delivery.csv`
Transport-level delivery records showing NB-IoT or BLE fallback in the local runtime.

### `outputs/observation_policy.csv`
Timeline-level view of the adaptive runtime, including whether each physical instant was observed.

### `outputs/model_metrics.csv`
Supervised baseline metrics for the current run.

### `outputs/policy_comparison.csv`
Comparison between fixed and adaptive observation policies.

### `outputs/campaign/campaign_policy_aggregate.csv`
Mean performance across all synthetic scenarios.

### `outputs/campaign/campaign_fusion_strategy_aggregate.csv`
Mean performance of adaptive fusion strategies across all synthetic scenarios.

### `outputs/risk_over_time.png`
Shows rule-based, supervised, and fused decision probabilities over time.

### `outputs/observation_modes.png`
Shows how the adaptive policy changed observation mode.

### `outputs/policy_comparison.png`
Shows the trade-off between communication cost and F1 across policies.

### `outputs/fusion_strategy_comparison.png`
Shows the trade-off between communication cost and F1 across adaptive fusion strategies.

## 8. How this connects to the paper

The software is designed so that the article can directly report:

- the data model
- the feature set
- the explicit twin state
- the decision engine and fusion strategies
- the policy orchestrator
- the command-plan representation
- the local closed-loop simulation runtime
- the transport contingency behavior
- the policy comparison outputs
- the fusion-strategy comparison outputs
- the reproducible synthetic scenarios

## 9. Running tests

```powershell
pytest
```

Recommended test framework: `pytest`.
The repository currently includes unit tests for the twin state, decision engine, fusion strategies, policy orchestrator, command plan, mock device, mock transport, and integration tests for the closed-loop runtime and end-to-end pipeline.
