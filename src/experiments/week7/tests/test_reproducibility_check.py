#!/usr/bin/env python3
"""Reproducibility tests for Week 7 training and greedy evaluation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

WEEK7_DIR = Path(__file__).resolve().parents[1]
if str(WEEK7_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK7_DIR))

from reproducibility_check import run_reproducibility_check  # noqa: E402
from train_week7_rl import TrainingConfig  # noqa: E402


class ReproducibilityTests(unittest.TestCase):
    def test_two_fixed_training_and_evaluation_runs_have_identical_signatures(self) -> None:
        config = TrainingConfig(
            scales=(20,), profiles=("baseline",),
            train_instances=1, eval_instances=1,
            train_seed=501, eval_seed=701,
            epochs=1, max_steps=3, patience=2,
            hidden_dim=8, batch_size=2, replay_capacity=50,
            target_sync=5, agent_seed=17,
        )
        report = run_reproducibility_check(config, repeats=2)
        self.assertEqual(report["mismatch_count"], 0)
        self.assertEqual(report["checks"], 2)
        self.assertEqual(len(set(report["model_hashes"])), 1)


if __name__ == "__main__":
    unittest.main()
