#!/usr/bin/env python3
"""Tests for Week 6 deterministic reproducibility checks."""

from __future__ import annotations

import sys
import unittest
import importlib.util
from dataclasses import replace
from pathlib import Path

WEEK6_DIR = Path(__file__).resolve().parents[1]
if str(WEEK6_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK6_DIR))

from portfolio_solver import E_ADAPTIVE_METHOD, solve_method  # noqa: E402
spec = importlib.util.spec_from_file_location(
    "week6_reproducibility_check", WEEK6_DIR / "reproducibility_check.py"
)
assert spec is not None and spec.loader is not None
week6_reproducibility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(week6_reproducibility)
run_checks = week6_reproducibility.run_checks
solution_signature = week6_reproducibility.solution_signature

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src/experiments/week3"))
sys.path.insert(0, str(ROOT / "src/experiments/week4"))
from compare_week3_baselines import generate_instance  # noqa: E402
from compare_week4_methods import apply_profile  # noqa: E402


class SignatureTests(unittest.TestCase):
    def test_same_result_has_same_signature(self) -> None:
        instance = apply_profile(generate_instance(20, 20260813), "baseline")
        result = solve_method(instance, E_ADAPTIVE_METHOD, adaptive_steps=4, patience=2)
        self.assertEqual(solution_signature(result), solution_signature(result))

    def test_changed_action_changes_signature(self) -> None:
        instance = apply_profile(generate_instance(20, 20260813), "baseline")
        result = solve_method(instance, E_ADAPTIVE_METHOD, adaptive_steps=4, patience=2)
        trace = list(result.trace)
        self.assertTrue(trace)
        trace[0] = replace(trace[0], action="changed_action")
        changed = replace(result, trace=tuple(trace))
        self.assertNotEqual(solution_signature(result), solution_signature(changed))


class CheckMatrixTests(unittest.TestCase):
    def test_two_repeats_match_for_all_methods(self) -> None:
        report = run_checks(
            scales=[20],
            profiles=["baseline"],
            instances_per_scale=1,
            repeats=2,
            base_seed=20260813,
            adaptive_steps=4,
            patience=2,
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["checks"], 4)
        self.assertEqual(report["mismatches"], [])


if __name__ == "__main__":
    unittest.main()
