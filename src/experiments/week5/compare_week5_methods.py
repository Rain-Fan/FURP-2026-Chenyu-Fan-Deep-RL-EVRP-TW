#!/usr/bin/env python3
"""Week 5 consolidation experiment for EVRP-TW.

Week 5 is a consolidation week.  Weeks 1-4 built a controlled EVRP-TW
comparison pipeline and, in Week 4, a composite-score greedy with intra-route
2-opt (Method C).  The Week 4 report found that Method C still trailed the
nearest-customer baseline (Method B) on the medium 50-customer scale, and named
inter-route local search (or-opt relocation and swap) as the next step.

This week follows two of the Week 5 lab tracks:

* Track C (one focused extension): add Method D = Method C + inter-route local
  search (relocate + swap).  Method D is the only new method; C and B are
  carried over unchanged from Weeks 3-4 so the comparison stays controlled.
* Track B (consolidate / verify): rerun the same instance set across scales and
  stress profiles, and report whether the inter-route moves close the Week 4
  medium-scale gap.  A companion script (``reproducibility_check.py``) verifies
  that the algorithmic outputs are deterministic across repeated runs.

The research question is:

    Does adding inter-route local search (or-opt relocation and swap) on top of
    the Week 4 composite-score + 2-opt method close the medium-scale distance
    gap against the nearest-customer baseline, without losing feasibility?

Every number in the committed results is produced by running this script
locally.
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

# Reuse the Week 3 instance model and the Week 4 construction / checking /
# 2-opt machinery so all weeks share one definition of "feasible".
WEEK3_DIR = Path(__file__).resolve().parent.parent / "week3"
WEEK4_DIR = Path(__file__).resolve().parent.parent / "week4"
sys.path.insert(0, str(WEEK3_DIR))
sys.path.insert(0, str(WEEK4_DIR))

from compare_week3_baselines import (  # noqa: E402
    Instance,
    RouteSummary,
    distance,
    generate_instance,
    route_distance,
)
from compare_week4_methods import (  # noqa: E402
    COMPOSITE_METHOD,
    NEAREST_METHOD,
    apply_profile,
    apply_two_opt,
    check_single_route,
    greedy_solve,
)
from nearest_customer import DESCRIPTION as NEAREST_DESCRIPTION  # noqa: E402
from composite_score import DESCRIPTION as COMPOSITE_DESCRIPTION  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inter_route_moves import inter_route_optimize  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_SCALES = (20, 50, 100)
DEFAULT_INSTANCES_PER_SCALE = 12
DEFAULT_SEED = 20260713

# Method D is the Week 5 extension; C and B are references carried over so the
# comparison isolates the effect of the inter-route moves.
HYBRID_METHOD = "D_composite_inter_route"
METHODS = {
    HYBRID_METHOD: {
        "role": "tested_method",
        "description": (
            "Composite-score greedy with intra-route 2-opt and inter-route "
            "local search (or-opt relocation + swap)."
        ),
    },
    COMPOSITE_METHOD: {"role": "week4_reference", "description": COMPOSITE_DESCRIPTION},
    NEAREST_METHOD: {"role": "baseline", "description": NEAREST_DESCRIPTION},
}

# Same three stress profiles as Week 4 so the two weeks are directly comparable.
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
    inter_route_moves: int
    ls_gain: float
    time_window_violations: int
    capacity_violations: int
    energy_violations: int
    coverage_violations: int
    depot_violations: int
    routes: list[list[int]]
    route_summaries: list[RouteSummary]
    violations: list[str]


def method_for_construction(method: str) -> str:
    """Map a Week 5 method id onto the construction policy it is built on."""
    if method == HYBRID_METHOD:
        return COMPOSITE_METHOD
    return method


def _solution_distance(instance: Instance, routes: list[list[int]]) -> float:
    """Total distance over all routes (used only for local-search gain)."""
    return sum(route_distance(instance, route) for route in routes)


def solve_method(instance: Instance, method: str) -> tuple[list[list[int]], int, int, float]:
    """Construct and (for the tested methods) locally improve a solution.

    Returns ``(routes, two_opt_moves, inter_route_moves, ls_gain)`` where
    ``ls_gain`` is the total feasible distance removed by all local-search
    steps.  Method B is pure greedy; Method C adds intra-route 2-opt; Method D
    adds inter-route relocation and swap on top of C.
    """
    routes, _construction_violations = greedy_solve(instance, method_for_construction(method))
    two_opt_moves = 0
    inter_route_moves = 0
    ls_gain = 0.0

    if method in (COMPOSITE_METHOD, HYBRID_METHOD):
        before = _solution_distance(instance, routes)
        routes, two_opt_moves, _gain = apply_two_opt(instance, routes)
        if method == HYBRID_METHOD:
            checker = lambda candidate: check_single_route(instance, candidate)  # noqa: E731
            routes, inter_route_moves = inter_route_optimize(
                routes, instance.customer_ids, checker
            )
        after = _solution_distance(instance, routes)
        ls_gain = before - after

    return routes, two_opt_moves, inter_route_moves, ls_gain


def validate_solution(
    instance: Instance,
    method: str,
    profile: str,
    routes: list[list[int]],
    two_opt_moves: int,
    inter_route_moves: int,
    ls_gain: float,
) -> InstanceResult:
    """Independently replay all routes to compute metrics and confirm feasibility.

    Validation intentionally repeats the physical simulation rather than
    trusting the construction or local-search steps, so an accepted move can
    never hide a constraint violation.
    """
    served: list[int] = []
    violations: list[str] = []
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
        inter_route_moves=inter_route_moves,
        ls_gain=ls_gain,
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
    routes, two_opt_moves, inter_route_moves, ls_gain = solve_method(instance, method)
    result = validate_solution(
        instance, method, profile, routes, two_opt_moves, inter_route_moves, ls_gain
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
                        "mean_inter_route_moves": mean(r.inter_route_moves for r in subset),
                        "mean_ls_gain": mean(r.ls_gain for r in subset),
                        "coverage_violations": sum(r.coverage_violations for r in subset),
                        "time_window_violations": sum(r.time_window_violations for r in subset),
                        "energy_violations": sum(r.energy_violations for r in subset),
                    }
                )
    return rows


def compare_methods(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Compare tested Method D against each reference method, per profile/scale."""
    comparisons: list[dict[str, object]] = []
    keys = sorted({(str(r["profile"]), int(r["scale"])) for r in rows})
    for profile, scale in keys:
        d = next(
            (r for r in rows if r["profile"] == profile and r["scale"] == scale
             and r["method"] == HYBRID_METHOD),
            None,
        )
        if d is None:
            continue
        for reference in (COMPOSITE_METHOD, NEAREST_METHOD):
            ref = next(
                (r for r in rows if r["profile"] == profile and r["scale"] == scale
                 and r["method"] == reference),
                None,
            )
            if ref is None:
                continue
            d_obj = d["mean_objective_feasible"]
            ref_obj = ref["mean_objective_feasible"]
            comparisons.append(
                {
                    "profile": profile,
                    "scale": scale,
                    "tested_method": HYBRID_METHOD,
                    "reference": reference,
                    "feasibility_rate_delta": d["feasibility_rate"] - ref["feasibility_rate"],
                    "mean_feasible_objective_delta": (
                        d_obj - ref_obj if d_obj is not None and ref_obj is not None else None
                    ),
                    "mean_feasible_objective_pct": (
                        100.0 * (d_obj - ref_obj) / ref_obj
                        if d_obj is not None and ref_obj not in (None, 0) else None
                    ),
                    "mean_runtime_delta_sec": d["mean_runtime_sec"] - ref["mean_runtime_sec"],
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
    """Surface the cases where Method D improved most over Method C.

    For each (profile, scale, seed) we pair the D and C results and report the
    instances with the largest feasible distance reduction, which is the whole
    point of the inter-route extension.
    """
    by_key: dict[tuple[str, int, int], dict[str, InstanceResult]] = {}
    for r in results:
        by_key.setdefault((r.profile, r.scale, r.seed), {})[r.method] = r

    improvements: list[dict[str, object]] = []
    for (profile, scale, seed), methods in by_key.items():
        d = methods.get(HYBRID_METHOD)
        c = methods.get(COMPOSITE_METHOD)
        if d is None or c is None or not d.feasible or not c.feasible:
            continue
        improvements.append(
            {
                "profile": profile,
                "scale": scale,
                "seed": seed,
                "instance": d.instance,
                "method_c_distance": c.objective_distance,
                "method_d_distance": d.objective_distance,
                "distance_reduction": c.objective_distance - d.objective_distance,
                "inter_route_moves": d.inter_route_moves,
                "two_opt_moves": d.two_opt_moves,
            }
        )
    improvements.sort(key=lambda row: row["distance_reduction"], reverse=True)
    return improvements[:limit]


def build_metadata(args: argparse.Namespace, run_started: str, command: list[str]) -> dict[str, object]:
    return {
        "run_started_local": run_started,
        "run_command": " ".join(shlex.quote(part) for part in command),
        "research_question": (
            "Does adding inter-route local search (or-opt relocation and swap) on "
            "top of the Week 4 composite-score + 2-opt method close the "
            "medium-scale distance gap against the nearest-customer baseline, "
            "without losing feasibility?"
        ),
        "tested_method": METHODS[HYBRID_METHOD],
        "reference_methods": {
            COMPOSITE_METHOD: METHODS[COMPOSITE_METHOD],
            NEAREST_METHOD: METHODS[NEAREST_METHOD],
        },
        "fairness_controls": [
            "same Week 3 instance generator, coordinates, and random seeds",
            "same objective definition: total route distance",
            "same EVRP-TW feasibility checker for all methods",
            "same vehicle, battery, charging, and stopping rules",
            "local-search moves accept only feasible, strictly-shorter solutions",
            "Method D reuses Method C's construction and 2-opt unchanged",
        ],
        "parameter_profiles": PARAMETER_PROFILES,
        "scales": args.scales,
        "instances_per_scale": args.instances_per_scale,
        "base_seed": args.seed,
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
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    full_output = {
        "metadata": metadata,
        "aggregate": aggregate_rows,
        "comparison": comparisons,
        "instances": [result_to_dict(r) for r in results],
        "diagnostic_cases": diagnostic_cases(results),
    }
    (RESULTS_DIR / "week5_results.json").write_text(
        json.dumps(full_output, indent=2) + "\n", encoding="utf-8"
    )
    with (RESULTS_DIR / "week5_results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(aggregate_rows[0].keys()))
        writer.writeheader()
        writer.writerows(aggregate_rows)
    with (RESULTS_DIR / "week5_comparison.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(comparisons[0].keys()))
        writer.writeheader()
        writer.writerows(comparisons)


def write_markdown(
    aggregate_rows: list[dict[str, object]],
    comparisons: list[dict[str, object]],
    cases: list[dict[str, object]],
    run_started: str,
) -> None:
    lines = [
        "# Week 5 Consolidation Results: Inter-Route Local Search",
        "",
        f"Run started: `{run_started}`",
        "",
        "Research question: does adding inter-route local search (or-opt "
        "relocation + swap) on top of the Week 4 composite-score + 2-opt method "
        "(Method C) close the medium-scale distance gap against the "
        "nearest-customer baseline (Method B), without losing feasibility?",
        "",
        "D = composite + 2-opt + inter-route LS (tested). "
        "C = composite + 2-opt (Week 4). B = nearest-customer baseline.",
        "",
        "## Summary Table (by profile x scale x method)",
        "",
        "| Profile | Method | Customers | Instances | Feasible | Feas. rate | "
        "Mean feas. objective | Mean runtime (s) | Mean vehicles | "
        "Mean 2-opt | Mean inter-route | Mean LS gain |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregate_rows:
        lines.append(
            f"| {row['profile']} | {row['method']} | {row['scale']} | {row['instances']} | "
            f"{row['feasible_instances']} | {row['feasibility_rate']:.3f} | "
            f"{fmt_optional(row['mean_objective_feasible'])} | {row['mean_runtime_sec']:.6f} | "
            f"{row['mean_vehicles_used']:.3f} | {row['mean_two_opt_moves']:.3f} | "
            f"{row['mean_inter_route_moves']:.3f} | {row['mean_ls_gain']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Method D vs References",
            "",
            "Negative objective delta / percent = D finds shorter feasible routes.",
            "",
            "| Profile | Customers | Reference | Feasibility delta | "
            "Feasible-objective delta | Objective delta (%) | Runtime delta (s) |",
            "|---|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in comparisons:
        lines.append(
            f"| {row['profile']} | {row['scale']} | {row['reference']} | "
            f"{row['feasibility_rate_delta']:.3f} | "
            f"{fmt_optional(row['mean_feasible_objective_delta'])} | "
            f"{fmt_optional(row['mean_feasible_objective_pct'], 2)} | "
            f"{row['mean_runtime_delta_sec']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Largest Method D improvements over Method C",
            "",
            "These are the instances where inter-route moves removed the most "
            "distance relative to the Week 4 method.",
            "",
            "| Profile | Customers | Seed | C distance | D distance | Reduction | Inter-route moves |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for case in cases:
        lines.append(
            f"| {case['profile']} | {case['scale']} | {case['seed']} | "
            f"{case['method_c_distance']:.3f} | {case['method_d_distance']:.3f} | "
            f"{case['distance_reduction']:.3f} | {case['inter_route_moves']} |"
        )
    (RESULTS_DIR / "week5_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_run_log(
    aggregate_rows: list[dict[str, object]],
    run_started: str,
    command: list[str],
) -> None:
    log_lines = [
        "Week 5 consolidation experiment local run log",
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
            "mean_inter_route_moves={mean_inter_route_moves:.3f}, "
            "mean_runtime_sec={mean_runtime_sec:.6f}".format(**row)
        )
    log_lines.extend(
        [
            "",
            "Output files:",
            "- week5_results.json",
            "- week5_results.csv",
            "- week5_comparison.csv",
            "- week5_results.md",
            "- run_log.txt",
        ]
    )
    (RESULTS_DIR / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", nargs="+", type=int, default=list(DEFAULT_SCALES))
    parser.add_argument("--instances-per-scale", type=int, default=DEFAULT_INSTANCES_PER_SCALE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
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
    write_json_csv(results, aggregate_rows, comparisons, metadata)
    write_markdown(aggregate_rows, comparisons, diagnostic_cases(results), run_started)
    write_run_log(aggregate_rows, run_started, sys.argv)
    print(
        json.dumps(
            {
                "results_dir": str(RESULTS_DIR),
                "runs": len(results),
                "profiles": args.profiles,
                "methods": list(METHODS),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
