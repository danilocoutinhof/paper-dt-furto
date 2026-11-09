"""Empirical computational-complexity / scalability benchmark.

Addresses a peer-review finding: the manuscript included feature extraction,
two risk engines, probability fusion, policy decisions, and continuous twin-
state updates, but reported no computational cost, memory footprint, or
runtime-scaling analysis as the number of monitored devices grows.

Design of the benchmark: each simulated forensic twin is independent (no
cross-twin interaction exists anywhere in the architecture: `ForensicTwin`,
`DecisionEngine`, `PolicyOrchestrator`, and `MockTransport` all operate on a
single device's event stream). Processing N twins is therefore an
embarrassingly parallel workload; this script measures the SEQUENTIAL,
single-process cost (N twins processed one after another in the same
process) to obtain a conservative, worst-case scaling curve and to verify
empirically that per-twin cost does not grow with N (i.e. no accidental
global state or O(N^2) behavior was introduced by the pipeline/runtime
code).
"""
from __future__ import annotations

import time
import tracemalloc
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd

from fraud_dt.comparison import ComparisonSettings, evaluate_policy
from fraud_dt.config import build_config
from fraud_dt.control import PolicyOrchestrator
from fraud_dt.decision import DecisionEngine, build_fusion_strategies
from fraud_dt.devices import MockTransport
from fraud_dt.features import build_feature_dataset, load_input_dataset
from fraud_dt.risk import score_rule_based_risk, train_supervised_baseline
from fraud_dt.runtime import SimulationRunner
from fraud_dt.schemas import Scenario
from fraud_dt.synthetic import generate_synthetic_dataset

FLEET_SIZES = [1, 5, 10, 25, 50, 100]
DAYS = 7


def _prepare_single_twin_dataset(root: Path, seed: int) -> pd.DataFrame:
    raw_dir = root / "raw_benchmark"
    generate_synthetic_dataset(raw_dir, days=DAYS, scenario=Scenario.INTERMITTENT_EVENING, seed=seed)
    forensic_df, billing_df, alarm_df = load_input_dataset(raw_dir)
    merged_df = build_feature_dataset(forensic_df, billing_df, alarm_df)
    scored_df = score_rule_based_risk(merged_df)
    supervised_df, _ = train_supervised_baseline(scored_df)
    return supervised_df


def _run_one_twin(config, supervised_df: pd.DataFrame, dev_eui: str) -> None:
    df = supervised_df.copy()
    df["dev_eui"] = dev_eui
    fusion_strategy = build_fusion_strategies()["weighted"]
    runner = SimulationRunner(
        config=config,
        decision_engine=DecisionEngine(thresholds=config.thresholds, fusion_strategy=fusion_strategy),
        orchestrator=PolicyOrchestrator(policy=config.policy, thresholds=config.thresholds),
        transport=MockTransport(ble_available=True),
    )
    adaptive_df, decision_df, state_df, command_df, transport_df = runner.run(df)
    evaluate_policy(adaptive_df, "decision_probability", ComparisonSettings())


def run_benchmark() -> pd.DataFrame:
    config = build_config(ROOT)
    supervised_df = _prepare_single_twin_dataset(ROOT / "outputs" / "_scalability_tmp", seed=42)
    events_per_twin = len(supervised_df)

    rows = []
    for fleet_size in FLEET_SIZES:
        tracemalloc.start()
        start = time.perf_counter()
        for i in range(fleet_size):
            _run_one_twin(config, supervised_df, dev_eui=f"bench-{i:04d}")
        elapsed_seconds = time.perf_counter() - start
        _, peak_memory_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        rows.append(
            {
                "fleet_size": fleet_size,
                "events_per_twin": events_per_twin,
                "total_events": fleet_size * events_per_twin,
                "elapsed_seconds": elapsed_seconds,
                "seconds_per_twin": elapsed_seconds / fleet_size,
                "seconds_per_1000_events": elapsed_seconds / (fleet_size * events_per_twin) * 1000.0,
                "peak_memory_mb": peak_memory_bytes / (1024 * 1024),
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    output_dir = ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmark_df = run_benchmark()
    benchmark_df.to_csv(output_dir / "scalability_benchmark.csv", index=False)

    print(benchmark_df.to_string(index=False))

    baseline = benchmark_df.iloc[0]["seconds_per_twin"]
    largest = benchmark_df.iloc[-1]["seconds_per_twin"]
    drift_ratio = largest / baseline if baseline > 0 else float("nan")
    print(
        f"\nPer-twin cost drift from N={benchmark_df.iloc[0]['fleet_size']} to "
        f"N={benchmark_df.iloc[-1]['fleet_size']}: {drift_ratio:.3f}x "
        f"(close to 1.0x is expected/confirms linear O(N) scaling with no shared-state overhead)"
    )
