"""Evaluate the greedy baseline and an optional trained policy."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.main import evaluate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="experiments/configs/baseline.yaml")
    parser.add_argument("--checkpoint")
    args = parser.parse_args()
    evaluate(args.config, args.checkpoint)


if __name__ == "__main__":
    main()
