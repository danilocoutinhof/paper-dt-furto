from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.schemas import Scenario
from fraud_dt.synthetic import generate_synthetic_dataset
from fraud_dt.pipeline import run_pipeline


def test_end_to_end_pipeline(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    out_dir = tmp_path / "outputs"
    generate_synthetic_dataset(raw_dir, days=2, scenario=Scenario.INTERMITTENT_EVENING, seed=7)
    outputs = run_pipeline(tmp_path, raw_dir, out_dir)

    assert outputs["merged"].exists()
    assert outputs["scored"].exists()
    assert outputs["supervised"].exists()
    assert outputs["policy"].exists()
    assert outputs["comparison"].exists()
    assert outputs["model_metrics"].exists()
    assert outputs["decisions"].exists()
    assert outputs["state_history"].exists()
    assert outputs["command_plan"].exists()
    assert outputs["transport_delivery"].exists()
    assert outputs["fusion_comparison"].exists()
    assert outputs["summary"].exists()
