from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Thresholds:
    moderate_risk: float = 0.30
    high_risk: float = 0.60
    divergence_ratio_flag: float = 0.08
    divergence_ratio_high: float = 0.15


@dataclass(frozen=True)
class ObservationPolicy:
    basal_minutes: int = 60
    moderate_minutes: int = 15
    aggressive_minutes: int = 5
    fixed_long_minutes: int = 60
    fixed_short_minutes: int = 15
    # Must match `synthetic.NATIVE_INTERVAL_MINUTES`: this is the true
    # "dense monitoring" ceiling (one report per native tick). It was added
    # because, once the native data resolution was corrected from 15 to 5
    # minutes (see synthetic.py), `fixed_short` (15 min) stopped being
    # equivalent to dense monitoring and became an intermediate fixed-cadence
    # baseline in its own right.
    fixed_dense_minutes: int = 5


@dataclass(frozen=True)
class ExperimentConfig:
    payload_bytes_per_sample: int = 64
    prediction_threshold: float = 0.50


@dataclass(frozen=True)
class AppConfig:
    root_dir: Path
    raw_dir: Path
    processed_dir: Path
    outputs_dir: Path
    database_path: Path
    thresholds: Thresholds = Thresholds()
    policy: ObservationPolicy = ObservationPolicy()
    experiment: ExperimentConfig = ExperimentConfig()


DEFAULT_DEV_EUI = "0080e11550019bf1"


def build_config(root_dir: Path) -> AppConfig:
    return AppConfig(
        root_dir=root_dir,
        raw_dir=root_dir / "data" / "raw",
        processed_dir=root_dir / "data" / "processed",
        outputs_dir=root_dir / "outputs",
        database_path=root_dir / "outputs" / "fraud_dt.sqlite3",
    )
