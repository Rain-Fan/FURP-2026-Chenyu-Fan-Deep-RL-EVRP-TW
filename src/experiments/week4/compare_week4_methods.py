#!/usr/bin/env python3
"""Week 4 method-improvement experiment for EVRP-TW.

Week 3 compared a due-time-priority greedy (Method A) against a
nearest-customer greedy (Baseline B) and found that A was worse: lower
feasibility, more coverage failures, and longer routes.  Week 3 explicitly
recommended a composite scoring rule plus a local-search repair as the next
step.

Week 4 implements that recommendation as Method C
(``C_composite_score`` + feasibility-aware 2-opt) and asks:

    Does a composite-score greedy with 2-opt local search recover the
    feasibility and route quality that the due-time-only method lost, and how
    does it compare with the nearest-customer baseline across scales and under
    tighter time windows / smaller batteries?

The experiment reuses the exact Week 3 instance generator and constraint model
so results stay directly comparable.  Methods A and B are imported unchanged
from the Week 3 package; only Method C is new.  Every number in the committed
results is produced by running this script locally.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import shlex
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev

# Reuse the Week 3 instance model, constraint checker, and greedy machinery so
# the two experiments share one definition of "feasible".
WEEK3_DIR = Path(__file__).resolve().parent.parent / "week3"
sys.path.insert(0, str(WEEK3_DIR))

from compare_week3_baselines import (  # noqa: E402
    Instance,
    Node,
    RouteSummary,
    close_route,
    distance,
    feasible_customer_candidates,
    generate_instance,
    nearest_reachable_station,
    nearest_recharge_distance,
    route_distance,
    travel_to,
)
from due_time_priority import (  # noqa: E402
    DESCRIPTION as DUE_TIME_DESCRIPTION,
    METHOD_ID as DUE_TIME_METHOD,
    METHOD_ROLE as DUE_TIME_ROLE,
    select_customer as select_due_time_customer,
)
from nearest_customer import (  # noqa: E402
    DESCRIPTION as NEAREST_DESCRIPTION,
    METHOD_ID as NEAREST_METHOD,
    METHOD_ROLE as NEAREST_ROLE,
    select_customer as select_nearest_customer,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from composite_score import (  # noqa: E402
    DESCRIPTION as COMPOSITE_DESCRIPTION,
    METHOD_ID as COMPOSITE_METHOD,
    METHOD_ROLE as COMPOSITE_ROLE,
    select_customer as select_composite_customer,
)
from two_opt import two_opt_route  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_SCALES = (20, 50, 100)
DEFAULT_INSTANCES_PER_SCALE = 12
DEFAULT_SEED = 20260706

# Methods C, A, and B all reuse the Week 3 feasibility model.  C is the tested
# improvement; A and B are carried over unchanged as references.
METHODS = {
    COMPOSITE_METHOD: {"role": COMPOSITE_ROLE, "description": COMPOSITE_DESCRIPTION},
    DUE_TIME_METHOD: {"role": "week3_reference", "description": DUE_TIME_DESCRIPTION},
    NEAREST_METHOD: {"role": "baseline", "description": NEAREST_DESCRIPTION},
}

# Parameter-sensitivity settings explore when methods start to fail: tighter
# time windows and a smaller battery both stress EVRP-TW feasibility.  The
# "baseline" profile reproduces the Week 3 instance parameters exactly.
PARAMETER_PROFILES = {
    "baseline": {"tw_scale": 1.0, "battery_scale": 1.0},
    "tight_tw": {"tw_scale": 0.6, "battery_scale": 1.0},
    "small_battery": {"tw_scale": 1.0, "battery_scale": 0.75},
}


@dataclass
class InstanceResult:
    method: str
    method_role: str
    profile: str
    instance: str
    scale: int
    seed: int
    objective_distance: float
    feasible: bool
    runtime_sec: float
    vehicles_used: int
    charge_count: int
    charging_time: float
    two_opt_moves: int
    two_opt_gain: float
    time_window_violations: int
    capacity_violations: int
    energy_violations: int
    coverage_violations: int
    depot_violations: int
    routes: list[list[int]]
    route_summaries: list[RouteSummary]
    violations: list[str]


def apply_profile(instance: Instance, profile: str) -> Instance:
    """Return a copy of ``instance`` transformed by a parameter profile.

    ``tight_tw`` shrinks every customer time window around its ready time;
    ``small_battery`` lowers the vehicle battery capacity.  Coordinates,
    demands, and seeds are untouched so instances stay comparable across
    profiles.
    """
    settings = PARAMETER_PROFILES[profile]
    tw_scale = settings["tw_scale"]
    battery_scale = settings["battery_scale"]

    customers: list[Node] = []
    for customer in instance.customers:
        width = (customer.due - customer.ready) * tw_scale
        customers.append(
            Node(
                idx=customer.idx,
                kind=customer.kind,
                x=customer.x,
                y=customer.y,
                demand=customer.demand,
                ready=customer.ready,
                due=customer.ready + width,
                service=customer.service,
            )
        )

    return Instance(
        name=f"{instance.name}_{profile}",
        scale=instance.scale,
        seed=instance.seed,
        depot=instance.depot,
        customers=customers,
        stations=list(instance.stations),
        capacity=instance.capacity,
        battery_capacity=instance.battery_capacity * battery_scale,
        energy_rate=instance.energy_rate,
        speed=instance.speed,
        charge_time=instance.charge_time,
        max_vehicles=instance.max_vehicles,
    )


def composite_candidates(
    instance: Instance,
    base_candidates: list[tuple[float, float, int]],
    clock: float,
) -> list[tuple[float, float, float, float, int]]:
    """Add normalized distance/urgency/slack features for the composite score.

    ``base_candidates`` is the shared ``(leg, due, customer_id)`` list from the
    Week 3 feasibility checker.  Normalization is done over the current
    candidate set so the three features are comparable regardless of instance
    scale.
    """
    legs = [leg for leg, _due, _cid in base_candidates]
    max_leg = max(legs) or 1.0
    slacks = [max(cust_due - clock, 0.0) for _leg, cust_due, _cid in base_candidates]
    max_slack = max(slacks) or 1.0
    dues = [cust_due for _leg, cust_due, _cid in base_candidates]
    max_due = max(dues) or 1.0

    enriched: list[tuple[float, float, float, float, int]] = []
    for (leg, cust_due, customer_id), slack in zip(base_candidates, slacks):
        norm_distance = leg / max_leg
        # Urgency: an early due time is more urgent, so smaller due -> larger
        # urgency term but we keep "lower score is better", hence due/max_due.
        norm_urgency = cust_due / max_due
        # Slack: little remaining slack should be served first, so a tight slack
        # maps to a small (preferred) term.
        norm_slack = slack / max_slack
        enriched.append((norm_distance, norm_urgency, norm_slack, leg, customer_id))
    return enriched


def choose_customer(
    instance: Instance,
    current: Node,
    unserved: set[int],
    load: int,
    battery: float,
    clock: float,
    method: str,
) -> int | None:
    candidates = feasible_customer_candidates(instance, current, unserved, load, battery, clock)
    if not candidates:
        return None
    # All methods see the same feasible candidate set; only the ranking differs.
    if method == COMPOSITE_METHOD:
        return select_composite_customer(composite_candidates(instance, candidates, clock))
    if method == DUE_TIME_METHOD:
        return select_due_time_customer(candidates)
    if method == NEAREST_METHOD:
        return select_nearest_customer(candidates)
    raise ValueError(f"Unknown method: {method}")


def greedy_solve(instance: Instance, method: str) -> tuple[list[list[int]], list[str]]:
    """Per-vehicle greedy construction (same control flow as Week 3)."""
    unserved = set(instance.customer_ids)
    routes: list[list[int]] = []
    violations: list[str] = []

    for _vehicle in range(instance.max_vehicles):
        if not unserved:
            break
        route = [0]
        current = instance.depot
        load = 0
        battery = instance.battery_capacity
        clock = 0.0
        route_has_customer = False
        last_station: int | None = None

        for _step in range((instance.scale + len(instance.stations)) * 3):
            customer_id = choose_customer(instance, current, unserved, load, battery, clock, method)
            if customer_id is not None:
                customer = instance.node(customer_id)
                route.append(customer_id)
                battery, clock = travel_to(instance, current, customer, battery, clock)
                load += customer.demand
                current = customer
                unserved.remove(customer_id)
                route_has_customer = True
                last_station = None
                if not unserved:
                    route, battery, clock = close_route(instance, route, battery, clock, violations)
                    routes.append(route)
                    return routes, violations
                continue

            if route_has_customer:
                route, battery, clock = close_route(instance, route, battery, clock, violations)
                routes.append(route)
                break

            station_id = nearest_reachable_station(instance, current, battery, clock)
            if station_id is not None and station_id != last_station:
                station = instance.node(station_id)
                route.append(station_id)
                battery, clock = travel_to(instance, current, station, battery, clock)
                current = station
                last_station = station_id
                continue

            violations.append(f"vehicle cannot serve any remaining customer from node {current.idx}")
            routes.append(route)
            break

    if unserved:
        violations.append(f"unserved customers: {sorted(unserved)[:20]}")
    return routes, violations


def check_single_route(instance: Instance, route: list[int]) -> tuple[bool, float]:
    """Replay one route and report ``(is_feasible, distance)``.

    This is the feasibility oracle injected into 2-opt.  It enforces the same
    load / time-window / battery rules as the full validator but on a single
    route, so a segment reversal is only accepted when the route stays valid.
    """
    if not route or route[0] != 0 or route[-1] != 0:
        return False, math.inf
    load = 0
    battery = instance.battery_capacity
    clock = 0.0
    total = 0.0
    for prev_idx, node_idx in zip(route, route[1:]):
        prev = instance.node(prev_idx)
        node = instance.node(node_idx)
        leg = distance(prev, node)
        total += leg
        battery -= leg * instance.energy_rate
        if battery < -1e-7:
            return False, math.inf
        clock += leg / instance.speed
        if clock < node.ready:
            clock = node.ready
        if clock > node.due + 1e-7:
            return False, math.inf
        clock += node.service
        if node.kind == "customer":
            load += node.demand
            if load > instance.capacity:
                return False, math.inf
        elif node.kind in ("station", "depot"):
            if node.kind == "station":
                clock += instance.charge_time
            battery = instance.battery_capacity
    return True, total


def apply_two_opt(
    instance: Instance,
    routes: list[list[int]],
) -> tuple[list[list[int]], int, float]:
    """Run feasibility-aware 2-opt on every route; return improved routes.

    Only Method C uses this step.  The total distance gained (old minus new)
    across all routes is reported so the report can quantify the local-search
    contribution.
    """
    customer_ids = instance.customer_ids
    improved_routes: list[list[int]] = []
    total_moves = 0
    total_gain = 0.0
    for route in routes:
        _ok, before = check_single_route(instance, route)
        new_route, after, moves = two_opt_route(
            route,
            customer_ids,
            lambda candidate: check_single_route(instance, candidate),
        )
        improved_routes.append(new_route)
        total_moves += moves
        if math.isfinite(before) and math.isfinite(after):
            total_gain += before - after
    return improved_routes, total_moves, total_gain


def validate_solution(
    instance: Instance,
    method: str,
    profile: str,
    routes: list[list[int]],
    construction_violations: list[str],
    two_opt_moves: int,
    two_opt_gain: float,
) -> InstanceResult:
    """Independently replay all routes to compute metrics and confirm feasibility."""
    served: list[int] = []
    violations = list(construction_violations)
    route_summaries: list[RouteSummary] = []
    objective = 0.0
    charge_count = 0
    time_window_violations = 0
    capacity_violations = 0
    energy_violations = 0
    depot_violations = 0

    if len(routes) > instance.max_vehicles:
        violations.append(f"vehicles_used={len(routes)} > max={instance.max_vehicles}")

    for route_no, route in enumerate(routes, start=1):
        if not route or route[0] != 0 or route[-1] != 0:
            depot_violations += 1
            violations.append(f"route {route_no} does not start and end at depot")
            continue
        load = 0
        battery = instance.battery_capacity
        clock = 0.0
        route_charge_count = 0
        for prev_idx, node_idx in zip(route, route[1:]):
            prev = instance.node(prev_idx)
            node = instance.node(node_idx)
            leg = distance(prev, node)
            objective += leg
            battery -= leg * instance.energy_rate
            if battery < -1e-7:
                energy_violations += 1
                violations.append(f"route {route_no} negative battery before node {node_idx}")
            clock += leg / instance.speed
            if clock < node.ready:
                clock = node.ready
            if clock > node.due + 1e-7:
                time_window_violations += 1
                violations.append(f"route {route_no} misses time window at node {node_idx}")
            clock += node.service
            if node.kind == "customer":
                load += node.demand
                served.append(node.idx)
                if load > instance.capacity:
                    capacity_violations += 1
                    violations.append(f"route {route_no} exceeds capacity")
            elif node.kind == "station":
                route_charge_count += 1
                charge_count += 1
                clock += instance.charge_time
                battery = instance.battery_capacity
            elif node.kind == "depot":
                battery = instance.battery_capacity
        route_summaries.append(
            RouteSummary(
                route=route,
                distance=route_distance(instance, route),
                load=load,
                charge_count=route_charge_count,
                elapsed_time=clock,
            )
        )

    coverage_violations = 0
    served_set = set(served)
    if served_set != instance.customer_ids:
        coverage_violations += 1
        missing = sorted(instance.customer_ids - served_set)
        extra = sorted(served_set - instance.customer_ids)
        if missing:
            violations.append(f"missing customers: {missing[:20]}")
        if extra:
            violations.append(f"unexpected customers: {extra[:20]}")
    duplicates = sorted({customer for customer in served if served.count(customer) > 1})
    if duplicates:
        coverage_violations += 1
        violations.append(f"duplicate customers: {duplicates[:20]}")

    return InstanceResult(
        method=method,
        method_role=METHODS[method]["role"],
        profile=profile,
        instance=instance.name,
        scale=instance.scale,
        seed=instance.seed,
        objective_distance=objective,
        feasible=not violations,
        runtime_sec=0.0,
        vehicles_used=len(routes),
        charge_count=charge_count,
        charging_time=charge_count * instance.charge_time,
        two_opt_moves=two_opt_moves,
        two_opt_gain=two_opt_gain,
        time_window_violations=time_window_violations,
        capacity_violations=capacity_violations,
        energy_violations=energy_violations,
        coverage_violations=coverage_violations,
        depot_violations=depot_violations,
        routes=routes,
        route_summaries=route_summaries,
        violations=violations,
    )


def run_instance(instance: Instance, method: str, profile: str) -> InstanceResult:
    started = time.perf_counter()
    routes, construction_violations = greedy_solve(instance, method)
    two_opt_moves = 0
    two_opt_gain = 0.0
    if method == COMPOSITE_METHOD:
        # Local search is the second half of the Week 4 improvement; only the
        # tested method uses it so its effect is attributable.
        routes, two_opt_moves, two_opt_gain = apply_two_opt(instance, routes)
    result = validate_solution(
        instance, method, profile, routes, construction_violations, two_opt_moves, two_opt_gain
    )
    result.runtime_sec = time.perf_counter() - started
    return result


def aggregate(results: list[InstanceResult]) -> list[dict[str, object]]:
    """Aggregate by (profile, scale, method) so every cell is comparable."""
    rows: list[dict[str, object]] = []
    profiles = sorted({r.profile for r in results}, key=list(PARAMETER_PROFILES).index)
    for profile in profiles:
        for scale in sorted({r.scale for r in results if r.profile == profile}):
            for method in METHODS:
                subset = [
                    r for r in results
                    if r.profile == profile and r.scale == scale and r.method == method
                ]
                if not subset:
                    continue
                feasible = [r for r in subset if r.feasible]
                rows.append(
                    {
                        "profile": profile,
                        "method": method,
                        "method_role": METHODS[method]["role"],
                        "scale": scale,
                        "instances": len(subset),
                        "feasible_instances": len(feasible),
                        "feasibility_rate": len(feasible) / len(subset),
                        "mean_objective_all": mean(r.objective_distance for r in subset),
                        "mean_objective_feasible": (
                            mean(r.objective_distance for r in feasible) if feasible else None
                        ),
                        "std_objective_feasible": (
                            pstdev(r.objective_distance for r in feasible)
                            if len(feasible) > 1 else 0.0
                        ) if feasible else None,
                        "mean_runtime_sec": mean(r.runtime_sec for r in subset),
                        "mean_vehicles_used": mean(r.vehicles_used for r in subset),
                        "mean_charge_count": mean(r.charge_count for r in subset),
                        "mean_two_opt_moves": mean(r.two_opt_moves for r in subset),
                        "mean_two_opt_gain": mean(r.two_opt_gain for r in subset),
                        "coverage_violations": sum(r.coverage_violations for r in subset),
                        "time_window_violations": sum(r.time_window_violations for r in subset),
                        "energy_violations": sum(r.energy_violations for r in subset),
                    }
                )
    return rows


def compare_methods(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Compare tested Method C against each reference method, per profile/scale."""
    comparisons: list[dict[str, object]] = []
    keys = sorted({(str(r["profile"]), int(r["scale"])) for r in rows})
    for profile, scale in keys:
        c = next(
            (r for r in rows if r["profile"] == profile and r["scale"] == scale
             and r["method"] == COMPOSITE_METHOD),
            None,
        )
        if c is None:
            continue
        for reference in (DUE_TIME_METHOD, NEAREST_METHOD):
            ref = next(
                (r for r in rows if r["profile"] == profile and r["scale"] == scale
                 and r["method"] == reference),
                None,
            )
            if ref is None:
                continue
            c_obj = c["mean_objective_feasible"]
            ref_obj = ref["mean_objective_feasible"]
            comparisons.append(
                {
                    "profile": profile,
                    "scale": scale,
                    "tested_method": COMPOSITE_METHOD,
                    "reference": reference,
                    "feasibility_rate_delta": c["feasibility_rate"] - ref["feasibility_rate"],
                    "mean_feasible_objective_delta": (
                        c_obj - ref_obj if c_obj is not None and ref_obj is not None else None
                    ),
                    "mean_runtime_delta_sec": c["mean_runtime_sec"] - ref["mean_runtime_sec"],
                    "coverage_violation_delta": c["coverage_violations"] - ref["coverage_violations"],
                }
            )
    return comparisons


def fmt_optional(value: object, digits: int = 3) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def result_to_dict(result: InstanceResult) -> dict[str, object]:
    record = asdict(result)
    record["route_summaries"] = [asdict(summary) for summary in result.route_summaries]
    return record


def diagnostic_cases(results: list[InstanceResult], limit: int = 4) -> list[dict[str, object]]:
    """Surface the hardest cases: infeasible first, then longest feasible."""
    failures = [r for r in results if not r.feasible]
    selected = sorted(
        failures if failures else results,
        key=lambda r: (r.scale, r.objective_distance),
        reverse=True,
    )[:limit]
    cases = []
    for r in selected:
        cases.append(
            {
                "method": r.method,
                "profile": r.profile,
                "instance": r.instance,
                "scale": r.scale,
                "seed": r.seed,
                "objective_distance": r.objective_distance,
                "feasible": r.feasible,
                "vehicles_used": r.vehicles_used,
                "two_opt_moves": r.two_opt_moves,
                "violations": r.violations,
                "diagnosis": (
                    "infeasible route; inspect listed constraint violations"
                    if not r.feasible else "feasible but high-distance case"
                ),
            }
        )
    return cases


def build_metadata(args: argparse.Namespace, run_started: str, command: list[str]) -> dict[str, object]:
    return {
        "run_started_local": run_started,
        "run_command": " ".join(shlex.quote(part) for part in command),
        "research_question": (
            "Does a composite-score greedy with feasibility-aware 2-opt local "
            "search recover the feasibility and route quality lost by the Week 3 "
            "due-time-only method, and how does it compare with the nearest-customer "
            "baseline across scales and under tighter time windows / smaller batteries?"
        ),
        "tested_method": METHODS[COMPOSITE_METHOD],
        "reference_methods": {
            DUE_TIME_METHOD: METHODS[DUE_TIME_METHOD],
            NEAREST_METHOD: METHODS[NEAREST_METHOD],
        },
        "fairness_controls": [
            "same Week 3 instance generator, coordinates, and random seeds",
            "same objective definition: total route distance",
            "same EVRP-TW feasibility checker for all methods",
            "same vehicle, battery, charging, and stopping rules",
            "2-opt accepts a move only if the route stays feasible and shorter",
        ],
        "parameter_profiles": PARAMETER_PROFILES,
        "scales": args.scales,
        "instances_per_scale": args.instances_per_scale,
        "base_seed": args.seed,
        "composite_weights": {
            "distance": 1.0,
            "urgency": 0.35,
            "slack": 0.25,
        },
        "hardware": {
            "platform": platform.platform(),
            "processor": platform.processor() or "unknown",
            "python_version": platform.python_version(),
        },
    }


def write_json_csv(
    results: list[InstanceResult],
    aggregate_rows: list[dict[str, object]],
    comparisons: list[dict[str, object]],
    metadata: dict[str, object],
    results_dir: Path,
) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    full_output = {
        "metadata": metadata,
        "aggregate": aggregate_rows,
        "comparison": comparisons,
        "instances": [result_to_dict(r) for r in results],
        "diagnostic_cases": diagnostic_cases(results),
    }
    (results_dir / "week4_results.json").write_text(
        json.dumps(full_output, indent=2) + "\n", encoding="utf-8"
    )
    with (results_dir / "week4_results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(aggregate_rows[0].keys()))
        writer.writeheader()
        writer.writerows(aggregate_rows)
    with (results_dir / "week4_comparison.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(comparisons[0].keys()))
        writer.writeheader()
        writer.writerows(comparisons)


def write_markdown(
    aggregate_rows: list[dict[str, object]],
    comparisons: list[dict[str, object]],
    cases: list[dict[str, object]],
    run_started: str,
    results_dir: Path,
) -> None:
    lines = [
        "# Week 4 Method-Improvement Results",
        "",
        f"Run started: `{run_started}`",
        "",
        "Research question: does a composite-score greedy with feasibility-aware "
        "2-opt (Method C) recover the feasibility and route quality lost by the "
        "Week 3 due-time-only method (A), and how does it compare with the "
        "nearest-customer baseline (B) across scales and stress profiles?",
        "",
        "C = composite-score greedy + 2-opt (tested). "
        "A = week3 due-time greedy. B = nearest-customer baseline.",
        "",
        "## Summary Table (by profile x scale x method)",
        "",
        "| Profile | Method | Customers | Instances | Feasible | Feas. rate | "
        "Mean feas. objective | Mean runtime (s) | Mean vehicles | Mean charges | "
        "Mean 2-opt moves | Mean 2-opt gain | Coverage viol. |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregate_rows:
        lines.append(
            f"| {row['profile']} | {row['method']} | {row['scale']} | {row['instances']} | "
            f"{row['feasible_instances']} | {row['feasibility_rate']:.3f} | "
            f"{fmt_optional(row['mean_objective_feasible'])} | {row['mean_runtime_sec']:.6f} | "
            f"{row['mean_vehicles_used']:.3f} | {row['mean_charge_count']:.3f} | "
            f"{row['mean_two_opt_moves']:.3f} | {row['mean_two_opt_gain']:.3f} | "
            f"{row['coverage_violations']} |"
        )

    lines.extend(
        [
            "",
            "## Method C vs References",
            "",
            "Positive feasibility delta = C is more often feasible. "
            "Negative objective delta = C finds shorter feasible routes.",
            "",
            "| Profile | Customers | Reference | Feasibility delta | "
            "Feasible-objective delta | Runtime delta (s) | Coverage-viol. delta |",
            "|---|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in comparisons:
        lines.append(
            f"| {row['profile']} | {row['scale']} | {row['reference']} | "
            f"{row['feasibility_rate_delta']:.3f} | "
            f"{fmt_optional(row['mean_feasible_objective_delta'])} | "
            f"{row['mean_runtime_delta_sec']:.6f} | {row['coverage_violation_delta']} |"
        )

    lines.extend(["", "## Diagnostic Cases", ""])
    for case in cases:
        lines.extend(
            [
                f"### {case['method']} on {case['instance']} ({case['profile']})",
                "",
                f"- Scale: {case['scale']}",
                f"- Objective distance: {case['objective_distance']:.3f}",
                f"- Feasible: {case['feasible']}",
                f"- Vehicles used: {case['vehicles_used']}",
                f"- 2-opt moves: {case['two_opt_moves']}",
                f"- Diagnosis: {case['diagnosis']}",
                f"- Violations: {case['violations'] if case['violations'] else 'none'}",
            ]
        )
    (results_dir / "week4_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_run_log(
    aggregate_rows: list[dict[str, object]],
    run_started: str,
    command: list[str],
    results_dir: Path,
) -> None:
    log_lines = [
        "Week 4 method-improvement local run log",
        "",
        f"Run started: {run_started}",
        f"Command: {' '.join(shlex.quote(part) for part in command)}",
        f"Python: {platform.python_version()}",
        f"Platform: {platform.platform()}",
        f"Processor: {platform.processor() or 'unknown'}",
        "",
        "Aggregate results:",
    ]
    for row in aggregate_rows:
        log_lines.append(
            "- profile={profile}, method={method}, customers={scale}, "
            "feasible={feasible_instances}/{instances}, "
            "feasibility_rate={feasibility_rate:.3f}, "
            "mean_feasible_objective={mean_objective_feasible}, "
            "mean_runtime_sec={mean_runtime_sec:.6f}".format(**row)
        )
    log_lines.extend(
        [
            "",
            "Output files:",
            "- week4_results.json",
            "- week4_results.csv",
            "- week4_comparison.csv",
            "- week4_results.md",
            "- run_log.txt",
        ]
    )
    (results_dir / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", nargs="+", type=int, default=list(DEFAULT_SCALES))
    parser.add_argument("--instances-per-scale", type=int, default=DEFAULT_INSTANCES_PER_SCALE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_DIR,
        help="Directory for generated result files.",
    )
    parser.add_argument(
        "--profiles",
        nargs="+",
        default=list(PARAMETER_PROFILES),
        choices=list(PARAMETER_PROFILES),
        help="Parameter-sensitivity profiles to run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_started = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    results: list[InstanceResult] = []
    for profile in args.profiles:
        for scale in args.scales:
            for offset in range(args.instances_per_scale):
                seed = args.seed + scale * 1000 + offset
                base_instance = generate_instance(scale, seed)
                instance = apply_profile(base_instance, profile)
                for method in METHODS:
                    results.append(run_instance(instance, method, profile))

    aggregate_rows = aggregate(results)
    comparisons = compare_methods(aggregate_rows)
    metadata = build_metadata(args, run_started, sys.argv)
    write_json_csv(results, aggregate_rows, comparisons, metadata, args.results_dir)
    write_markdown(aggregate_rows, comparisons, diagnostic_cases(results), run_started, args.results_dir)
    write_run_log(aggregate_rows, run_started, sys.argv, args.results_dir)
    print(
        json.dumps(
            {
                "results_dir": str(args.results_dir),
                "runs": len(results),
                "profiles": args.profiles,
                "methods": list(METHODS),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
