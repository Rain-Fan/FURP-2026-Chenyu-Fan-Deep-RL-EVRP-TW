#!/usr/bin/env python3
"""Smoke tests for all Week 6 generated figures."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

WEEK6_DIR = Path(__file__).resolve().parents[1]
if str(WEEK6_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK6_DIR))

from compare_week6_methods import run_experiment  # noqa: E402
from visualize_week6 import FIGURE_NAMES, generate_all  # noqa: E402


class VisualizationSmokeTests(unittest.TestCase):
    def test_all_figures_are_nonempty_png_files(self) -> None:
        bundle = run_experiment(
            scales=[20],
            profiles=["baseline"],
            instances_per_scale=1,
            base_seed=20260813,
            adaptive_steps=4,
            patience=2,
        )
        payload = {
            "metadata": bundle.metadata,
            "aggregate": list(bundle.aggregate),
            "comparisons": list(bundle.comparisons),
            "instances": [row.to_dict() for row in bundle.instances],
            "diagnostics": list(bundle.diagnostics),
            "adaptive_trace": list(bundle.adaptive_trace),
        }
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            generate_all(payload, output_dir)
            self.assertEqual({path.name for path in output_dir.iterdir()}, set(FIGURE_NAMES))
            for name in FIGURE_NAMES:
                path = output_dir / name
                self.assertGreater(path.stat().st_size, 5_000, name)
                self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
