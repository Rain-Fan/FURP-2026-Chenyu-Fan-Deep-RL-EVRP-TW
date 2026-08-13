#!/usr/bin/env python3
"""Smoke tests for every generated Week 7 PNG."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

WEEK7_DIR = Path(__file__).resolve().parents[1]
if str(WEEK7_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK7_DIR))

from train_week7_rl import TrainingConfig, run_experiment, write_outputs  # noqa: E402
from visualize_week7 import FIGURE_NAMES, generate_all  # noqa: E402


class Week7VisualizationTests(unittest.TestCase):
    def test_all_figures_are_nonempty_png_files(self) -> None:
        config = TrainingConfig(
            scales=(20,), profiles=("baseline",),
            train_instances=1, eval_instances=1,
            train_seed=801, eval_seed=901,
            epochs=1, max_steps=3, patience=2,
            hidden_dim=8, batch_size=2, replay_capacity=50,
            target_sync=5, agent_seed=19,
        )
        bundle, agent = run_experiment(config)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            figure_dir = root / "figures"
            write_outputs(bundle, agent, data_dir, command=["week7-figure-test"])
            payload = json.loads((data_dir / "week7_results.json").read_text())
            generate_all(payload, figure_dir)
            self.assertEqual({path.name for path in figure_dir.iterdir()}, set(FIGURE_NAMES))
            for name in FIGURE_NAMES:
                path = figure_dir / name
                self.assertGreater(path.stat().st_size, 5_000, name)
                self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
