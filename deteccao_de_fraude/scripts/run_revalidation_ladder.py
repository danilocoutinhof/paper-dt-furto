"""Runs the revalidation ladder E0 -> E4 (see `fraud_dt.revalidation`).

Outputs (per stage, in outputs/revalidation/<stage>/):
  runs.csv              one row per (scenario, replicate, policy, source, fusion)
  macro7.csv            v1-style mean over the 7 scenarios (theft-free scored 0)
  theft_pooled.csv      micro-averaged detection + episode metrics, 4 theft scenarios
  theft_macro4.csv      mean over the 4 theft scenarios (as in the submitted Table 5)
  theft_free.csv        false alarms / time in elevated modes, theft-free scenarios
  per_scenario.csv      per-scenario means with 95% bootstrap CIs
  paired_vs_fixed.csv   adaptive vs each fixed cadence (paired, Wilcoxon + Holm)
  classifier.csv        AUROC of the supervised model per scenario
and, across stages, outputs/revalidation/ladder_summary.csv/.md.

Usage:
  python scripts/run_revalidation_ladder.py --stages E0 E1 E2 E3 E4 --replicates 30
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from fraud_dt.revalidation import (
    ADAPTIVE_KEY,
    DENSE_PAPER_KEY,
    FIXED_POLICIES,
    SCENARIOS,
    STAGES,
    THEFT_SCENARIOS,
    bootstrap_ci,
    macro_seven,
    paired_against_fixed,
    per_scenario,
    protocol_record,
    run_realization,
    theft_free,
    theft_macro4,
    theft_pooled,
    train_global_model,
)

# Values reported in the submitted manuscript (Tables 4-6), single seed.
V1_PAPER = {
    "macro7_dense_f1": 0.5545,
    "macro7_dense_recall": 0.5705,
    "macro7_dense_bytes": 137835,
    "macro7_adaptive_f1": 0.5039,
    "macro7_adaptive_recall": 0.4727,
    "macro7_adaptive_bytes": 40646,
    "theft_dense_f1_mean4": 0.9703,
    "theft_dense_recall_mean4": 0.9984,
    "theft_dense_bytes": 135162,
    "theft_adaptive_f1_mean4": 0.8819,
    "theft_adaptive_recall_mean4": 0.8272,
    "theft_adaptive_bytes": 58186,
    "theft_free_adaptive_bytes": (17736 + 17736 + 16304) / 3,
}


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _row(table: pd.DataFrame, key: tuple) -> pd.Series | None:
    mask = (
        (table["policy_name"] == key[0])
        & (table["probability_source"] == key[1])
        & (table["fusion_strategy"] == key[2])
    )
    selected = table[mask]
    return None if selected.empty else selected.iloc[0]


def _fmt(row: pd.Series | None, metric: str, digits: int = 4) -> str:
    if row is None:
        return "n/a"
    mean, lo, hi = row[f"{metric}_mean"], row[f"{metric}_ci_low"], row[f"{metric}_ci_high"]
    if digits == 0:
        return f"{mean:,.0f} [{lo:,.0f}; {hi:,.0f}]"
    return f"{mean:.{digits}f} [{lo:.{digits}f}; {hi:.{digits}f}]"


def run_stage(stage: str, replicates: int, train_replicates: int, days: int, n_jobs: int, out_root: Path) -> dict:
    protocol = STAGES[stage]
    stage_dir = out_root / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()

    model = None
    model_info = {}
    if protocol.training == "global":
        model = train_global_model(protocol, train_replicates, days, n_jobs)
        model_info = {"train_samples": model.train_samples, "train_positive_rate": model.train_positive_rate}

    tasks = [(i, k) for i in range(len(SCENARIOS)) for k in range(replicates)]
    results = Parallel(n_jobs=n_jobs)(delayed(run_realization)(protocol, i, k, model, days) for i, k in tasks)
    runs = pd.DataFrame([row for rows in results for row in rows])
    runs.to_csv(stage_dir / "runs.csv", index=False)

    tables = {
        "macro7": macro_seven(runs),
        "theft_pooled": theft_pooled(runs),
        "theft_macro4": theft_macro4(runs),
        "theft_free": theft_free(runs),
        "per_scenario": per_scenario(runs),
        "paired_vs_fixed": paired_against_fixed(runs, "fused_weighted_probability"),
        "paired_vs_fixed_supervised": paired_against_fixed(runs, "supervised_probability"),
    }
    for name, table in tables.items():
        table.to_csv(stage_dir / f"{name}.csv", index=False)

    classifier = (
        runs.drop_duplicates(["scenario", "replicate"])
        .groupby("scenario")["classifier_auc_full_week"]
        .apply(lambda s: pd.Series(bootstrap_ci(s.to_numpy()), index=["mean", "ci_low", "ci_high"]))
        .unstack()
        .reset_index()
    )
    classifier.to_csv(stage_dir / "classifier.csv", index=False)

    manifest = {
        "stage": stage,
        "protocol": protocol_record(protocol),
        "replicates": replicates,
        "train_replicates_per_scenario": train_replicates if protocol.training == "global" else 0,
        "days": days,
        "test_seed_rule": "42 + scenario_index + 100 * replicate (replicate 0 = v1 campaign)",
        "train_seed_rule": "50000 + 1000 * scenario_index + replicate",
        "model": model_info,
        "git_commit": _git_commit(),
        "python": platform.python_version(),
        "elapsed_s": round(time.time() - started, 1),
    }
    (stage_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"runs": runs, **tables, "classifier": classifier, "manifest": manifest}


def ladder_row(stage: str, out: dict) -> dict:
    macro = out["macro7"]
    pooled = out["theft_pooled"]
    clean = out["theft_free"]
    paired = out["paired_vs_fixed"]
    adaptive_m, dense_m = _row(macro, ADAPTIVE_KEY), _row(macro, DENSE_PAPER_KEY)
    adaptive_p, dense_p = _row(pooled, ADAPTIVE_KEY), _row(pooled, DENSE_PAPER_KEY)
    dense_fused_p = _row(pooled, ("fixed_dense", "fused_weighted_probability", "not_applicable"))
    macro4 = out["theft_macro4"]
    adaptive_4, dense_4 = _row(macro4, ADAPTIVE_KEY), _row(macro4, DENSE_PAPER_KEY)
    adaptive_c = _row(clean, ADAPTIVE_KEY)
    dense_c = _row(clean, ("fixed_dense", "fused_weighted_probability", "not_applicable"))

    budget = None
    if not paired.empty:
        paired = paired.assign(gap=(paired["fixed_communication_bytes"] - paired["adaptive_communication_bytes"]).abs())
        budget = paired.sort_values("gap").iloc[0]

    return {
        "stage": stage,
        "description": STAGES[stage].description,
        "macro7_adaptive_f1": adaptive_m["f1_mean"],
        "macro7_dense_f1": dense_m["f1_mean"],
        "macro7_adaptive_bytes": adaptive_m["communication_bytes_mean"],
        "macro7_dense_bytes": dense_m["communication_bytes_mean"],
        "macro7_f1_retention": adaptive_m["f1_mean"] / dense_m["f1_mean"] if dense_m["f1_mean"] else np.nan,
        "macro7_recall_retention": adaptive_m["recall_mean"] / dense_m["recall_mean"] if dense_m["recall_mean"] else np.nan,
        "macro7_bytes_ratio": adaptive_m["communication_bytes_mean"] / dense_m["communication_bytes_mean"],
        "macro4_adaptive_f1": adaptive_4["f1_mean"],
        "macro4_adaptive_f1_ci": f"[{adaptive_4['f1_ci_low']:.4f}; {adaptive_4['f1_ci_high']:.4f}]",
        "macro4_adaptive_recall": adaptive_4["recall_mean"],
        "macro4_dense_f1": dense_4["f1_mean"],
        "macro4_dense_recall": dense_4["recall_mean"],
        "macro4_adaptive_bytes": adaptive_4["communication_bytes_mean"],
        "macro4_dense_bytes": dense_4["communication_bytes_mean"],
        "episode_detection_adaptive": adaptive_p["episode_detection_rate_mean"],
        "episode_delay_adaptive_min": adaptive_p["mean_delay_min_mean"],
        "episode_undetected_adaptive_min": adaptive_p["undetected_theft_min_per_scenario_mean"],
        "episode_detection_dense": dense_fused_p["episode_detection_rate_mean"],
        "episode_delay_dense_min": dense_fused_p["mean_delay_min_mean"],
        "theft_adaptive_f1": adaptive_p["f1_mean"],
        "theft_adaptive_f1_ci": f"[{adaptive_p['f1_ci_low']:.4f}; {adaptive_p['f1_ci_high']:.4f}]",
        "theft_adaptive_recall": adaptive_p["recall_mean"],
        "theft_adaptive_precision": adaptive_p["precision_mean"],
        "theft_dense_sup_f1": dense_p["f1_mean"],
        "theft_dense_sup_recall": dense_p["recall_mean"],
        "theft_dense_fused_f1": dense_fused_p["f1_mean"],
        "theft_adaptive_bytes": adaptive_p["communication_bytes_mean"],
        "theft_dense_bytes": dense_p["communication_bytes_mean"],
        "theft_bytes_ratio": adaptive_p["communication_bytes_mean"] / dense_p["communication_bytes_mean"],
        "clean_adaptive_fpr": adaptive_c["fpr_mean"],
        "clean_adaptive_fp_per_week": adaptive_c["fp_mean"],
        "clean_dense_fused_fpr": dense_c["fpr_mean"],
        "clean_adaptive_share_elevated": adaptive_c.get("share_elevated_mean", np.nan),
        "clean_adaptive_escalations": adaptive_c.get("escalations_mean", np.nan),
        "clean_adaptive_bytes": adaptive_c["communication_bytes_mean"],
        "budget_fixed_policy": None if budget is None else budget["fixed_policy"],
        "budget_fixed_bytes": None if budget is None else budget["fixed_communication_bytes"],
        "budget_fixed_f1": None if budget is None else budget["fixed_f1"],
        "budget_diff_f1": None if budget is None else budget["diff_f1_mean"],
        "budget_diff_f1_ci": None if budget is None else f"[{budget['diff_f1_ci_low']:.4f}; {budget['diff_f1_ci_high']:.4f}]",
        "budget_p_f1_holm": None if budget is None else budget["p_f1_holm"],
        "budget_diff_recall": None if budget is None else budget["diff_recall_mean"],
        "budget_p_recall_holm": None if budget is None else budget["p_recall_holm"],
        "budget_fixed_episode_detection": None if budget is None else budget.get("fixed_episode_detection_rate"),
        "budget_fixed_delay_min": None if budget is None else budget.get("fixed_mean_delay_min"),
        "budget_diff_delay_min": None if budget is None else budget.get("diff_mean_delay_min_mean"),
        "budget_diff_delay_ci": None if budget is None else f"[{budget.get('diff_mean_delay_min_ci_low', np.nan):.1f}; {budget.get('diff_mean_delay_min_ci_high', np.nan):.1f}]",
        "budget_p_delay_holm": None if budget is None else budget.get("p_mean_delay_min_holm"),
        "budget_diff_undetected_min": None if budget is None else budget.get("diff_undetected_theft_min_per_scenario_mean"),
        "budget_p_undetected_holm": None if budget is None else budget.get("p_undetected_theft_min_per_scenario_holm"),
    }


def write_ladder_markdown(ladder: pd.DataFrame, outputs: dict, out_root: Path) -> None:
    lines = [
        "# Revalidation ladder E0 -> E4 (auto-generated)",
        "",
        "Means over replicates; brackets are 95% bootstrap CIs. Adaptive = weighted fusion, decision probability.",
        "Dense (paper) = fixed_dense with supervised probability (as in Tables 4-5 of the submission).",
        "",
        "## Headline numbers per stage",
        "",
        "| Stage | Adaptive F1 (theft, pooled) | Adaptive recall | Dense F1 (sup.) | Bytes adaptive/dense (theft) | FPR adaptive (no theft) | Time elevated (no theft) | Bytes adaptive (no theft) |",
        "|---|---|---|---|---|---|---|---|",
        f"| v1 paper | {V1_PAPER['theft_adaptive_f1_mean4']:.4f}* | {V1_PAPER['theft_adaptive_recall_mean4']:.4f}* | {V1_PAPER['theft_dense_f1_mean4']:.4f}* | {V1_PAPER['theft_adaptive_bytes'] / V1_PAPER['theft_dense_bytes']:.3f} | n/r | n/r | {V1_PAPER['theft_free_adaptive_bytes']:,.0f} |",
    ]
    for _, row in ladder.iterrows():
        lines.append(
            f"| {row['stage']} | {row['theft_adaptive_f1']:.4f} {row['theft_adaptive_f1_ci']} | {row['theft_adaptive_recall']:.4f} | "
            f"{row['theft_dense_sup_f1']:.4f} | {row['theft_bytes_ratio']:.3f} | {row['clean_adaptive_fpr']:.4f} | "
            f"{row['clean_adaptive_share_elevated']:.3f} | {row['clean_adaptive_bytes']:,.0f} |"
        )
    lines += ["", "*v1 paper values are macro means over the 4 theft scenarios (single seed), not pooled.", ""]
    lines += [
        "## Mean over the 4 theft scenarios (same aggregation as the submitted Table 5)",
        "",
        "| Stage | Adaptive F1 | Adaptive recall | Dense F1 | Dense recall | Bytes adaptive | Bytes dense | Bytes ratio |",
        "|---|---|---|---|---|---|---|---|",
        "| v1 paper | 0.8819 | 0.8272 | 0.9703 | 0.9984 | 58,186 | 135,162 | 0.430 |",
    ]
    for _, row in ladder.iterrows():
        lines.append(
            f"| {row['stage']} | {row['macro4_adaptive_f1']:.4f} {row['macro4_adaptive_f1_ci']} | {row['macro4_adaptive_recall']:.4f} | "
            f"{row['macro4_dense_f1']:.4f} | {row['macro4_dense_recall']:.4f} | {row['macro4_adaptive_bytes']:,.0f} | "
            f"{row['macro4_dense_bytes']:,.0f} | {row['macro4_adaptive_bytes'] / row['macro4_dense_bytes']:.3f} |"
        )
    lines += [
        "",
        "## Episode-level detection (4 theft scenarios, R1.3)",
        "",
        "| Stage | Adaptive: episodes detected | Adaptive: mean delay (min) | Adaptive: undetected theft (min/scenario-week) | Dense: episodes detected | Dense: mean delay (min) |",
        "|---|---|---|---|---|---|",
    ]
    for _, row in ladder.iterrows():
        lines.append(
            f"| {row['stage']} | {row['episode_detection_adaptive']:.3f} | {row['episode_delay_adaptive_min']:.1f} | "
            f"{row['episode_undetected_adaptive_min']:.0f} | {row['episode_detection_dense']:.3f} | {row['episode_delay_dense_min']:.1f} |"
        )
    lines.append("")
    lines += [
        "## v1-style 7-scenario means (Table 4 analogue)",
        "",
        "| Stage | Adaptive F1 | Dense F1 | F1 retention | Recall retention | Bytes adaptive | Bytes dense | Bytes ratio |",
        "|---|---|---|---|---|---|---|---|",
        f"| v1 paper | 0.5039 | 0.5545 | 0.909 | 0.829 | 40,646 | 137,835 | 0.295 |",
    ]
    for _, row in ladder.iterrows():
        lines.append(
            f"| {row['stage']} | {row['macro7_adaptive_f1']:.4f} | {row['macro7_dense_f1']:.4f} | {row['macro7_f1_retention']:.3f} | "
            f"{row['macro7_recall_retention']:.3f} | {row['macro7_adaptive_bytes']:,.0f} | {row['macro7_dense_bytes']:,.0f} | {row['macro7_bytes_ratio']:.3f} |"
        )
    lines += [
        "",
        "## Adaptive vs budget-matched fixed cadence (theft scenarios, same detector = weighted fusion)",
        "",
        "Tick-level (F1, recall) and episode-level (mean delay, undetected theft minutes). Negative delay/undetected differences favor the adaptive policy.",
        "",
        "| Stage | Closest fixed cadence | Fixed bytes | Diff F1 | p (Holm) | Diff recall | Fixed: episodes detected | Diff mean delay (min) | p (Holm) | Diff undetected (min) | p (Holm) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, row in ladder.iterrows():
        lines.append(
            f"| {row['stage']} | {row['budget_fixed_policy']} | {row['budget_fixed_bytes']:,.0f} | "
            f"{row['budget_diff_f1']:+.4f} {row['budget_diff_f1_ci']} | {row['budget_p_f1_holm']:.2g} | {row['budget_diff_recall']:+.4f} | "
            f"{row['budget_fixed_episode_detection']:.3f} | {row['budget_diff_delay_min']:+.1f} {row['budget_diff_delay_ci']} | {row['budget_p_delay_holm']:.2g} | "
            f"{row['budget_diff_undetected_min']:+.0f} | {row['budget_p_undetected_holm']:.2g} |"
        )
    for stage, out in outputs.items():
        lines += ["", f"### {stage}: adaptive vs every fixed cadence (theft scenarios, weighted-fusion detector)", "",
                  "| Fixed | Fixed bytes | Adaptive bytes | Diff F1 | Diff episodes detected | Diff mean delay (min) | Diff undetected (min) | p delay (Holm) |",
                  "|---|---|---|---|---|---|---|---|"]
        for _, row in out["paired_vs_fixed"].iterrows():
            lines.append(
                f"| {row['fixed_policy']} | {row['fixed_communication_bytes']:,.0f} | {row['adaptive_communication_bytes']:,.0f} | {row['diff_f1_mean']:+.4f} | "
                f"{row.get('diff_episode_detection_rate_mean', np.nan):+.3f} | {row.get('diff_mean_delay_min_mean', np.nan):+.1f} | "
                f"{row.get('diff_undetected_theft_min_per_scenario_mean', np.nan):+.0f} | {row.get('p_mean_delay_min_holm', np.nan):.2g} |"
            )

    for stage, out in outputs.items():
        lines += ["", f"## {stage}: per-scenario (adaptive weighted vs fixed_dense supervised)", ""]
        lines += ["| Scenario | Dense F1 | Dense recall | Dense bytes | Adaptive F1 | Adaptive recall | Adaptive bytes | Adaptive FPR | Time elevated |", "|---|---|---|---|---|---|---|---|---|"]
        table = out["per_scenario"]
        for scenario in [s.value for s in SCENARIOS]:
            sub = table[table["scenario"] == scenario]
            dense = _row(sub, DENSE_PAPER_KEY)
            adaptive = _row(sub, ADAPTIVE_KEY)
            lines.append(
                f"| {scenario} | {_fmt(dense, 'f1')} | {_fmt(dense, 'recall')} | {_fmt(dense, 'communication_bytes', 0)} | "
                f"{_fmt(adaptive, 'f1')} | {_fmt(adaptive, 'recall')} | {_fmt(adaptive, 'communication_bytes', 0)} | "
                f"{_fmt(adaptive, 'fpr')} | {_fmt(adaptive, 'share_elevated', 3)} |"
            )
        lines += ["", f"### {stage}: all policies, theft scenarios pooled", "", "| Policy | Source | Fusion | F1 | Recall | Precision | Episodes detected | Mean delay (min) | Bytes/scenario |", "|---|---|---|---|---|---|---|---|---|"]
        pooled = out["theft_pooled"].sort_values("communication_bytes_mean")
        for _, row in pooled.iterrows():
            lines.append(
                f"| {row['policy_name']} | {row['probability_source']} | {row['fusion_strategy']} | {_fmt(row, 'f1')} | "
                f"{_fmt(row, 'recall')} | {_fmt(row, 'precision')} | {_fmt(row, 'episode_detection_rate', 3)} | {_fmt(row, 'mean_delay_min', 1)} | {_fmt(row, 'communication_bytes', 0)} |"
            )
        lines += ["", f"### {stage}: fusion strategies (adaptive, decision probability)", "", "| Fusion | F1 theft pooled | Recall | Bytes theft | FPR no theft | Time elevated no theft |", "|---|---|---|---|---|---|"]
        for fusion in ["weighted", "conservative_max", "context_aware"]:
            key = ("adaptive", "decision_probability", fusion)
            p, c = _row(out["theft_pooled"], key), _row(out["theft_free"], key)
            lines.append(
                f"| {fusion} | {_fmt(p, 'f1')} | {_fmt(p, 'recall')} | {_fmt(p, 'communication_bytes', 0)} | {_fmt(c, 'fpr')} | {_fmt(c, 'share_elevated', 3)} |"
            )
        lines += ["", f"### {stage}: supervised classifier AUROC on the evaluated week", "", "| Scenario | AUROC |", "|---|---|"]
        for _, row in out["classifier"].iterrows():
            auc = "n/a (single class)" if pd.isna(row["mean"]) else f"{row['mean']:.4f} [{row['ci_low']:.4f}; {row['ci_high']:.4f}]"
            lines.append(f"| {row['scenario']} | {auc} |")
    (out_root / "ladder_summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stages", nargs="+", default=list(STAGES), choices=list(STAGES))
    parser.add_argument("--replicates", type=int, default=30)
    parser.add_argument("--train-replicates", type=int, default=10)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--jobs", type=int, default=-2)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "revalidation")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs, ladder_rows = {}, []
    for stage in args.stages:
        print(f"[{stage}] {STAGES[stage].description} ...", flush=True)
        outputs[stage] = run_stage(stage, args.replicates, args.train_replicates, args.days, args.jobs, args.output_dir)
        ladder_rows.append(ladder_row(stage, outputs[stage]))
        print(f"[{stage}] done in {outputs[stage]['manifest']['elapsed_s']} s", flush=True)

    ladder = pd.DataFrame(ladder_rows)
    ladder.to_csv(args.output_dir / "ladder_summary.csv", index=False)
    write_ladder_markdown(ladder, outputs, args.output_dir)
    print(ladder.T.to_string())
