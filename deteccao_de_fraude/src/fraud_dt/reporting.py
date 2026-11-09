from __future__ import annotations

import json
import platform
from dataclasses import asdict, is_dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pandas as pd


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {k: _serialize(v) for k, v in asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    return value


def build_environment_manifest() -> dict[str, Any]:
    packages = {}
    for package_name in ["numpy", "pandas", "scikit-learn", "matplotlib", "pytest"]:
        try:
            packages[package_name] = version(package_name)
        except Exception:
            packages[package_name] = "unavailable"
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "packages": packages,
    }


def write_json_manifest(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_serialize(payload), indent=2), encoding="utf-8")
    return path


def build_run_manifest(project_root: Path, input_dir: Path, output_dir: Path, config: Any, extra: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "single_run",
        "project_root": project_root,
        "input_dir": input_dir,
        "output_dir": output_dir,
        "config": _serialize(config),
        "environment": build_environment_manifest(),
        "extra": extra,
    }


def build_campaign_manifest(project_root: Path, output_dir: Path, extra: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "campaign",
        "project_root": project_root,
        "output_dir": output_dir,
        "environment": build_environment_manifest(),
        "extra": extra,
    }


def export_campaign_tables_to_tex(policy_df: pd.DataFrame, fusion_df: pd.DataFrame, output_path: Path) -> Path:
    newline = r"\\"
    lines = [
        "% Auto-generated table file for the article",
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Aggregate comparison between observation policies.}",
        r"\begin{tabular}{llrrrr}",
        r"\hline",
        f"Policy & Probability & Fusion & F1 & Recall & Bytes {newline}",
        r"\hline",
    ]
    for _, row in policy_df.iterrows():
        lines.append(
            f"{row['policy_name']} & {row['probability_source']} & {row['fusion_strategy']} & "
            f"{row['f1']:.4f} & {row['recall']:.4f} & {row['communication_bytes']:.1f} {newline}"
        )
    lines.extend([
        r"\hline",
        r"\end{tabular}",
        r"\end{table}",
        "",
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Aggregate comparison between adaptive fusion strategies.}",
        r"\begin{tabular}{lrrr}",
        r"\hline",
        f"Fusion & F1 & Recall & Bytes {newline}",
        r"\hline",
    ])
    for _, row in fusion_df.iterrows():
        lines.append(
            f"{row['fusion_strategy']} & {row['f1']:.4f} & {row['recall']:.4f} & {row['communication_bytes']:.1f} {newline}"
        )
    lines.extend([
        r"\hline",
        r"\end{tabular}",
        r"\end{table}",
    ])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path

