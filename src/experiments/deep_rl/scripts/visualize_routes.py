"""Visualise a greedy or learned route."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.main import visualize


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="experiments/configs/baseline.yaml")
    parser.add_argument("--checkpoint")
    parser.add_argument("--output", default="figures/route_visualization.png")
    args = parser.parse_args()
    visualize(args.config, args.output, args.checkpoint)


if __name__ == "__main__":
    main()
