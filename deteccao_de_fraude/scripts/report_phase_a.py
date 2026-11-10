"""Phase A report (backfill, basal period, evidence cap) from the E5 outputs.

Run the stage first:
  python scripts/run_revalidation_ladder.py --stages E5 --replicates 30
then:
  python scripts/report_phase_a.py
Writes outputs/revalidation/E5/phase_a_summary.csv and phase_a_report.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np
import pandas as pd

from fraud_dt.revalidation import (
    NO_THEFT_SCENARIOS,
    PHASE_A_VARIANTS,
    SCENARIOS,
    THEFT_SCENARIOS,
    bootstrap_ci,
    paired_against_fixed,
)

FIXED_REFERENCES = ["fixed_dense", "fixed_short", "fixed_20", "fixed_25", "fixed_30", "fixed_40", "fixed_long"]
REFERENCE_FOR_PAIRING = ["fixed_short", "fixed_20", "fixed_30"]
SENSITIVITY_RECORD_FACTOR = 0.5  # backfill records of 32 B instead of 64 B


def _policy_rows(runs: pd.DataFrame) -> pd.DataFrame:
    """One (policy, scenario, replicate) row per policy of interest, all with
    the weighted-fusion detector."""
    fixed = runs[(runs["policy_name"].isin(FIXED_REFERENCES)) & (runs["probability_source"] == "fused_weighted_probability")]
    adaptive = runs[(runs["probability_source"] == "decision_probability") & (runs["fusion_strategy"] == "weighted")]
    out = pd.concat([fixed, adaptive], ignore_index=True)
    out["backfill_bytes"] = out.get("backfill_bytes", pd.Series(np.nan, index=out.index)).fillna(0.0)
    out["bytes_sensitivity"] = out["communication_bytes"] - (1 - SENSITIVITY_RECORD_FACTOR) * out["backfill_bytes"]
    return out


def _pooled_theft(rows: pd.DataFrame) -> pd.DataFrame:
    theft = rows[rows["scenario"].isin(THEFT_SCENARIOS)]
    sums = ["tp", "fn", "theft_received", "episodes", "episodes_detected", "episodes_detected_live", "delay_live_sum_min",
            "undetected_theft_min", "communication_bytes", "bytes_sensitivity", "backfill_bytes"]
    per = theft.groupby(["policy_name", "replicate"], as_index=False)[sums].sum()
    n = len(THEFT_SCENARIOS)
    per["evidence_received"] = per["theft_received"] / (per["tp"] + per["fn"])
    per["evidence_flagged"] = per["tp"] / (per["tp"] + per["fn"])
    per["episodes_documented"] = per["episodes_detected"] / per["episodes"]
    per["episodes_live"] = per["episodes_detected_live"] / per["episodes"]
    per["delay_live_min"] = per["delay_live_sum_min"] / per["episodes_detected_live"].replace(0, np.nan)
    per["undetected_min"] = per["undetected_theft_min"] / n
    for column in ["communication_bytes", "bytes_sensitivity", "backfill_bytes"]:
        per[column] = per[column] / n
    return per


def _pooled_clean(rows: pd.DataFrame) -> pd.DataFrame:
    clean = rows[rows["scenario"].isin(NO_THEFT_SCENARIOS)]
    per = clean.groupby(["policy_name", "replicate"], as_index=False)[["fp", "communication_bytes", "bytes_sensitivity"]].mean()
    return per.rename(columns={"fp": "clean_fp_week", "communication_bytes": "clean_bytes", "bytes_sensitivity": "clean_bytes_sensitivity"})


METRICS = [
    ("communication_bytes", "Bytes (furto)", 0),
    ("bytes_sensitivity", "Bytes, registro de 32 B", 0),
    ("episodes_live", "Episódios detectados em tempo real", 3),
    ("delay_live_min", "Atraso em tempo real (min)", 1),
    ("episodes_documented", "Episódios documentados (com backfill)", 3),
    ("evidence_received", "Evidência recebida", 3),
    ("evidence_flagged", "Evidência sinalizada (recall)", 3),
    ("clean_fp_week", "Falsos positivos/semana (sem furto)", 2),
    ("clean_bytes", "Bytes (sem furto)", 0),
]


def summarize(theft: pd.DataFrame, clean: pd.DataFrame) -> pd.DataFrame:
    merged = theft.merge(clean, on=["policy_name", "replicate"], how="left")
    rows = []
    for policy, group in merged.groupby("policy_name"):
        row = {"policy_name": policy}
        for metric, _, _ in METRICS:
            mean, lo, hi = bootstrap_ci(group[metric].to_numpy(dtype=float))
            row[f"{metric}_mean"], row[f"{metric}_ci_low"], row[f"{metric}_ci_high"] = mean, lo, hi
        rows.append(row)
    return pd.DataFrame(rows).sort_values("communication_bytes_mean")


def non_dominated(summary: pd.DataFrame) -> set[str]:
    """Policies not dominated on (bytes min, live delay min, evidence flagged max, live detection max)."""
    names = set()
    values = summary[["policy_name", "communication_bytes_mean", "delay_live_min_mean", "evidence_flagged_mean", "episodes_live_mean"]].to_numpy()
    for a in values:
        dominated = False
        for b in values:
            if b[0] == a[0]:
                continue
            better_or_equal = b[1] <= a[1] and b[2] <= a[2] and b[3] >= a[3] and b[4] >= a[4]
            strictly = b[1] < a[1] or b[2] < a[2] or b[3] > a[3] or b[4] > a[4]
            if better_or_equal and strictly:
                dominated = True
                break
        if not dominated:
            names.add(a[0])
    return names


def _cell(row: pd.Series, metric: str, digits: int) -> str:
    mean = row[f"{metric}_mean"]
    if pd.isna(mean):
        return "n/a"
    if digits == 0:
        return f"{mean:,.0f}"
    return f"{mean:.{digits}f} [{row[f'{metric}_ci_low']:.{digits}f}; {row[f'{metric}_ci_high']:.{digits}f}]"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage-dir", type=Path, default=ROOT / "outputs" / "revalidation" / "E5")
    args = parser.parse_args()

    runs = pd.read_csv(args.stage_dir / "runs.csv")
    rows = _policy_rows(runs)
    theft, clean = _pooled_theft(rows), _pooled_clean(rows)
    summary = summarize(theft, clean)
    frontier = non_dominated(summary)
    summary["non_dominated"] = summary["policy_name"].isin(frontier)
    summary.to_csv(args.stage_dir / "phase_a_summary.csv", index=False)

    paired = []
    for variant in ["adaptive"] + [v.name for v in PHASE_A_VARIANTS]:
        table = paired_against_fixed(runs, "fused_weighted_probability", adaptive_key=(variant, "decision_probability", "weighted"))
        paired.append(table[table["fixed_policy"].isin(REFERENCE_FOR_PAIRING)])
    paired_df = pd.concat(paired, ignore_index=True)
    paired_df.to_csv(args.stage_dir / "phase_a_paired.csv", index=False)

    lines = [
        "# Phase A (stage E5 = E4 protocol + new policies) — auto-generated",
        "",
        "4 theft scenarios pooled (bytes per scenario-week) and 3 theft-free scenarios (mean per scenario-week).",
        "All policies use the weighted-fusion detector. `*` = not dominated on (bytes, live delay, evidence flagged, live detection).",
        "",
        "| Policy | " + " | ".join(label for _, label, _ in METRICS) + " |",
        "|---|" + "---|" * len(METRICS),
    ]
    for _, row in summary.iterrows():
        mark = "*" if row["non_dominated"] else ""
        lines.append(f"| {row['policy_name']}{mark} | " + " | ".join(_cell(row, m, d) for m, _, d in METRICS) + " |")

    lines += ["", "## Paired differences vs fixed cadences (policy − fixed; theft scenarios)", "",
              "| Policy | Fixed | Bytes diff | Live detection diff | Live delay diff (min) | p (Holm) | Evidence flagged diff | p (Holm) |",
              "|---|---|---|---|---|---|---|---|"]
    for _, row in paired_df.iterrows():
        lines.append(
            f"| {row['policy']} | {row['fixed_policy']} | {row['diff_communication_bytes_mean']:+,.0f} | "
            f"{row.get('diff_episode_detection_live_rate_mean', np.nan):+.3f} | {row.get('diff_mean_delay_live_min_mean', np.nan):+.1f} | "
            f"{row.get('p_mean_delay_live_min_holm', np.nan):.2g} | {row.get('diff_recall_mean', np.nan):+.3f} | {row.get('p_recall_holm', np.nan):.2g} |"
        )

    lines += ["", "## Per scenario (mean of 30 realizations)", ""]
    key_policies = ["fixed_short", "fixed_30", "adaptive", "adaptive_b30", "adaptive_b60_cap", "adaptive_b60_bf", "adaptive_b30_bf", "adaptive_b60_bf_cap", "fixed_60_bf", "fixed_30_bf"]
    lines += ["| Scenario | Policy | Bytes | Live detection | Live delay (min) | Evidence flagged | Backfill bytes |", "|---|---|---|---|---|---|---|"]
    for scenario in [s.value for s in SCENARIOS if s.value in THEFT_SCENARIOS]:
        sub = rows[rows["scenario"] == scenario]
        for policy in key_policies:
            g = sub[sub["policy_name"] == policy]
            if g.empty:
                continue
            live = g["episodes_detected_live"].sum() / g["episodes"].sum()
            delay = g["delay_live_sum_min"].sum() / max(g["episodes_detected_live"].sum(), 1)
            recall = g["tp"].sum() / (g["tp"].sum() + g["fn"].sum())
            lines.append(f"| {scenario} | {policy} | {g['communication_bytes'].mean():,.0f} | {live:.3f} | {delay:.1f} | {recall:.3f} | {g['backfill_bytes'].mean():,.0f} |")
    (args.stage_dir / "phase_a_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Written: {args.stage_dir / 'phase_a_report.md'}")
