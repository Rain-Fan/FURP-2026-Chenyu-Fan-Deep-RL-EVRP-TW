#!/usr/bin/env python3
"""Tests for the Week 6 adaptive operator-selection core."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

WEEK6_DIR = Path(__file__).resolve().parents[1]
if str(WEEK6_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK6_DIR))

from adaptive_selector import (  # noqa: E402
    ActionOutcome,
    UCB1Policy,
    adaptive_search,
    normalized_reward,
)


class RewardTests(unittest.TestCase):
    def test_relative_improvement_is_normalized_by_starting_objective(self) -> None:
        self.assertAlmostEqual(normalized_reward(100.0, 90.0, True), 0.1)

    def test_infeasible_transition_has_fixed_negative_reward(self) -> None:
        self.assertEqual(normalized_reward(100.0, 80.0, False), -1.0)

    def test_invalid_objectives_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalized_reward(0.0, 0.0, True)
        with self.assertRaises(ValueError):
            normalized_reward(math.inf, 1.0, True)


class UCB1PolicyTests(unittest.TestCase):
    def test_untried_actions_are_selected_in_declared_order(self) -> None:
        policy = UCB1Policy(("two_opt", "relocate", "swap"), 0.7)
        selected = [policy.select(), policy.select(), policy.select()]
        self.assertEqual(selected, ["two_opt", "relocate", "swap"])

    def test_equal_scores_use_declared_order(self) -> None:
        policy = UCB1Policy(("two_opt", "relocate"), 0.0)
        for action in ("two_opt", "relocate"):
            self.assertEqual(policy.select(), action)
            policy.update(action, 0.25)
        self.assertEqual(policy.select(), "two_opt")

    def test_update_requires_a_reserved_selection(self) -> None:
        policy = UCB1Policy(("swap",), 0.7)
        with self.assertRaises(ValueError):
            policy.update("swap", 0.1)


class AdaptiveSearchTests(unittest.TestCase):
    def test_infeasible_candidate_is_rejected_and_patience_stops_search(self) -> None:
        actions = {
            "bad": lambda value: ActionOutcome(
                solution=value - 5.0,
                moves=1,
                feasible=False,
                runtime_sec=0.01,
            )
        }
        result = adaptive_search(
            100.0,
            actions,
            float,
            lambda value: value >= 100.0,
            max_steps=3,
            patience=1,
        )
        self.assertEqual(result.solution, 100.0)
        self.assertEqual(result.termination_reason, "patience")
        self.assertEqual(len(result.trace), 1)
        self.assertFalse(result.trace[0].accepted)
        self.assertEqual(result.trace[0].reward, -1.0)

    def test_improving_actions_run_until_budget(self) -> None:
        actions = {
            "step": lambda value: ActionOutcome(
                solution=value - 1.0,
                moves=1,
                feasible=True,
                runtime_sec=0.01,
            )
        }
        result = adaptive_search(
            10.0,
            actions,
            float,
            lambda value: value > 0.0,
            max_steps=3,
            patience=4,
        )
        self.assertEqual(result.solution, 7.0)
        self.assertEqual(len(result.trace), 3)
        self.assertEqual(result.termination_reason, "budget")
        self.assertTrue(all(record.accepted for record in result.trace))

    def test_context_is_copied_into_every_trace_record(self) -> None:
        result = adaptive_search(
            10.0,
            {"idle": lambda value: ActionOutcome(value, 0, True, 0.0)},
            float,
            lambda _value: True,
            max_steps=1,
            patience=1,
            context={"profile": "baseline", "scale": 20},
        )
        self.assertEqual(result.trace[0].context["profile"], "baseline")
        self.assertEqual(result.trace[0].context["scale"], 20)


if __name__ == "__main__":
    unittest.main()
