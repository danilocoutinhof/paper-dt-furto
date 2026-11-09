from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.reporting import build_campaign_manifest, build_run_manifest, export_campaign_tables_to_tex
from fraud_dt.config import build_config
import pandas as pd


def test_run_manifest_contains_environment_and_config(tmp_path: Path) -> None:
    config = build_config(tmp_path)
    manifest = build_run_manifest(
        project_root=tmp_path,
        input_dir=tmp_path / "raw",
        output_dir=tmp_path / "outputs",
        config=config,
        extra={"samples": 10},
    )
    assert manifest["kind"] == "single_run"
    assert manifest["environment"]["python_version"]
    assert manifest["config"]["policy"]["basal_minutes"] == 60


def test_export_campaign_tables_to_tex_writes_nonempty_file(tmp_path: Path) -> None:
    policy_df = pd.DataFrame([
        {"policy_name": "adaptive", "probability_source": "decision_probability", "fusion_strategy": "weighted", "f1": 0.63, "recall": 0.61, "communication_bytes": 18752.0},
    ])
    fusion_df = pd.DataFrame([
        {"fusion_strategy": "weighted", "f1": 0.63, "recall": 0.61, "communication_bytes": 18752.0},
    ])
    out = tmp_path / "tables.tex"
    export_campaign_tables_to_tex(policy_df, fusion_df, out)
    content = out.read_text(encoding="utf-8")
    assert "Aggregate comparison between observation policies" in content
    assert "weighted" in content
