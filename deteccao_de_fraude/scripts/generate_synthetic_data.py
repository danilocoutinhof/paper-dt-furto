from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.schemas import Scenario
from fraud_dt.synthetic import generate_synthetic_dataset


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic forensic telemetry datasets")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--scenario", type=str, default=Scenario.INTERMITTENT_EVENING.value)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    generate_synthetic_dataset(
        output_dir=args.output_dir,
        days=args.days,
        scenario=Scenario(args.scenario),
        seed=args.seed,
    )
