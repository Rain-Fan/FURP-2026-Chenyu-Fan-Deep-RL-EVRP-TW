"""Train an EVRP-TW policy."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.main import train


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="experiments/configs/reinforce.yaml",
        help="Path to a REINFORCE or PPO YAML configuration.",
    )
    args = parser.parse_args()
    train(args.config)


if __name__ == "__main__":
    main()
