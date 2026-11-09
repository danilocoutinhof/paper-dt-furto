# Framework Overview

## Why this repository now qualifies as a framework prototype

The implementation is no longer only a static feature-and-classification pipeline. It now includes explicit architectural entities that represent the digital-twin control loop:

- `ForensicTwin`: maintains twin state for the monitored asset
- `DecisionEngine`: interprets contextual evidence and produces twin decisions
- `PolicyOrchestrator`: converts decisions into observation-policy actions
- `TelemetryReconfigurationDecision`: formal command-plan representation
- `MockForensicDevice`: simulates how reconfiguration affects future telemetry emission
- `MockTransport`: simulates NB-IoT delivery with BLE contingency
- `SimulationRunner`: executes the local closed-loop runtime

## Closed-loop interpretation in the local prototype

The current prototype runs locally over synthetic traces, but it already implements the decision loop required by the paper:

1. the physical timeline contains all potential measurement instants;
2. the mock forensic device emits events only when allowed by the current capture period;
3. the twin receives emitted telemetry evidence;
4. the decision engine evaluates contextual theft risk;
5. the policy orchestrator determines the desired observation mode;
6. the command plan records the reconfiguration decision;
7. the mock transport applies the decision through NB-IoT or BLE fallback;
8. the device changes its future emission schedule;
9. the twin state is updated and persisted.

This is a local and reproducible emulation of the cyber-physical loop. A future runtime can replace local command application with real NB-IoT/BLE delivery without changing the twin abstractions.

## Fusion strategies in Phase 3

The adaptive twin no longer depends on a single fusion rule. The framework now includes three fusion strategies:

- `weighted`: fixed weighted combination of rule-based and supervised probabilities
- `conservative_max`: chooses the strongest risk signal
- `context_aware`: changes the combination according to alarms, recurrence, and operational context

This allows the paper to treat fusion strategy as an experimental design dimension rather than a hidden implementation detail.

## Flowchart for the article

You can directly convert the following flow into a figure in the manuscript:

`Synthetic physical timeline -> MockForensicDevice emission gate -> TwinObservation -> DecisionEngine -> Fusion strategy -> PolicyOrchestrator -> TelemetryReconfigurationDecision -> MockTransport -> ForensicTwin and MockForensicDevice update -> Evaluation and persistence`

## Recommended article phrasing

The article can now state that the implementation provides:

- an explicit digital-twin software layer;
- twin state persistence over the event stream;
- a modular decision architecture;
- a policy orchestrator separate from the classifier baselines;
- a formal command-plan output;
- a local closed-loop simulation runtime;
- multiple fusion strategies for adaptive control;
- reproducible local execution for controlled experiments.

## Fourth policy: `fixed_dense` as the true observation ceiling

`fixed_short` (15 min) is no longer equivalent to dense monitoring once the native
acquisition grid was corrected to 5 minutes (see `docs/data_model.md`). `apply_fixed_dense_policy`
reports at the native resolution and is the correct reference point for "what would
detection performance be under the densest possible monitoring." `fixed_short` remains
a distinct, realistic fixed-cadence baseline in its own right.

## Communication-cost model

`MockTransport` and `comparison.evaluate_policy` now share `devices/network_cost.py`,
a parametrized NB-IoT/BLE cost model (RRC-style signaling overhead on cold connections,
a connection-reuse window, and a retransmission probability that increases under
degraded link/heartbeat state) instead of a flat bytes-per-sample proxy. This lets the
paper report latency and retransmission counts alongside communication bytes, and
ensures fixed and adaptive policies are costed on a like-for-like basis. Device energy
consumption is intentionally out of scope: the forensic device is mains-powered and
available full-time, so the operationally relevant cost driver is data volume, not
battery life.

## Fusion-weight and threshold resolution (`scripts/run_policy_optimization.py`)

The detection-vs-communication-cost trade-off is no longer left as fixed, unjustified
constants. A grid search over the fusion weight and the hysteresis thresholds produces
an empirical Pareto frontier (`outputs/policy_pareto_frontier.csv`), against which the
configuration used elsewhere in the pipeline can be reported as a documented,
near-frontier operating point rather than an arbitrary choice. This is presented as an
empirical resolution of the trade-off, not a formal proof of optimality.

## Scalability benchmark (`scripts/run_scalability_benchmark.py`)

Since every twin/decision/policy/transport component operates on a single device's
event stream with no cross-twin shared state, processing N twins is an embarrassingly
parallel workload. The benchmark measures sequential (single-process, worst-case)
wall-clock time and peak memory as a function of fleet size to verify empirically that
per-twin cost does not grow with the number of monitored devices.
