#!/usr/bin/env python3
"""Integration tests for the Week 6 portfolio solver."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
for relative in (
    "src/experiments/week3",
    "src/experiments/week4",
    "src/experiments/week5",
    "src/experiments/week6",
):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from compare_week3_baselines import generate_instance  # noqa: E402
from compare_week4_methods import apply_profile, greedy_solve  # noqa: E402
from compare_week5_methods import (  # noqa: E402
    HYBRID_METHOD as WEEK5_D_METHOD,
    NEAREST_METHOD as WEEK5_B_METHOD,
    solve_method as solve_week5_method,
)
from portfolio_solver import (  # noqa: E402
    B_METHOD,
    D_METHOD,
    E_ADAPTIVE_METHOD,
    E_FIXED_METHOD,
    CandidateSolution,
    choose_best_candidate,
    solve_method,
    validate_routes,
)


def route_tuple(routes: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(route) for route in routes)


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instance = generate_instance(20, 20260813)
        self.routes, _ = greedy_solve(self.instance, WEEK5_B_METHOD)

    def test_existing_nearest_solution_is_independently_feasible(self) -> None:
        result = validate_routes(self.instance, self.routes)
        self.assertTrue(result.feasible, result.violations)
        self.assertTrue(math.isfinite(result.objective))

    def test_missing_customer_is_reported(self) -> None:
        broken = [list(route) for route in self.routes]
        customer = next(node for route in broken for node in route if node in self.instance.customer_ids)
        for route in broken:
            if customer in route:
                route.remove(customer)
                break
        result = validate_routes(self.instance, broken)
        self.assertFalse(result.feasible)
        self.assertTrue(any("unserved customers" in item for item in result.violations))

    def test_duplicate_customer_is_reported(self) -> None:
        broken = [list(route) for route in self.routes]
        customer = next(node for route in broken for node in route if node in self.instance.customer_ids)
        broken[0].insert(-1, customer)
        result = validate_routes(self.instance, broken)
        self.assertFalse(result.feasible)
        self.assertTrue(any("duplicate customers" in item for item in result.violations))

    def test_best_candidate_ignores_infeasible_shorter_candidate(self) -> None:
        feasible = CandidateSolution(
            source="nearest",
            routes=((0, 1, 0),),
            initial_objective=100.0,
            final_objective=90.0,
            feasible=True,
            violations=(),
        )
        infeasible = CandidateSolution(
            source="composite",
            routes=((0, 2, 0),),
            initial_objective=80.0,
            final_objective=70.0,
            feasible=False,
            violations=("unserved customers",),
        )
        self.assertIs(choose_best_candidate([infeasible, feasible]), feasible)


class CompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instance = generate_instance(20, 20260813)

    def test_method_b_matches_week5_routes_and_objective(self) -> None:
        expected_routes, *_ = solve_week5_method(self.instance, WEEK5_B_METHOD)
        result = solve_method(self.instance, B_METHOD)
        self.assertEqual(route_tuple(result.route_lists()), route_tuple(expected_routes))
        expected = validate_routes(self.instance, expected_routes).objective
        self.assertAlmostEqual(result.objective, expected)

    def test_method_d_matches_week5_routes_and_objective(self) -> None:
        expected_routes, *_ = solve_week5_method(self.instance, WEEK5_D_METHOD)
        result = solve_method(self.instance, D_METHOD)
        self.assertEqual(route_tuple(result.route_lists()), route_tuple(expected_routes))
        expected = validate_routes(self.instance, expected_routes).objective
        self.assertAlmostEqual(result.objective, expected)


class PortfolioMethodTests(unittest.TestCase):
    def test_all_methods_preserve_feasibility_when_reported_feasible(self) -> None:
        for profile in ("baseline", "small_battery"):
            instance = apply_profile(generate_instance(20, 20260813), profile)
            for method in (B_METHOD, D_METHOD, E_FIXED_METHOD, E_ADAPTIVE_METHOD):
                with self.subTest(profile=profile, method=method):
                    result = solve_method(instance, method, adaptive_steps=6, patience=3)
                    if result.feasible:
                        validation = validate_routes(instance, result.route_lists())
                        self.assertTrue(validation.feasible, validation.violations)

    def test_fixed_inputs_reproduce_routes_and_adaptive_trace(self) -> None:
        instance = apply_profile(generate_instance(20, 20260814), "tight_tw")
        for method in (B_METHOD, D_METHOD, E_FIXED_METHOD, E_ADAPTIVE_METHOD):
            with self.subTest(method=method):
                first = solve_method(instance, method, adaptive_steps=6, patience=3)
                second = solve_method(instance, method, adaptive_steps=6, patience=3)
                self.assertEqual(first.routes, second.routes)
                self.assertAlmostEqual(first.objective, second.objective)
                self.assertEqual(first.selected_source, second.selected_source)
                self.assertEqual(first.action_sequence, second.action_sequence)
                self.assertEqual(first.termination_reason, second.termination_reason)


if __name__ == "__main__":
    unittest.main()
