# Architecture

## Purpose

This prototype implements the software layer of the digital twin described in the paper. The current implementation favors reproducibility and low setup friction over deployment complexity while already making the twin state, decision logic, policy orchestration, command outputs, and local closed-loop runtime explicit.

## Framework view

The current implementation is structured into seven layers:

1. Data ingestion and temporal alignment
2. Feature engineering and contextual enrichment
3. Risk baselines and decision fusion
4. Explicit digital twin state
5. Policy orchestration and command-plan generation
6. Mock device and transport runtime
7. Persistence, reporting, and comparative evaluation

## Current prototype architecture

### Offline-reproducible closed-loop mode

The current version runs as a CLI pipeline over CSV inputs. This was chosen because:

- it is easy to reproduce with `requirements.txt`
- it supports article experiments without requiring infrastructure services
- it provides a clean scientific baseline before online integration

Even in offline mode, the code now materializes an explicit twin cycle:

1. read one temporally ordered physical event from the synthetic timeline
2. let the mock forensic device decide whether the event is emitted under the current capture period
3. if emitted, build a `TwinObservation`
4. evaluate the event with a `DecisionEngine`
5. fuse rule-based and supervised evidence into a twin-level probability
6. issue a `TelemetryReconfigurationDecision` through a `PolicyOrchestrator`
7. deliver the command through a `MockTransport` using NB-IoT or BLE fallback
8. apply the delivered command to the `ForensicTwin` and `MockForensicDevice`
9. persist the resulting `TwinStateSnapshot`

### Core modules

- `src/fraud_dt/twin/`
  - `state.py`: `ForensicTwin`
  - `models.py`: observation, decision, and state snapshot models
- `src/fraud_dt/decision/`
  - `engine.py`: `DecisionEngine`
  - `fusion.py`: `weighted`, `conservative_max`, and `context_aware` fusion strategies
- `src/fraud_dt/control/`
  - `orchestrator.py`: `PolicyOrchestrator`
- `src/fraud_dt/actions/`
  - `commands.py`: `TelemetryReconfigurationDecision`
- `src/fraud_dt/devices/`
  - `mock_forensic_device.py`: local forensic-device model with configurable capture period
  - `mock_billing_meter.py`: local billing reference
  - `mock_transport.py`: local NB-IoT/BLE delivery mock with delivery-status feedback to the twin state
- `src/fraud_dt/runtime/`
  - `simulator.py`: closed-loop simulation runner
- `src/fraud_dt/synthetic.py`
  - deterministic scenario generator with metrologically consistent forensic and billing streams

## Planned online architecture

The long-term architecture remains service-oriented:

- forensic telemetry ingestion service
- billing ingestion service
- digital twin state service
- risk engine
- policy orchestrator
- command/output interface
- command delivery over NB-IoT with BLE contingency

## Why SQLite by default

The paper may later discuss PostgreSQL/TimescaleDB as a scale-up path, but SQLite is used here because:

- it is available with standard Python
- it avoids external database setup
- it is sufficient for controlled experiments

## Post-rejection revisions (IEEE Access resubmission)

Following peer-review rejection, the following components were added without changing the core twin/decision/orchestration abstractions:

- `src/fraud_dt/devices/network_cost.py`: shared NB-IoT/BLE communication-cost model (payload bytes, RRC signaling overhead, connection-reuse window, retransmission probability that worsens under degraded link/heartbeat state, latency), used consistently by both `MockTransport` (closed-loop) and `comparison.evaluate_policy` (fixed policies), replacing a flat bytes-per-sample proxy. Device energy consumption is out of scope by design: the forensic device is mains-powered and available full-time, so the utility's actual constraint is data cost, not battery life.
- `apply_fixed_dense_policy` in `policy.py`: a fourth observation policy reporting at the native acquisition resolution (`ObservationPolicy.fixed_dense_minutes`), used as the true "dense monitoring" ceiling. This was required because correcting the native-resolution bug (see below) made `fixed_short` (15 min) a genuinely sparser policy than the native grid, so it could no longer serve as the dense-monitoring reference point.
- `risk.compute_model_comparison_and_importance`: reporting-only analysis (logistic-regression standardized coefficients, permutation importance, an MLP baseline, ROC curve points) that does not feed the twin's decision loop.
- `comparison.py`: added a Gaussian-decay relaxed `critical_slot_score_relaxed` alongside the existing binary `critical_slot_hit`.
- `scripts/run_policy_optimization.py`: grid search over the fusion weight and hysteresis thresholds, producing an empirical Pareto frontier between F1-score and communication bytes.
- `scripts/run_scalability_benchmark.py`: empirical wall-clock/memory scaling benchmark as the number of simulated twins grows.
- `synthetic.py`: native resolution corrected from 15 to 5 minutes; independent noise sources and heterogeneous fraud profiles added (see `docs/data_model.md`); a seventh scenario, `degraded_link_no_theft`, was added to stress-test false-alert behavior and transport fallback under poor connectivity without a theft confound.

## Scientific traceability

Every run of the pipeline generates:

- merged data
- feature-enriched data
- twin decisions
- state history
- command plans
- transport-delivery records
- observation modes
- a summary report
- plots
- manifest files for run- and campaign-level reproducibility

These artifacts can be directly referenced when preparing results for the manuscript.
