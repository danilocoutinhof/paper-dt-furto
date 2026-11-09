"""Grid search / Pareto-frontier resolution of the detection-vs-communication-cost
trade-off for the adaptive observation policy.

This script exists to address a peer-review finding: the manuscript defined a
utility function U = lambda1*D - lambda2*C conceptually, but never solved for
lambda1/lambda2, and the fusion weights (rule_weight/supervised_weight) and
hysteresis thresholds (moderate_risk/high_risk) were fixed, unjustified
constants in the code. This script does not claim a formal proof of
optimality or convergence (that would require a materially larger research
scope); instead it performs an explicit, reproducible grid search over the
fusion weight and the hysteresis thresholds, evaluates every configuration on
the same scenarios/data used elsewhere in the experimental campaign, and
extracts the empirical Pareto frontier between F1-score (detection) and
communication bytes (cost). The configuration used elsewhere in the pipeline
(`WeightedProbabilityFusion(rule_weight=0.6)`, `Thresholds(moderate_risk=0.30,
high_risk=0.60)`) can then be reported as a documented, empirically-motivated
point on (or near) this frontier, rather than an arbitrary choice.
"""
from __future__ import annotations

import itertools
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd

from fraud_dt.comparison import ComparisonSettings, evaluate_policy
from fraud_dt.config import AppConfig, ObservationPolicy, Thresholds
from fraud_dt.control import PolicyOrchestrator
from fraud_dt.decision import DecisionEngine
from fraud_dt.decision.fusion import WeightedProbabilityFusion
from fraud_dt.devices import MockTransport
from fraud_dt.features import build_feature_dataset, load_input_dataset
from fraud_dt.risk import score_rule_based_risk, train_supervised_baseline
from fraud_dt.runtime import SimulationRunner
from fraud_dt.schemas import Scenario
from fraud_dt.synthetic import generate_synthetic_dataset

RULE_WEIGHTS = [0.2, 0.4, 0.5, 0.6, 0.8]
MODERATE_RISKS = [0.20, 0.25, 0.30, 0.35]
HIGH_RISK_MARGINS = [0.20, 0.30, 0.40]
GRID_SCENARIOS = [Scenario.INTERMITTENT_EVENING, Scenario.PEAK_THEFT, Scenario.NIGHT_THEFT]


def _throwaway_config(policy: ObservationPolicy, thresholds: Thresholds) -> AppConfig:
    return AppConfig(
        root_dir=ROOT,
        raw_dir=ROOT / "data" / "raw",
        processed_dir=ROOT / "data" / "processed",
        outputs_dir=ROOT / "outputs",
        database_path=ROOT / "outputs" / "fraud_dt.sqlite3",
        thresholds=thresholds,
        policy=policy,
    )


def run_grid(days: int = 7, seed: int = 42) -> pd.DataFrame:
    policy = ObservationPolicy()
    comparison_settings = ComparisonSettings()
    rows = []

    for scenario in GRID_SCENARIOS:
        raw_dir = ROOT / "outputs" / "_policy_optimization_tmp" / scenario.value
        generate_synthetic_dataset(raw_dir, days=days, scenario=scenario, seed=seed)
        forensic_df, billing_df, alarm_df = load_input_dataset(raw_dir)
        merged_df = build_feature_dataset(forensic_df, billing_df, alarm_df)
        scored_df = score_rule_based_risk(merged_df)
        supervised_df, _ = train_supervised_baseline(scored_df)

        for rule_weight, moderate_risk, margin in itertools.product(RULE_WEIGHTS, MODERATE_RISKS, HIGH_RISK_MARGINS):
            high_risk = min(0.95, moderate_risk + margin)
            thresholds = Thresholds(moderate_risk=moderate_risk, high_risk=high_risk)
            fusion = WeightedProbabilityFusion(rule_weight=rule_weight, supervised_weight=1.0 - rule_weight)
            runner = SimulationRunner(
                config=_throwaway_config(policy, thresholds),
                decision_engine=DecisionEngine(thresholds=thresholds, fusion_strategy=fusion),
                orchestrator=PolicyOrchestrator(policy=policy, thresholds=thresholds),
                transport=MockTransport(ble_available=True),
            )
            adaptive_df, *_ = runner.run(supervised_df)
            if adaptive_df.empty:
                continue
            _, summary = evaluate_policy(adaptive_df, "decision_probability", comparison_settings)
            rows.append(
                {
                    "scenario": scenario.value,
                    "rule_weight": rule_weight,
                    "moderate_risk": moderate_risk,
                    "high_risk": high_risk,
                    **summary,
                }
            )
    return pd.DataFrame(rows)


def pareto_frontier(df: pd.DataFrame, cost_col: str = "communication_bytes", benefit_col: str = "f1") -> pd.DataFrame:
    """Non-dominated set under 'minimize cost, maximize benefit'."""
    ordered = df.sort_values(cost_col)
    frontier_rows = []
    best_benefit_so_far = -1.0
    for _, row in ordered.iterrows():
        if row[benefit_col] > best_benefit_so_far:
            frontier_rows.append(row)
            best_benefit_so_far = row[benefit_col]
    return pd.DataFrame(frontier_rows)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Grid search / Pareto frontier for the adaptive fusion/threshold configuration")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    output_dir = ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    grid_df = run_grid(days=args.days, seed=args.seed)
    grid_df.to_csv(output_dir / "policy_pareto_grid.csv", index=False)

    aggregate_df = (
        grid_df.groupby(["rule_weight", "moderate_risk", "high_risk"], as_index=False)[
            ["f1", "recall", "precision", "communication_bytes", "mean_latency_ms"]
        ]
        .mean()
        .sort_values("communication_bytes")
    )
    aggregate_df.to_csv(output_dir / "policy_pareto_aggregate.csv", index=False)

    frontier_df = pareto_frontier(aggregate_df)
    frontier_df.to_csv(output_dir / "policy_pareto_frontier.csv", index=False)

    default_row = aggregate_df[
        (aggregate_df["rule_weight"] == 0.6) & (aggregate_df["moderate_risk"] == 0.30) & (aggregate_df["high_risk"] == 0.60)
    ]

    print(f"Grid points evaluated: {len(aggregate_df)}")
    print(f"Pareto-optimal points: {len(frontier_df)}")
    print("\nPareto frontier (aggregate across scenarios):")
    print(frontier_df.to_string(index=False))
    if not default_row.empty:
        print("\nCurrently used configuration (rule_weight=0.6, moderate_risk=0.30, high_risk=0.60):")
        print(default_row.to_string(index=False))
        on_frontier = (
            (frontier_df["rule_weight"] == 0.6)
            & (frontier_df["moderate_risk"] == 0.30)
            & (frontier_df["high_risk"] == 0.60)
        ).any()
        print(f"On Pareto frontier: {on_frontier}")
