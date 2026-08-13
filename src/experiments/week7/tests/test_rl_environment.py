#!/usr/bin/env python3
"""Behavior tests for the Week 7 operator-selection MDP."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

WEEK7_DIR = Path(__file__).resolve().parents[1]
ROOT = WEEK7_DIR.parents[2]
for path in (
    WEEK7_DIR,
    ROOT / "src" / "experiments" / "week3",
    ROOT / "src" / "experiments" / "week4",
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from compare_week3_baselines import generate_instance  # noqa: E402
from compare_week4_methods import apply_profile  # noqa: E402
from rl_environment import ACTIONS, OperatorSelectionEnv, build_warm_start  # noqa: E402


class OperatorSelectionEnvironmentTests(unittest.TestCase):
    @staticmethod
    def make_env(*, patience: int = 4) -> OperatorSelectionEnv:
        instance = apply_profile(generate_instance(20, 31020001), "baseline")
        warm = build_warm_start(instance, "nearest")
        if warm is None:
            raise AssertionError("fixture construction unexpectedly infeasible")
        return OperatorSelectionEnv(
            instance,
            warm.routes,
            "nearest",
            max_steps=12,
            patience=patience,
        )

    def test_reset_returns_finite_twelve_value_state(self) -> None:
        state = self.make_env().reset()
        self.assertEqual(state.shape, (12,))
        self.assertTrue(np.isfinite(state).all())
        np.testing.assert_allclose(state[8:11], np.zeros(3))
        self.assertEqual(float(state[11]), 0.0)

    def test_invalid_action_index_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "action index"):
            self.make_env().step(len(ACTIONS))

    def test_one_step_records_real_operator_transition(self) -> None:
        env = self.make_env()
        transition = env.step(1)
        self.assertEqual(transition.action, "relocate")
        self.assertEqual(transition.action_index, 1)
        self.assertEqual(transition.next_state.shape, (12,))
        self.assertTrue(np.isfinite(transition.reward))
        self.assertTrue(env.validation.feasible)
        self.assertLessEqual(env.objective, env.warm_start_objective + 1e-9)

    def test_patience_one_terminates_after_non_improving_two_opt(self) -> None:
        env = self.make_env(patience=1)
        transition = env.step(0)
        self.assertFalse(transition.accepted)
        self.assertEqual(transition.reward, -0.001)
        self.assertTrue(transition.done)
        self.assertEqual(transition.termination_reason, "patience")


if __name__ == "__main__":
    unittest.main()
