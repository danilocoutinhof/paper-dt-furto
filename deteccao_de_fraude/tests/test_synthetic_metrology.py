from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
import sys
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.schemas import Scenario
from fraud_dt.synthetic import generate_synthetic_dataset


def test_synthetic_metrology_consistency(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    paths = generate_synthetic_dataset(raw_dir, days=2, scenario=Scenario.INTERMITTENT_EVENING, seed=21)

    forensic_df = pd.read_csv(paths["forensic"])
    billing_df = pd.read_csv(paths["billing"])

    forensic_triangle_error = (forensic_df["apparent_power"] ** 2 - (forensic_df["active_power"] ** 2 + forensic_df["reactive_power"] ** 2)).abs()
    billing_triangle_error = (billing_df["billing_apparent_power"] ** 2 - (billing_df["billing_active_power"] ** 2 + billing_df["billing_reactive_power"] ** 2)).abs()

    forensic_current_error = (forensic_df["apparent_power"] / forensic_df["voltage_rms"] - forensic_df["current_rms"]).abs()
    billing_current_error = (billing_df["billing_apparent_power"] / billing_df["billing_voltage_rms"] - billing_df["billing_current_rms"]).abs()

    assert forensic_triangle_error.max() < 5.0
    assert billing_triangle_error.max() < 5.0
    assert forensic_current_error.max() < 0.001
    assert billing_current_error.max() < 0.001

    assert (forensic_df["active_energy"].diff().fillna(0.0) >= -1e-9).all()
    assert (forensic_df["reactive_energy"].diff().fillna(0.0) >= -1e-9).all()
    assert (billing_df["billing_active_energy"].diff().fillna(0.0) >= -1e-9).all()
    assert (billing_df["billing_reactive_energy"].diff().fillna(0.0) >= -1e-9).all()
