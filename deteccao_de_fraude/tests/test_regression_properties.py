from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.schemas import Scenario
from fraud_dt.synthetic import generate_synthetic_dataset
from fraud_dt.pipeline import run_pipeline
import pandas as pd


def test_adaptive_fusion_regression_properties(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    out_dir = tmp_path / "outputs"
    generate_synthetic_dataset(raw_dir, days=3, scenario=Scenario.INTERMITTENT_EVENING, seed=9)
    outputs = run_pipeline(tmp_path, raw_dir, out_dir)

    fusion_df = pd.read_csv(outputs["fusion_comparison"])
    weighted = fusion_df.loc[fusion_df["fusion_strategy"] == "weighted"].iloc[0]
    conservative = fusion_df.loc[fusion_df["fusion_strategy"] == "conservative_max"].iloc[0]

    assert weighted["communication_bytes"] <= conservative["communication_bytes"]
    assert weighted["f1"] >= 0.5
