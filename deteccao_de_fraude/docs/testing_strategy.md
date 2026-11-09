# Testing Strategy

## Framework

The project uses `pytest` as the primary test framework.

## Current coverage focus

### Unit tests

- `test_twin_state.py`
  - validates that the explicit twin state is updated after command application
- `test_decision_engine.py`
  - validates probability fusion and risk classification
- `test_fusion_strategies.py`
  - validates context-aware fusion behavior
- `test_policy_orchestrator.py`
  - validates reconfiguration and maintain decisions
- `test_command_plan.py`
  - validates command-plan serialization
- `test_mock_device.py`
  - validates device reconfiguration and future emission timing
- `test_mock_transport.py`
  - validates NB-IoT/BLE fallback behavior

### Integration tests

- `test_runtime_closed_loop.py`
  - validates the local closed-loop runtime and generated artifacts
- `test_pipeline.py`
  - validates end-to-end execution and artifact generation

## Why this matters for the paper

The test suite provides evidence that the implementation is not only executable but also architecturally structured around explicit components corresponding to the manuscript:

- digital twin state
- decision engine
- fusion strategy layer
- policy orchestrator
- command plan
- mock device behavior
- transport contingency
- reproducible pipeline outputs

## Recommended future additions

- regression tests for campaign metrics
- tests for multiple devices in the same runtime
- tests for stronger NB-IoT degradation scenarios
- sensitivity tests for fusion hyperparameters
