#!/usr/bin/env python3
"""Tests for Week 6 experiment aggregation and serialization."""

from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

WEEK6_DIR = Path(__file__).resolve().parents[1]
if str(WEEK6_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK6_DIR))

from compare_week6_methods import (  # noqa: E402
    InstanceResult,
    aggregate_results,
    run_experiment,
    write_outputs,
)
from portfolio_solver import B_METHOD  # noqa: E402


class AggregationTests(unittest.TestCase):
    def test_aggregate_reports_feasible_statistics_and_runtime(self) -> None:
        rows = [
            InstanceResult(
                profile="baseline",
                method=B_METHOD,
                method_role="baseline",
                instance="i1",
                scale=20,
                seed=1,
                feasible=True,
                objective=100.0,
                runtime_sec=0.1,
                vehicles_used=2,
                violations=(),
                selected_source="nearest",
                initial_objective=110.0,
                accepted_moves=2,
                two_opt_moves=1,
                inter_route_moves=1,
                trace=(),
                routes=((0, 1, 0),),
                termination_reason="test",
                candidates=(),
            ),
            InstanceResult(
                profile="baseline",
                method=B_METHOD,
                method_role="baseline",
                instance="i2",
                scale=20,
                seed=2,
                feasible=False,
                objective=math.inf,
                runtime_sec=0.3,
                vehicles_used=3,
                violations=("unserved customers",),
                selected_source="nearest",
                initial_objective=math.inf,
                accepted_moves=0,
                two_opt_moves=0,
                inter_route_moves=0,
                trace=(),
                routes=((0, 0),),
                termination_reason="test",
                candidates=(),
            ),
        ]
        aggregate = aggregate_results(rows)
        self.assertEqual(len(aggregate), 1)
        summary = aggregate[0]
        self.assertEqual(summary["instances"], 2)
        self.assertEqual(summary["feasible_instances"], 1)
        self.assertEqual(summary["feasibility_rate"], 0.5)
        self.assertEqual(summary["mean_objective_feasible"], 100.0)
        self.assertEqual(summary["median_objective_feasible"], 100.0)
        self.assertEqual(summary["best_objective_feasible"], 100.0)
        self.assertEqual(summary["std_objective_feasible"], 0.0)
        self.assertAlmostEqual(summary["mean_runtime_sec"], 0.2)
        self.assertEqual(summary["total_accepted_moves"], 2)


class OutputSchemaTests(unittest.TestCase):
    def test_smoke_experiment_writes_complete_schema(self) -> None:
        bundle = run_experiment(
            scales=[20],
            profiles=["baseline"],
            instances_per_scale=1,
            base_seed=20260813,
            adaptive_steps=4,
            patience=2,
        )
        self.assertEqual(len(bundle.instances), 4)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            write_outputs(bundle, output_dir, command=["week6-smoke"])
            expected = {
                "week6_results.json",
                "week6_aggregate.csv",
                "week6_comparison.csv",
                "adaptive_trace.json",
                "adaptive_trace.csv",
                "week6_results.md",
                "run_log.txt",
            }
            self.assertEqual({path.name for path in output_dir.iterdir()}, expected)
            payload = json.loads((output_dir / "week6_results.json").read_text())
            self.assertEqual(
                set(payload),
                {
                    "metadata",
                    "aggregate",
                    "comparisons",
                    "instances",
                    "diagnostics",
                    "adaptive_trace",
                },
            )
            self.assertEqual(len(payload["instances"]), 4)
            self.assertTrue(payload["adaptive_trace"])


if __name__ == "__main__":
    unittest.main()
