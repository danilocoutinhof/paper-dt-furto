# Flowcharts

## 1. Twin control loop

```mermaid
flowchart TD
    A[Synthetic physical timeline] --> B[MockForensicDevice emission gate]
    C[Billing reference timeline] --> D[TwinObservation build]
    B --> D
    D --> E[DecisionEngine]
    E --> F[Probability fusion]
    F --> G[PolicyOrchestrator]
    G --> H[TelemetryReconfigurationDecision]
    H --> I[MockTransport NB-IoT or BLE]
    I --> J[ForensicTwin state update]
    I --> K[MockForensicDevice reconfiguration]
    J --> L[TwinStateSnapshot]
    K --> M[Future observation density]
    L --> N[Persistence and reports]
    M --> N
```

## 2. Event-level sequence

```mermaid
sequenceDiagram
    participant Timeline as Physical timeline
    participant Device as MockForensicDevice
    participant Twin as ForensicTwin
    participant Engine as DecisionEngine
    participant Policy as PolicyOrchestrator
    participant Transport as MockTransport
    participant Store as Output artifacts

    Timeline->>Device: candidate timestamp
    Device->>Twin: emitted event
    Twin->>Engine: TwinObservation
    Engine->>Policy: TwinDecision
    Policy->>Transport: TelemetryReconfigurationDecision
    Transport->>Twin: delivered command
    Transport->>Device: delivered command
    Twin->>Store: state snapshot
    Engine->>Store: decision record
    Transport->>Store: delivery record
```

## 3. Comparison experiment flow

```mermaid
flowchart LR
    A[Synthetic scenario] --> B[Closed-loop runtime]
    B --> C[Adaptive timeline and commands]
    A --> D[Fixed short policy evaluation]
    A --> E[Fixed long policy evaluation]
    C --> F[Policy comparison]
    D --> F
    E --> F
    F --> G[Detection vs communication trade-off]
```

## Recommended use in the article

- Figure 1: use the first flowchart as the framework architecture.
- Figure 2: use the sequence diagram to show the twin control loop.
- Figure 3: use the third flowchart to present the experimental methodology.
