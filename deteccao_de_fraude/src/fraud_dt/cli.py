from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline
from .schemas import Scenario
from .synthetic import generate_synthetic_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Digital twin prototype CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    synth = subparsers.add_parser("generate-synthetic", help="Generate synthetic datasets")
    synth.add_argument("--output-dir", type=Path, required=True)
    synth.add_argument("--days", type=int, default=7)
    synth.add_argument("--scenario", type=str, default=Scenario.INTERMITTENT_EVENING.value)
    synth.add_argument("--seed", type=int, default=42)

    run = subparsers.add_parser("run-pipeline", help="Run the feature, risk and policy pipeline")
    run.add_argument("--project-root", type=Path, required=True)
    run.add_argument("--input-dir", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)

    args = parser.parse_args()

    if args.command == "generate-synthetic":
        generate_synthetic_dataset(
            output_dir=args.output_dir,
            days=args.days,
            scenario=Scenario(args.scenario),
            seed=args.seed,
        )
        return

    if args.command == "run-pipeline":
        run_pipeline(args.project_root, args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
