#!/usr/bin/env python3
"""Week 6 portfolio solver combining construction and improvement methods."""

from __future__ import annotations

import math
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for relative in (
    "src/experiments/week3",
    "src/experiments/week4",
    "src/experiments/week5",
):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from adaptive_selector import ActionOutcome, TraceRecord, adaptive_search  # noqa: E402
from compare_week3_baselines import Instance, route_distance  # noqa: E402
from compare_week4_methods import (  # noqa: E402
    COMPOSITE_METHOD,
    NEAREST_METHOD,
    apply_two_opt,
    check_single_route,
    greedy_solve,
)
from compare_week5_methods import (  # noqa: E402
    HYBRID_METHOD,
    solve_method as solve_week5_method,
)
from inter_route_moves import (  # noqa: E402
    inter_route_optimize,
    relocate_pass,
    swap_pass,
)

B_METHOD = "B_nearest_customer"
D_METHOD = "D_composite_inter_route"
E_FIXED_METHOD = "E_fixed_portfolio"
E_ADAPTIVE_METHOD = "E_adaptive_portfolio"

METHODS = {
    B_METHOD: {
        "role": "baseline",
        "description": "Nearest-customer greedy construction (Week 3 baseline B).",
    },
    D_METHOD: {
        "role": "week5_reference",
        "description": "Composite construction + 2-opt + fixed relocate/swap (Week 5 D).",
    },
    E_FIXED_METHOD: {
        "role": "portfolio_ablation",
        "description": "Nearest/composite portfolio with fixed local-search order.",
    },
    E_ADAPTIVE_METHOD: {
        "role": "tested_method",
        "description": "Nearest/composite portfolio with deterministic UCB1 operator selection.",
    },
}

SOURCE_METHODS = (
    ("nearest", NEAREST_METHOD),
    ("composite", COMPOSITE_METHOD),
)


def _route_tuple(routes: list[list[int]] | tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(route) for route in routes)


def _route_lists(routes: tuple[tuple[int, ...], ...] | list[list[int]]) -> list[list[int]]:
    return [list(route) for route in routes]


def raw_solution_distance(instance: Instance, routes: list[list[int]] | tuple[tuple[int, ...], ...]) -> float:
    try:
        return sum(route_distance(instance, list(route)) for route in routes)
    except (IndexError, KeyError):
        return math.inf


@dataclass(frozen=True)
class ValidationResult:
    feasible: bool
    objective: float
    violations: tuple[str, ...]
    vehicles_used: int
    served_customers: int


def validate_routes(
    instance: Instance,
    routes: list[list[int]] | tuple[tuple[int, ...], ...],
) -> ValidationResult:
    """Independently validate route structure, coverage, and EVRP-TW rules."""

    route_lists = _route_lists(routes)
    violations: list[str] = []
    if len(route_lists) > instance.max_vehicles:
        violations.append(
            f"fleet limit exceeded: {len(route_lists)} > {instance.max_vehicles}"
        )

    customer_visits: list[int] = []
    for route_index, route in enumerate(route_lists):
        if not route or route[0] != instance.depot.idx or route[-1] != instance.depot.idx:
            violations.append(f"route {route_index} is not depot anchored")
        invalid_nodes = [node for node in route if node < 0 or node >= len(instance.nodes)]
        if invalid_nodes:
            violations.append(f"route {route_index} contains unknown nodes: {invalid_nodes[:5]}")
            continue
        customer_visits.extend(node for node in route if node in instance.customer_ids)
        route_ok, _distance = check_single_route(instance, route)
        if not route_ok:
            violations.append(
                f"route {route_index} violates capacity, time-window, battery, or depot constraints"
            )

    counts = Counter(customer_visits)
    duplicates = sorted(node for node, count in counts.items() if count > 1)
    unserved = sorted(instance.customer_ids - set(customer_visits))
    if duplicates:
        violations.append(f"duplicate customers: {duplicates[:20]}")
    if unserved:
        violations.append(f"unserved customers: {unserved[:20]}")

    objective = raw_solution_distance(instance, route_lists)
    feasible = not violations and math.isfinite(objective)
    return ValidationResult(
        feasible=feasible,
        objective=objective if feasible else math.inf,
        violations=tuple(violations),
        vehicles_used=len(route_lists),
        served_customers=len(set(customer_visits)),
    )


@dataclass(frozen=True)
class CandidateSolution:
    source: str
    routes: tuple[tuple[int, ...], ...]
    initial_objective: float
    final_objective: float
    feasible: bool
    violations: tuple[str, ...]
    two_opt_moves: int = 0
    inter_route_moves: int = 0
    accepted_moves: int = 0
    runtime_sec: float = 0.0
    trace: tuple[TraceRecord, ...] = ()
    termination_reason: str = "not_started"

    def route_lists(self) -> list[list[int]]:
        return _route_lists(self.routes)

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["routes"] = self.route_lists()
        data["trace"] = [record.to_dict() for record in self.trace]
        return data


def choose_best_candidate(candidates: list[CandidateSolution]) -> CandidateSolution:
    if not candidates:
        raise ValueError("at least one candidate is required")
    feasible = [candidate for candidate in candidates if candidate.feasible]
    if feasible:
        return min(feasible, key=lambda candidate: (candidate.final_objective, candidate.source))
    return min(candidates, key=lambda candidate: (len(candidate.violations), candidate.source))


@dataclass(frozen=True)
class SolveResult:
    method: str
    routes: tuple[tuple[int, ...], ...]
    feasible: bool
    objective: float
    violations: tuple[str, ...]
    selected_source: str
    initial_objective: float
    runtime_sec: float
    two_opt_moves: int
    inter_route_moves: int
    accepted_moves: int
    trace: tuple[TraceRecord, ...] = ()
    termination_reason: str = "not_applicable"
    candidates: tuple[CandidateSolution, ...] = ()

    @property
    def action_sequence(self) -> tuple[str, ...]:
        return tuple(record.action for record in self.trace)

    def route_lists(self) -> list[list[int]]:
        return _route_lists(self.routes)

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "routes": self.route_lists(),
            "feasible": self.feasible,
            "objective": self.objective if self.feasible else None,
            "violations": list(self.violations),
            "selected_source": self.selected_source,
            "initial_objective": self.initial_objective if math.isfinite(self.initial_objective) else None,
            "runtime_sec": self.runtime_sec,
            "two_opt_moves": self.two_opt_moves,
            "inter_route_moves": self.inter_route_moves,
            "accepted_moves": self.accepted_moves,
            "trace": [record.to_dict() for record in self.trace],
            "termination_reason": self.termination_reason,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


def _candidate_from_routes(
    instance: Instance,
    source: str,
    routes: list[list[int]],
    *,
    started: float,
    initial_objective: float | None = None,
    two_opt_moves: int = 0,
    inter_route_moves: int = 0,
    accepted_moves: int = 0,
    trace: tuple[TraceRecord, ...] = (),
    termination_reason: str = "not_applicable",
) -> CandidateSolution:
    validation = validate_routes(instance, routes)
    raw_initial = raw_solution_distance(instance, routes) if initial_objective is None else initial_objective
    return CandidateSolution(
        source=source,
        routes=_route_tuple(routes),
        initial_objective=raw_initial if math.isfinite(raw_initial) else math.inf,
        final_objective=validation.objective,
        feasible=validation.feasible,
        violations=validation.violations,
        two_opt_moves=two_opt_moves,
        inter_route_moves=inter_route_moves,
        accepted_moves=accepted_moves,
        runtime_sec=time.perf_counter() - started,
        trace=trace,
        termination_reason=termination_reason,
    )


def _operator_actions(instance: Instance):
    checker = lambda route: check_single_route(instance, route)  # noqa: E731

    def two_opt_action(routes: tuple[tuple[int, ...], ...]) -> ActionOutcome:
        started = time.perf_counter()
        improved, moves, _gain = apply_two_opt(instance, _route_lists(routes))
        validation = validate_routes(instance, improved)
        return ActionOutcome(_route_tuple(improved), moves, validation.feasible, time.perf_counter() - started)

    def relocate_action(routes: tuple[tuple[int, ...], ...]) -> ActionOutcome:
        started = time.perf_counter()
        improved, moves = relocate_pass(
            _route_lists(routes), instance.customer_ids, checker
        )
        validation = validate_routes(instance, improved)
        return ActionOutcome(_route_tuple(improved), moves, validation.feasible, time.perf_counter() - started)

    def swap_action(routes: tuple[tuple[int, ...], ...]) -> ActionOutcome:
        started = time.perf_counter()
        improved, moves = swap_pass(_route_lists(routes), instance.customer_ids, checker)
        validation = validate_routes(instance, improved)
        return ActionOutcome(_route_tuple(improved), moves, validation.feasible, time.perf_counter() - started)

    return {
        "two_opt": two_opt_action,
        "relocate": relocate_action,
        "swap": swap_action,
    }


def _build_portfolio_candidate(
    instance: Instance,
    source: str,
    construction_method: str,
    mode: str,
    adaptive_steps: int,
    patience: int,
) -> CandidateSolution:
    started = time.perf_counter()
    routes, construction_violations = greedy_solve(instance, construction_method)
    initial_validation = validate_routes(instance, routes)
    initial_objective = raw_solution_distance(instance, routes)
    if construction_violations or not initial_validation.feasible:
        violations = tuple(dict.fromkeys([*construction_violations, *initial_validation.violations]))
        return CandidateSolution(
            source=source,
            routes=_route_tuple(routes),
            initial_objective=math.inf,
            final_objective=math.inf,
            feasible=False,
            violations=violations,
            runtime_sec=time.perf_counter() - started,
            termination_reason="infeasible_construction",
        )

    warmed, two_opt_moves, _gain = apply_two_opt(instance, routes)
    warm_validation = validate_routes(instance, warmed)
    if not warm_validation.feasible:
        return _candidate_from_routes(
            instance,
            source,
            warmed,
            started=started,
            initial_objective=initial_objective,
            two_opt_moves=two_opt_moves,
            termination_reason="infeasible_warm_start",
        )

    if mode == "fixed":
        checker = lambda route: check_single_route(instance, route)  # noqa: E731
        improved, inter_moves = inter_route_optimize(
            warmed, instance.customer_ids, checker
        )
        return _candidate_from_routes(
            instance,
            source,
            improved,
            started=started,
            initial_objective=initial_objective,
            two_opt_moves=two_opt_moves,
            inter_route_moves=inter_moves,
            accepted_moves=two_opt_moves + inter_moves,
            termination_reason="fixed_schedule",
        )

    if mode != "adaptive":
        raise ValueError(f"unknown portfolio mode: {mode}")
    initial_tuple = _route_tuple(warmed)
    search = adaptive_search(
        initial_tuple,
        _operator_actions(instance),
        lambda candidate: raw_solution_distance(instance, candidate),
        lambda candidate: validate_routes(instance, candidate).feasible,
        max_steps=adaptive_steps,
        patience=patience,
        context={
            "instance": instance.name,
            "scale": instance.scale,
            "seed": instance.seed,
            "source": source,
        },
    )
    inter_moves = sum(
        record.moves for record in search.trace
        if record.accepted and record.action in ("relocate", "swap")
    )
    return _candidate_from_routes(
        instance,
        source,
        _route_lists(search.solution),
        started=started,
        initial_objective=initial_objective,
        two_opt_moves=two_opt_moves,
        inter_route_moves=inter_moves,
        accepted_moves=two_opt_moves + search.accepted_moves,
        trace=search.trace,
        termination_reason=search.termination_reason,
    )


def _solve_reference(instance: Instance, method: str) -> SolveResult:
    started = time.perf_counter()
    if method == B_METHOD:
        routes, construction_violations = greedy_solve(instance, NEAREST_METHOD)
        two_opt_moves = 0
        inter_route_moves = 0
        source = "nearest"
    elif method == D_METHOD:
        routes, two_opt_moves, inter_route_moves, _gain = solve_week5_method(
            instance, HYBRID_METHOD
        )
        construction_violations = []
        source = "composite"
    else:
        raise ValueError(f"unknown reference method: {method}")
    validation = validate_routes(instance, routes)
    violations = tuple(dict.fromkeys([*construction_violations, *validation.violations]))
    feasible = validation.feasible and not construction_violations
    objective = validation.objective if feasible else math.inf
    candidate = CandidateSolution(
        source=source,
        routes=_route_tuple(routes),
        initial_objective=objective,
        final_objective=objective,
        feasible=feasible,
        violations=violations,
        two_opt_moves=two_opt_moves,
        inter_route_moves=inter_route_moves,
        accepted_moves=two_opt_moves + inter_route_moves,
        runtime_sec=time.perf_counter() - started,
        termination_reason="reference_method",
    )
    return SolveResult(
        method=method,
        routes=candidate.routes,
        feasible=feasible,
        objective=objective,
        violations=violations,
        selected_source=source,
        initial_objective=objective,
        runtime_sec=candidate.runtime_sec,
        two_opt_moves=two_opt_moves,
        inter_route_moves=inter_route_moves,
        accepted_moves=two_opt_moves + inter_route_moves,
        termination_reason="reference_method",
        candidates=(candidate,),
    )


def solve_method(
    instance: Instance,
    method: str,
    *,
    adaptive_steps: int = 12,
    patience: int = 4,
) -> SolveResult:
    """Solve one instance with a Week 6 comparison method."""

    if method in (B_METHOD, D_METHOD):
        return _solve_reference(instance, method)
    if method not in (E_FIXED_METHOD, E_ADAPTIVE_METHOD):
        raise ValueError(f"unknown Week 6 method: {method}")

    started = time.perf_counter()
    mode = "fixed" if method == E_FIXED_METHOD else "adaptive"
    candidates = [
        _build_portfolio_candidate(
            instance,
            source,
            construction_method,
            mode,
            adaptive_steps,
            patience,
        )
        for source, construction_method in SOURCE_METHODS
    ]
    selected = choose_best_candidate(candidates)
    all_traces = tuple(record for candidate in candidates for record in candidate.trace)
    return SolveResult(
        method=method,
        routes=selected.routes,
        feasible=selected.feasible,
        objective=selected.final_objective,
        violations=selected.violations,
        selected_source=selected.source,
        initial_objective=selected.initial_objective,
        runtime_sec=time.perf_counter() - started,
        two_opt_moves=selected.two_opt_moves,
        inter_route_moves=selected.inter_route_moves,
        accepted_moves=selected.accepted_moves,
        trace=all_traces,
        termination_reason=selected.termination_reason,
        candidates=tuple(candidates),
    )
