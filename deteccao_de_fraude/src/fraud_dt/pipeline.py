from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless, file-only backend; avoids a Tk dependency that is not guaranteed to be present
import matplotlib.pyplot as plt
import pandas as pd

from .comparison import ComparisonSettings, evaluate_policy
from .config import build_config
from .control import PolicyOrchestrator
from .decision import DecisionEngine, build_fusion_strategies
from .devices import MockTransport
from .features import build_feature_dataset, load_input_dataset
from .policy import apply_fixed_dense_policy, apply_fixed_long_policy, apply_fixed_short_policy
from .reporting import build_run_manifest, write_json_manifest
from .risk import compute_model_comparison_and_importance, score_rule_based_risk, train_supervised_baseline
from .runtime import SimulationRunner
from .storage import persist_dataframe


def _run_adaptive_twin_loop(df: pd.DataFrame, config, fusion_strategy_name: str):
    if df.empty:
        empty = pd.DataFrame()
        return empty, empty, empty, empty, empty

    fusion_strategy = build_fusion_strategies()[fusion_strategy_name]
    runner = SimulationRunner(
        config=config,
        decision_engine=DecisionEngine(thresholds=config.thresholds, fusion_strategy=fusion_strategy),
        orchestrator=PolicyOrchestrator(policy=config.policy, thresholds=config.thresholds),
        transport=MockTransport(ble_available=True),
    )
    return runner.run(df)


def _write_summary(df: pd.DataFrame, comparison_df: pd.DataFrame, model_metrics_df: pd.DataFrame, command_df: pd.DataFrame, transport_df: pd.DataFrame, fusion_summary_df: pd.DataFrame, output_dir: Path) -> Path:
    summary_path = output_dir / "run_summary.md"
    mode_counts = df["observation_mode"].value_counts().to_dict()
    best_policy = comparison_df.sort_values(["f1", "communication_bytes"], ascending=[False, True]).iloc[0]
    best_fusion = fusion_summary_df.sort_values(["f1", "communication_bytes"], ascending=[False, True]).iloc[0] if not fusion_summary_df.empty else None
    model_metrics = model_metrics_df.iloc[0]
    applied_reconfigurations = int((command_df["action"] == "reconfigure").sum()) if not command_df.empty else 0
    ble_fallbacks = int(transport_df["fallback_used"].sum()) if not transport_df.empty else 0
    lines = [
        "# Run Summary",
        "",
        f"- samples: {len(df)}",
        f"- fusion strategy (default adaptive output): {df['fusion_strategy'].iloc[0] if 'fusion_strategy' in df.columns and not df.empty else 'n/a'}",
        f"- observed samples in adaptive runtime: {int(df['observed'].sum())}",
        f"- mean rule-based risk: {df['risk_probability'].mean():.4f}",
        f"- max rule-based risk: {df['risk_probability'].max():.4f}",
        f"- mean supervised probability: {df['supervised_probability'].mean():.4f}",
        f"- mean decision probability: {df['decision_probability'].mean():.4f}",
        f"- mean relative divergence: {df['relative_divergence'].mean():.4f}",
        f"- max relative divergence: {df['relative_divergence'].max():.4f}",
        f"- adaptive mode counts: {mode_counts}",
        f"- reconfiguration commands: {applied_reconfigurations}",
        f"- transport fallback to BLE: {ble_fallbacks}",
        "",
        "## Supervised baseline",
        f"- model: {model_metrics['model']}",
        f"- accuracy: {model_metrics['accuracy']:.4f}",
        f"- precision: {model_metrics['precision']:.4f}",
        f"- recall: {model_metrics['recall']:.4f}",
        f"- f1: {model_metrics['f1']:.4f}",
        f"- roc_auc: {model_metrics['roc_auc']:.4f}",
        "",
        "## Best policy by F1 then communication cost",
        f"- policy: {best_policy['policy_name']}",
        f"- probability source: {best_policy['probability_source']}",
        f"- observed samples: {int(best_policy['observed_samples'])}",
        f"- communication bytes: {int(best_policy['communication_bytes'])}",
        f"- precision: {best_policy['precision']:.4f}",
        f"- recall: {best_policy['recall']:.4f}",
        f"- f1: {best_policy['f1']:.4f}",
        f"- critical slot hit: {int(best_policy['critical_slot_hit'])}",
        f"- critical slot score (relaxed): {best_policy['critical_slot_score_relaxed']:.4f}",
    ]
    if best_fusion is not None:
        lines.extend([
            "",
            "## Best adaptive fusion strategy",
            f"- fusion strategy: {best_fusion['fusion_strategy']}",
            f"- observed samples: {int(best_fusion['observed_samples'])}",
            f"- communication bytes: {int(best_fusion['communication_bytes'])}",
            f"- precision: {best_fusion['precision']:.4f}",
            f"- recall: {best_fusion['recall']:.4f}",
            f"- f1: {best_fusion['f1']:.4f}",
        ])
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path


def _plot_risk(df: pd.DataFrame, output_dir: Path) -> None:
    plt.figure(figsize=(12, 4))
    plt.plot(df["timestamp"], df["risk_probability"], label="rule_based_risk")
    plt.plot(df["timestamp"], df["supervised_probability"], label="supervised_probability", alpha=0.8)
    plt.plot(df["timestamp"], df["decision_probability"], label="decision_probability", alpha=0.8)
    plt.ylabel("probability")
    plt.xlabel("timestamp")
    plt.title("Risk over time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "risk_over_time.png", dpi=150)
    plt.close()


def _plot_modes(df: pd.DataFrame, output_dir: Path) -> None:
    mode_map = {"basal": 0, "moderate": 1, "aggressive": 2}
    plt.figure(figsize=(12, 4))
    plt.step(df["timestamp"], df["observation_mode"].map(mode_map), where="post")
    plt.yticks([0, 1, 2], ["basal", "moderate", "aggressive"])
    plt.xlabel("timestamp")
    plt.title("Adaptive observation modes")
    plt.tight_layout()
    plt.savefig(output_dir / "observation_modes.png", dpi=150)
    plt.close()


def _plot_policy_comparison(comparison_df: pd.DataFrame, output_dir: Path) -> None:
    fig, ax1 = plt.subplots(figsize=(10, 4))
    x = range(len(comparison_df))
    ax1.bar(x, comparison_df["communication_bytes"], color="tab:blue", alpha=0.6)
    ax1.set_ylabel("communication bytes")
    ax1.set_xticks(list(x))
    labels = []
    for _, row in comparison_df.iterrows():
        fusion_suffix = f"\n{row['fusion_strategy']}" if "fusion_strategy" in row and row["fusion_strategy"] != "not_applicable" else ""
        labels.append(f"{row['policy_name']}\n{row['probability_source']}{fusion_suffix}")
    ax1.set_xticklabels(labels, rotation=0)
    ax2 = ax1.twinx()
    ax2.plot(x, comparison_df["f1"], color="tab:red", marker="o")
    ax2.set_ylabel("F1 score")
    plt.title("Policy comparison")
    fig.tight_layout()
    plt.savefig(output_dir / "policy_comparison.png", dpi=150)
    plt.close(fig)


def _plot_roc_curves(roc_curve_df: pd.DataFrame, output_dir: Path) -> None:
    if roc_curve_df.empty:
        return
    plt.figure(figsize=(6, 6))
    for model_name, group in roc_curve_df.groupby("model"):
        plt.plot(group["false_positive_rate"], group["true_positive_rate"], marker=".", label=model_name)
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="chance")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("ROC curves (held-out test split)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "roc_curves.png", dpi=150)
    plt.close()


def _plot_fusion_comparison(fusion_df: pd.DataFrame, output_dir: Path) -> None:
    if fusion_df.empty:
        return
    fig, ax1 = plt.subplots(figsize=(8, 4))
    x = range(len(fusion_df))
    ax1.bar(x, fusion_df["communication_bytes"], color="tab:green", alpha=0.6)
    ax1.set_ylabel("communication bytes")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(fusion_df["fusion_strategy"].tolist(), rotation=0)
    ax2 = ax1.twinx()
    ax2.plot(x, fusion_df["f1"], color="tab:purple", marker="o")
    ax2.set_ylabel("F1 score")
    plt.title("Adaptive fusion strategy comparison")
    fig.tight_layout()
    plt.savefig(output_dir / "fusion_strategy_comparison.png", dpi=150)
    plt.close(fig)


def run_pipeline(project_root: Path, input_dir: Path, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    config = build_config(project_root)
    forensic_df, billing_df, alarm_df = load_input_dataset(input_dir)
    merged_df = build_feature_dataset(forensic_df, billing_df, alarm_df)
    scored_df = score_rule_based_risk(merged_df)
    supervised_df, model_metrics_df = train_supervised_baseline(scored_df)
    model_comparison_df, feature_importance_df, roc_curve_df = compute_model_comparison_and_importance(scored_df)

    fusion_outputs = {}
    for fusion_strategy_name in build_fusion_strategies().keys():
        fusion_outputs[fusion_strategy_name] = _run_adaptive_twin_loop(supervised_df, config, fusion_strategy_name)

    default_fusion_strategy = "weighted"
    adaptive_df, decision_df, state_history_df, command_df, transport_df = fusion_outputs[default_fusion_strategy]
    fixed_long_df = apply_fixed_long_policy(supervised_df, config.policy)
    fixed_short_df = apply_fixed_short_policy(supervised_df, config.policy)
    fixed_dense_df = apply_fixed_dense_policy(supervised_df, config.policy)
    fixed_long_df["fusion_strategy"] = "not_applicable"
    fixed_short_df["fusion_strategy"] = "not_applicable"
    fixed_dense_df["fusion_strategy"] = "not_applicable"

    comparison_settings = ComparisonSettings(
        payload_bytes_per_sample=config.experiment.payload_bytes_per_sample,
        prediction_threshold=config.experiment.prediction_threshold,
    )

    evaluated_frames = []
    comparison_rows = []
    fusion_comparison_rows = []

    for probability_source in ["risk_probability", "supervised_probability"]:
        for policy_df in [fixed_long_df, fixed_short_df, fixed_dense_df, adaptive_df]:
            if probability_source not in policy_df.columns:
                continue
            evaluated_df, summary = evaluate_policy(policy_df, probability_source, comparison_settings)
            summary["fusion_strategy"] = str(policy_df["fusion_strategy"].iloc[0]) if "fusion_strategy" in policy_df.columns else "not_applicable"
            evaluated_frames.append(evaluated_df)
            comparison_rows.append(summary)

    for fusion_strategy_name, (fusion_adaptive_df, fusion_decision_df, _, _, _) in fusion_outputs.items():
        evaluated_df, summary = evaluate_policy(fusion_adaptive_df, "decision_probability", comparison_settings)
        summary["fusion_strategy"] = fusion_strategy_name
        evaluated_frames.append(evaluated_df)
        comparison_rows.append(summary)
        fusion_summary = summary.copy()
        fusion_summary["decision_probability_source_detail"] = fusion_decision_df["probability_source"].mode().iloc[0] if not fusion_decision_df.empty else "n/a"
        fusion_comparison_rows.append(fusion_summary)

    comparison_df = pd.DataFrame(comparison_rows)
    evaluated_policies_df = pd.concat(evaluated_frames, ignore_index=True)
    fusion_comparison_df = pd.DataFrame(fusion_comparison_rows).sort_values(["f1", "communication_bytes"], ascending=[False, True])

    merged_path = output_dir / "merged_dataset.csv"
    scored_path = output_dir / "risk_scored_dataset.csv"
    supervised_path = output_dir / "supervised_scored_dataset.csv"
    policy_path = output_dir / "observation_policy.csv"
    comparison_path = output_dir / "policy_comparison.csv"
    model_metrics_path = output_dir / "model_metrics.csv"
    decision_path = output_dir / "twin_decisions.csv"
    state_history_path = output_dir / "twin_state_history.csv"
    command_path = output_dir / "command_plan.csv"
    transport_path = output_dir / "transport_delivery.csv"
    fusion_comparison_path = output_dir / "fusion_strategy_comparison.csv"
    model_comparison_path = output_dir / "model_comparison.csv"
    feature_importance_path = output_dir / "feature_importance.csv"
    roc_curve_path = output_dir / "roc_curve_points.csv"
    manifest_path = output_dir / "run_manifest.json"

    merged_df.to_csv(merged_path, index=False)
    scored_df.to_csv(scored_path, index=False)
    supervised_df.to_csv(supervised_path, index=False)
    adaptive_df.to_csv(policy_path, index=False)
    comparison_df.to_csv(comparison_path, index=False)
    model_metrics_df.to_csv(model_metrics_path, index=False)
    decision_df.to_csv(decision_path, index=False)
    state_history_df.to_csv(state_history_path, index=False)
    command_df.to_csv(command_path, index=False)
    transport_df.to_csv(transport_path, index=False)
    fusion_comparison_df.to_csv(fusion_comparison_path, index=False)
    model_comparison_df.to_csv(model_comparison_path, index=False)
    feature_importance_df.to_csv(feature_importance_path, index=False)
    roc_curve_df.to_csv(roc_curve_path, index=False)

    persist_dataframe(merged_df, "merged_dataset", config.database_path)
    persist_dataframe(scored_df, "risk_scored_dataset", config.database_path)
    persist_dataframe(supervised_df, "supervised_scored_dataset", config.database_path)
    persist_dataframe(adaptive_df, "adaptive_policy", config.database_path)
    persist_dataframe(comparison_df, "policy_comparison", config.database_path)
    persist_dataframe(model_metrics_df, "model_metrics", config.database_path)
    persist_dataframe(evaluated_policies_df, "evaluated_policy_rows", config.database_path)
    persist_dataframe(decision_df, "twin_decisions", config.database_path)
    persist_dataframe(state_history_df, "twin_state_history", config.database_path)
    persist_dataframe(command_df, "command_plan", config.database_path)
    persist_dataframe(transport_df, "transport_delivery", config.database_path)
    persist_dataframe(fusion_comparison_df, "fusion_strategy_summary", config.database_path)
    if not model_comparison_df.empty:
        persist_dataframe(model_comparison_df, "model_comparison", config.database_path)
        persist_dataframe(feature_importance_df, "feature_importance", config.database_path)
        persist_dataframe(roc_curve_df, "roc_curve_points", config.database_path)

    _write_summary(adaptive_df, comparison_df, model_metrics_df, command_df, transport_df, fusion_comparison_df, output_dir)
    _plot_risk(adaptive_df, output_dir)
    _plot_modes(adaptive_df, output_dir)
    _plot_policy_comparison(comparison_df, output_dir)
    _plot_fusion_comparison(fusion_comparison_df, output_dir)
    _plot_roc_curves(roc_curve_df, output_dir)

    manifest = build_run_manifest(
        project_root=project_root,
        input_dir=input_dir,
        output_dir=output_dir,
        config=config,
        extra={
            "default_fusion_strategy": default_fusion_strategy,
            "fusion_strategies_evaluated": list(build_fusion_strategies().keys()),
            "samples": len(adaptive_df),
            "observed_samples": int(adaptive_df["observed"].sum()) if not adaptive_df.empty else 0,
            "reconfiguration_commands": int((command_df["action"] == "reconfigure").sum()) if not command_df.empty else 0,
        },
    )
    write_json_manifest(manifest_path, manifest)

    return {
        "merged": merged_path,
        "scored": scored_path,
        "supervised": supervised_path,
        "policy": policy_path,
        "comparison": comparison_path,
        "model_metrics": model_metrics_path,
        "decisions": decision_path,
        "state_history": state_history_path,
        "command_plan": command_path,
        "transport_delivery": transport_path,
        "fusion_comparison": fusion_comparison_path,
        "model_comparison": model_comparison_path,
        "feature_importance": feature_importance_path,
        "roc_curve_points": roc_curve_path,
        "run_manifest": manifest_path,
        "database": config.database_path,
        "summary": output_dir / "run_summary.md",
        "risk_plot": output_dir / "risk_over_time.png",
        "mode_plot": output_dir / "observation_modes.png",
        "comparison_plot": output_dir / "policy_comparison.png",
        "fusion_plot": output_dir / "fusion_strategy_comparison.png",
    }
