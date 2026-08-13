#!/usr/bin/env python3
"""Regression tests for the consolidated Week 6 result visualizations."""

from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import generate_research_visualizations as visualizations


class Week6ResearchVisualizationTests(unittest.TestCase):
    def test_main_generates_week6_figures_from_the_local_experiment_bundle(self) -> None:
        with tempfile.TemporaryDirectory(dir=visualizations.ROOT) as tmp:
            original_out_dir = visualizations.OUT_DIR
            visualizations.OUT_DIR = Path(tmp)
            try:
                with redirect_stdout(StringIO()):
                    visualizations.main()
            finally:
                visualizations.OUT_DIR = original_out_dir

            output_dir = Path(tmp)
            performance = output_dir / "week6_performance_summary.svg"
            operators = output_dir / "week6_adaptive_operator_summary.svg"
            routes = output_dir / "week6_representative_routes.svg"

            self.assertTrue(performance.is_file())
            self.assertTrue(operators.is_file())
            self.assertTrue(routes.is_file())

            performance_svg = performance.read_text(encoding="utf-8")
            self.assertIn("405.32", performance_svg)
            self.assertIn("946.28", performance_svg)

            operator_svg = operators.read_text(encoding="utf-8")
            self.assertIn("relocate", operator_svg)
            self.assertIn("809", operator_svg)
            self.assertIn("0.02141", operator_svg)

            route_svg = routes.read_text(encoding="utf-8")
            self.assertIn("seed=20310813", route_svg)
            self.assertIn("objective=651.4", route_svg)

            index = (output_dir / "research_visualizations.md").read_text(encoding="utf-8")
            self.assertIn("week6_performance_summary.svg", index)
            self.assertIn("Week 6 headline deltas", index)


if __name__ == "__main__":
    unittest.main()
