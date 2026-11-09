from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd

from fraud_dt.pipeline import run_pipeline
from fraud_dt.reporting import build_campaign_manifest, export_campaign_tables_to_tex, write_json_manifest
from fraud_dt.schemas import Scenario
from fraud_dt.synthetic import generate_synthetic_dataset


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run a multi-scenario experiment campaign")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    experiment_output_dir = ROOT / "outputs" / "campaign"
    experiment_output_dir.mkdir(parents=True, exist_ok=True)

    all_rows = []
    fusion_rows = []
    for idx, scenario in enumerate(Scenario):
        scenario_raw_dir = ROOT / "data" / "raw" / scenario.value
        scenario_out_dir = experiment_output_dir / scenario.value
        generate_synthetic_dataset(
            output_dir=scenario_raw_dir,
            days=args.days,
            scenario=scenario,
            seed=args.seed + idx,
        )
        run_pipeline(ROOT, scenario_raw_dir, scenario_out_dir)
        comparison_df = pd.read_csv(scenario_out_dir / "policy_comparison.csv")
        comparison_df.insert(0, "scenario", scenario.value)
        fusion_df = pd.read_csv(scenario_out_dir / "fusion_strategy_comparison.csv")
        fusion_df.insert(0, "scenario", scenario.value)
        model_metrics_df = pd.read_csv(scenario_out_dir / "model_metrics.csv")
        model_metrics_df.insert(0, "scenario", scenario.value)
        model_metrics_df.to_csv(scenario_out_dir / "model_metrics.csv", index=False)
        all_rows.append(comparison_df)
        fusion_rows.append(fusion_df)

    campaign_df = pd.concat(all_rows, ignore_index=True)
    campaign_df.to_csv(experiment_output_dir / "campaign_policy_comparison.csv", index=False)

    aggregate_df = (
        campaign_df.groupby(["policy_name", "probability_source", "fusion_strategy"], as_index=False)[
            ["communication_bytes", "precision", "recall", "f1", "critical_slot_hit", "critical_slot_score_relaxed", "false_alert_rate"]
        ]
        .mean()
        .sort_values(["probability_source", "f1", "communication_bytes"], ascending=[True, False, True])
    )
    aggregate_df.to_csv(experiment_output_dir / "campaign_policy_aggregate.csv", index=False)

    fusion_campaign_df = pd.concat(fusion_rows, ignore_index=True)
    fusion_aggregate_df = (
        fusion_campaign_df.groupby(["fusion_strategy"], as_index=False)[
            ["communication_bytes", "precision", "recall", "f1", "critical_slot_hit", "critical_slot_score_relaxed", "false_alert_rate"]
        ]
        .mean()
        .sort_values(["f1", "communication_bytes"], ascending=[False, True])
    )
    fusion_aggregate_df.to_csv(experiment_output_dir / "campaign_fusion_strategy_aggregate.csv", index=False)

    summary_lines = [
        "# Campaign Summary",
        "",
        f"- scenarios: {', '.join([s.value for s in Scenario])}",
        f"- runs: {len(list(Scenario))}",
        "",
        "## Aggregate policy comparison",
    ]
    for _, row in aggregate_df.iterrows():
        summary_lines.append(
            f"- {row['policy_name']} / {row['probability_source']} / {row['fusion_strategy']}: "
            f"f1={row['f1']:.4f}, recall={row['recall']:.4f}, "
            f"bytes={row['communication_bytes']:.1f}, critical_slot_hit={row['critical_slot_hit']:.4f}, "
            f"critical_slot_score_relaxed={row['critical_slot_score_relaxed']:.4f}"
        )
    summary_lines.extend(["", "## Aggregate adaptive fusion comparison"])
    for _, row in fusion_aggregate_df.iterrows():
        summary_lines.append(
            f"- {row['fusion_strategy']}: f1={row['f1']:.4f}, recall={row['recall']:.4f}, "
            f"bytes={row['communication_bytes']:.1f}, critical_slot_hit={row['critical_slot_hit']:.4f}, "
            f"critical_slot_score_relaxed={row['critical_slot_score_relaxed']:.4f}"
        )
    (experiment_output_dir / "campaign_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")

    write_json_manifest(
        experiment_output_dir / "campaign_manifest.json",
        build_campaign_manifest(
            project_root=ROOT,
            output_dir=experiment_output_dir,
            extra={
                "days": args.days,
                "seed": args.seed,
                "scenarios": [s.value for s in Scenario],
                "runs": len(list(Scenario)),
            },
        ),
    )
    export_campaign_tables_to_tex(
        aggregate_df,
        fusion_aggregate_df,
        experiment_output_dir / "campaign_tables.tex",
    )
