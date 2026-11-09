from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fraud_dt.pipeline import run_pipeline


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the digital twin prototype pipeline")
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()

    run_pipeline(ROOT, args.input_dir, args.output_dir)
