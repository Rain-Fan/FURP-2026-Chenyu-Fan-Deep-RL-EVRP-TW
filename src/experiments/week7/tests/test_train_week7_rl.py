#!/usr/bin/env python3
"""Integration and output-contract tests for the Week 7 experiment runner."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

WEEK7_DIR = Path(__file__).resolve().parents[1]
if str(WEEK7_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK7_DIR))

from train_week7_rl import METHODS, TrainingConfig, run_experiment, write_outputs  # noqa: E402


class Week7ExperimentTests(unittest.TestCase):
    @staticmethod
    def smoke_config(**overrides) -> TrainingConfig:
        values = {
            "scales": (20,),
            "profiles": ("baseline",),
            "train_instances": 1,
            "eval_instances": 1,
            "train_seed": 100,
            "eval_seed": 200,
            "epochs": 1,
            "max_steps": 3,
            "patience": 2,
            "hidden_dim": 8,
            "batch_size": 2,
            "replay_capacity": 50,
            "learning_rate": 0.001,
            "gamma": 0.95,
            "target_sync": 5,
            "agent_seed": 7,
        }
        values.update(overrides)
        return TrainingConfig(**values)

    def test_smoke_run_has_disjoint_splits_and_all_methods(self) -> None:
        bundle, _agent = run_experiment(self.smoke_config())
        self.assertEqual(bundle.metadata["seed_overlap"], [])
        self.assertEqual(len(bundle.instances), 4)
        self.assertEqual({row.method for row in bundle.instances}, set(METHODS))
        self.assertEqual(len(bundle.aggregate), 4)
        self.assertGreater(len(bundle.training_history), 0)
        self.assertTrue(all(row.independent_validation for row in bundle.instances))

    def test_overlapping_seed_namespaces_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "overlap"):
            run_experiment(self.smoke_config(eval_seed=100))

    def test_outputs_include_model_tables_trace_and_split_audit(self) -> None:
        bundle, agent = run_experiment(self.smoke_config())
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            write_outputs(bundle, agent, output_dir, command=["week7-smoke"])
            expected = {
                "week7_results.json",
                "week7_aggregate.csv",
                "week7_comparison.csv",
                "week7_instances.csv",
                "week7_training_history.csv",
                "week7_results.md",
                "dqn_checkpoint.npz",
                "dqn_checkpoint_manifest.json",
                "run_log.txt",
            }
            self.assertTrue(expected.issubset({path.name for path in output_dir.iterdir()}))
            payload = json.loads((output_dir / "week7_results.json").read_text())
            self.assertEqual(payload["metadata"]["seed_overlap"], [])
            self.assertEqual(len(payload["instances"]), 4)
            self.assertGreater(len(payload["action_trace"]), 0)
            self.assertGreater((output_dir / "dqn_checkpoint.npz").stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
