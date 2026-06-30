#!/usr/bin/env python3
"""Week 3 baseline reproduction for EVRP-TW.

This script runs a deterministic feasibility-first greedy construction
baseline on locally generated EVRP-TW instances.  It records objective value,
feasibility, runtime, solver parameters, random seeds, route summaries, and
constraint-level diagnostics.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shlex
import sys
import platform
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable


RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_SCALES = (10, 25, 50)
DEFAULT_INSTANCES_PER_SCALE = 32
DEFAULT_SEED = 20260630


@dataclass(frozen=True)
class Node:
    idx: int
    kind: str
    x: float
    y: float
    demand: int
    ready: float
    due: float
    service: float


@dataclass(frozen=True)
class Instance:
    name: str
    scale: int
    seed: int
    depot: Node
    customers: list[Node]
    stations: list[Node]
    capacity: int
    battery_capacity: float
    energy_rate: float
    speed: float
    charge_time: float
    max_vehicles: int

    @property
    def nodes(self) -> list[Node]:
        return [self.depot, *self.customers, *self.stations]

    @property
    def customer_ids(self) -> set[int]:
        return {node.idx for node in self.customers}

    @property
    def station_ids(self) -> set[int]:
        return {node.idx for node in self.stations}

    def node(self, idx: int) -> Node:
        return self.nodes[idx]


@dataclass
class RouteSummary:
    route: list[int]
    distance: float
    load: int
    charge_count: int
    elapsed_time: float


@dataclass
class InstanceResult:
    instance: str
    scale: int
    seed: int
    objective_distance: float
    feasible: bool
    runtime_sec: float
    vehicles_used: int
    charge_count: int
    charging_time: float
    time_window_violations: int
    capacity_violations: int
    energy_violations: int
    coverage_violations: int
    depot_violations: int
    routes: list[list[int]]
    route_summaries: list[RouteSummary]
    violations: list[str]


def distance(a: Node, b: Node) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def generate_instance(scale: int, seed: int) -> Instance:
    rng = random.Random(seed)
    depot = Node(0, "depot", 50.0, 50.0, 0, 0.0, 900.0, 0.0)
    customers: list[Node] = []
    stations: list[Node] = []

    for idx in range(1, scale + 1):
        x = rng.uniform(8.0, 92.0)
        y = rng.uniform(8.0, 92.0)
        direct = math.hypot(x - depot.x, y - depot.y)
        ready = rng.uniform(0.0, 80.0) + direct * 0.35
        due = ready + rng.uniform(260.0, 380.0)
        customers.append(
            Node(
                idx=idx,
                kind="customer",
                x=x,
                y=y,
                demand=rng.randint(1, 6),
                ready=ready,
                due=due,
                service=5.0,
            )
        )

    station_count = max(4, math.ceil(scale / 12))
    for station_no in range(station_count):
        angle = 2.0 * math.pi * station_no / station_count
        radius = 22.0 + 12.0 * (station_no % 2)
        stations.append(
            Node(
                idx=scale + 1 + station_no,
                kind="station",
                x=50.0 + radius * math.cos(angle),
                y=50.0 + radius * math.sin(angle),
                demand=0,
                ready=0.0,
                due=900.0,
                service=0.0,
            )
        )

    return Instance(
        name=f"synthetic_evrptw_n{scale}_seed{seed}",
        scale=scale,
        seed=seed,
        depot=depot,
        customers=customers,
        stations=stations,
        capacity=45,
        battery_capacity=155.0,
        energy_rate=1.0,
        speed=1.0,
        charge_time=18.0,
        max_vehicles=max(3, math.ceil(scale / 6)),
    )


def nearest_recharge_distance(instance: Instance, node: Node) -> float:
    recharge_nodes = [instance.depot, *instance.stations]
    return min(distance(node, recharge) for recharge in recharge_nodes)


def route_distance(instance: Instance, route: list[int]) -> float:
    return sum(
        distance(instance.node(a), instance.node(b))
        for a, b in zip(route, route[1:])
    )


def choose_customer(
    instance: Instance,
    current: Node,
    unserved: set[int],
    load: int,
    battery: float,
    clock: float,
) -> int | None:
    candidates: list[tuple[float, float, int]] = []
    for customer_id in unserved:
        customer = instance.node(customer_id)
        leg = distance(current, customer)
        arrival = clock + leg / instance.speed
        start = max(arrival, customer.ready)
        battery_after = battery - leg * instance.energy_rate
        if load + customer.demand > instance.capacity:
            continue
        if battery_after < -1e-7:
            continue
        if start > customer.due + 1e-7:
            continue
        reserve = nearest_recharge_distance(instance, customer) * instance.energy_rate
        if battery_after < reserve - 1e-7:
            continue
        score = customer.due + leg * 0.1
        candidates.append((score, leg, customer_id))
    if not candidates:
        return None
    return min(candidates)[2]


def nearest_reachable_station(
    instance: Instance,
    current: Node,
    battery: float,
    clock: float,
) -> int | None:
    options: list[tuple[float, int]] = []
    for station in instance.stations:
        leg = distance(current, station)
        if leg * instance.energy_rate > battery + 1e-7:
            continue
        if clock + leg / instance.speed > station.due + 1e-7:
            continue
        options.append((leg, station.idx))
    if not options:
        return None
    return min(options)[1]


def travel_to(
    instance: Instance,
    current: Node,
    target: Node,
    battery: float,
    clock: float,
) -> tuple[float, float]:
    leg = distance(current, target)
    battery -= leg * instance.energy_rate
    clock += leg / instance.speed
    clock = max(clock, target.ready) + target.service
    if target.kind == "station":
        clock += instance.charge_time
        battery = instance.battery_capacity
    elif target.kind == "depot":
        battery = instance.battery_capacity
    return battery, clock


def close_route(
    instance: Instance,
    route: list[int],
    battery: float,
    clock: float,
    violations: list[str],
) -> tuple[list[int], float, float]:
    current = instance.node(route[-1])
    depot = instance.depot
    guard = 0
    while current.idx != depot.idx and guard < len(instance.stations) + 2:
        leg_to_depot = distance(current, depot)
        if leg_to_depot * instance.energy_rate <= battery + 1e-7:
            route.append(depot.idx)
            battery, clock = travel_to(instance, current, depot, battery, clock)
            return route, battery, clock
        station_id = nearest_reachable_station(instance, current, battery, clock)
        if station_id is None:
            violations.append(f"cannot return to depot from node {current.idx}")
            return route, battery, clock
        route.append(station_id)
        station = instance.node(station_id)
        battery, clock = travel_to(instance, current, station, battery, clock)
        current = station
        guard += 1
    if route[-1] != depot.idx:
        violations.append(f"route did not close at depot: {route}")
    return route, battery, clock


def greedy_solve(instance: Instance) -> tuple[list[list[int]], list[str]]:
    unserved = set(instance.customer_ids)
    routes: list[list[int]] = []
    violations: list[str] = []

    for _vehicle in range(instance.max_vehicles):
        if not unserved:
            break
        route = [instance.depot.idx]
        current = instance.depot
        load = 0
        battery = instance.battery_capacity
        clock = 0.0
        route_has_customer = False
        last_station: int | None = None

        for _step in range((instance.scale + len(instance.stations)) * 3):
            customer_id = choose_customer(instance, current, unserved, load, battery, clock)
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
                    route, battery, clock = close_route(
                        instance, route, battery, clock, violations
                    )
                    routes.append(route)
                    return routes, violations
                continue

            if route_has_customer:
                route, battery, clock = close_route(
                    instance, route, battery, clock, violations
                )
                routes.append(route)
                break

            station_id = nearest_reachable_station(instance, current, battery, clock)
            if station_id is not None and station_id != last_station:
                route.append(station_id)
                station = instance.node(station_id)
                battery, clock = travel_to(instance, current, station, battery, clock)
                current = station
                last_station = station_id
                continue

            violations.append(
                f"vehicle cannot serve any remaining customer from node {current.idx}"
            )
            routes.append(route)
            break

    if unserved:
        violations.append(f"unserved customers: {sorted(unserved)[:20]}")
    return routes, violations


def validate_solution(
    instance: Instance,
    routes: list[list[int]],
    construction_violations: list[str],
) -> InstanceResult:
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
                violations.append(
                    f"route {route_no} negative battery before node {node_idx}"
                )
            clock += leg / instance.speed
            if clock < node.ready:
                clock = node.ready
            if clock > node.due + 1e-7:
                time_window_violations += 1
                violations.append(
                    f"route {route_no} misses time window at node {node_idx}"
                )
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
        instance=instance.name,
        scale=instance.scale,
        seed=instance.seed,
        objective_distance=objective,
        feasible=not violations,
        runtime_sec=0.0,
        vehicles_used=len(routes),
        charge_count=charge_count,
        charging_time=charge_count * instance.charge_time,
        time_window_violations=time_window_violations,
        capacity_violations=capacity_violations,
        energy_violations=energy_violations,
        coverage_violations=coverage_violations,
        depot_violations=depot_violations,
        routes=routes,
        route_summaries=route_summaries,
        violations=violations,
    )


def run_instance(instance: Instance) -> InstanceResult:
    started = time.perf_counter()
    routes, construction_violations = greedy_solve(instance)
    result = validate_solution(instance, routes, construction_violations)
    result.runtime_sec = time.perf_counter() - started
    return result


def aggregate(results: list[InstanceResult]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scale in sorted({result.scale for result in results}):
        subset = [result for result in results if result.scale == scale]
        feasible = [result for result in subset if result.feasible]
        rows.append(
            {
                "scale": scale,
                "instances": len(subset),
                "feasible_instances": len(feasible),
                "feasibility_rate": len(feasible) / len(subset),
                "mean_objective_all": mean(r.objective_distance for r in subset),
                "mean_objective_feasible": (
                    mean(r.objective_distance for r in feasible) if feasible else None
                ),
                "std_objective_all": pstdev(r.objective_distance for r in subset),
                "mean_runtime_sec": mean(r.runtime_sec for r in subset),
                "max_runtime_sec": max(r.runtime_sec for r in subset),
                "mean_vehicles_used": mean(r.vehicles_used for r in subset),
                "mean_charge_count": mean(r.charge_count for r in subset),
                "time_window_violations": sum(r.time_window_violations for r in subset),
                "capacity_violations": sum(r.capacity_violations for r in subset),
                "energy_violations": sum(r.energy_violations for r in subset),
                "coverage_violations": sum(r.coverage_violations for r in subset),
                "depot_violations": sum(r.depot_violations for r in subset),
            }
        )
    return rows


def worst_cases(results: list[InstanceResult], limit: int = 3) -> list[dict[str, object]]:
    def rank_key(result: InstanceResult) -> tuple[int, float]:
        return (0 if result.feasible else 1, result.objective_distance)

    selected = sorted(results, key=rank_key, reverse=True)[:limit]
    cases = []
    for result in selected:
        cases.append(
            {
                "instance": result.instance,
                "scale": result.scale,
                "seed": result.seed,
                "objective_distance": result.objective_distance,
                "feasible": result.feasible,
                "vehicles_used": result.vehicles_used,
                "charge_count": result.charge_count,
                "violations": result.violations,
                "diagnosis": (
                    "infeasible route; inspect listed constraint violations"
                    if not result.feasible
                    else "feasible but high-distance case for this baseline"
                ),
                "first_route": result.routes[0] if result.routes else [],
            }
        )
    return cases


def result_to_dict(result: InstanceResult) -> dict[str, object]:
    record = asdict(result)
    record["route_summaries"] = [asdict(summary) for summary in result.route_summaries]
    return record


def write_outputs(
    results: list[InstanceResult],
    args: argparse.Namespace,
    run_started: str,
    command: list[str],
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    aggregate_rows = aggregate(results)
    cases = worst_cases(results)
    metadata = {
        "run_started_local": run_started,
        "run_command": " ".join(shlex.quote(part) for part in command),
        "method": "deterministic feasibility-first greedy construction",
        "description": (
            "At each step choose the feasible unserved customer with the "
            "earliest due-time priority; return to depot or visit a charging "
            "station when no customer can be served."
        ),
        "scales": args.scales,
        "instances_per_scale": args.instances_per_scale,
        "base_seed": args.seed,
        "solver_parameters": {
            "capacity": 45,
            "battery_capacity": 155.0,
            "energy_rate": 1.0,
            "speed": 1.0,
            "charge_time": 18.0,
            "station_rule": "max(4, ceil(customers / 12))",
            "max_vehicle_rule": "max(3, ceil(customers / 6))",
        },
        "hardware": {
            "platform": platform.platform(),
            "processor": platform.processor() or "unknown",
            "python_version": platform.python_version(),
        },
    }

    full_output = {
        "metadata": metadata,
        "aggregate": aggregate_rows,
        "instances": [result_to_dict(result) for result in results],
        "diagnostic_cases": cases,
    }
    (RESULTS_DIR / "week3_results.json").write_text(
        json.dumps(full_output, indent=2) + "\n",
        encoding="utf-8",
    )

    with (RESULTS_DIR / "week3_results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(aggregate_rows[0].keys()))
        writer.writeheader()
        writer.writerows(aggregate_rows)

    lines = [
        "# Week 3 Baseline Results",
        "",
        f"Run started: `{run_started}`",
        "",
        "Method: deterministic feasibility-first greedy construction baseline.",
        "",
        "| Customers | Instances | Feasible | Feasibility rate | Mean objective | "
        "Mean feasible objective | Mean runtime (s) | Mean vehicles | Mean charges | "
        "TW viol. | Capacity viol. | Energy viol. | Coverage viol. |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregate_rows:
        feasible_obj = row["mean_objective_feasible"]
        lines.append(
            f"| {row['scale']} | {row['instances']} | {row['feasible_instances']} | "
            f"{row['feasibility_rate']:.3f} | {row['mean_objective_all']:.3f} | "
            f"{feasible_obj:.3f} | " if feasible_obj is not None else ""
        )
        if feasible_obj is not None:
            lines[-1] += (
                f"{row['mean_runtime_sec']:.6f} | {row['mean_vehicles_used']:.3f} | "
                f"{row['mean_charge_count']:.3f} | {row['time_window_violations']} | "
                f"{row['capacity_violations']} | {row['energy_violations']} | "
                f"{row['coverage_violations']} |"
            )
    lines.extend(
        [
            "",
            "## Diagnostic cases",
            "",
        ]
    )
    for case in cases:
        lines.extend(
            [
                f"### {case['instance']}",
                "",
                f"- Scale: {case['scale']}",
                f"- Seed: {case['seed']}",
                f"- Objective distance: {case['objective_distance']:.3f}",
                f"- Feasible: {case['feasible']}",
                f"- Vehicles used: {case['vehicles_used']}",
                f"- Charge count: {case['charge_count']}",
                f"- Diagnosis: {case['diagnosis']}",
                f"- Violations: {case['violations'] if case['violations'] else 'none'}",
                f"- First route: `{case['first_route']}`",
                "",
            ]
        )
    (RESULTS_DIR / "week3_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    log_lines = [
        "Week 3 baseline local run log",
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
            "- customers={scale}, instances={instances}, feasible={feasible_instances}, "
            "feasibility_rate={feasibility_rate:.3f}, mean_objective_all={mean_objective_all:.3f}, "
            "mean_runtime_sec={mean_runtime_sec:.6f}".format(**row)
        )
    log_lines.extend(
        [
            "",
            "Output files:",
            "- week3_results.json",
            "- week3_results.csv",
            "- week3_results.md",
            "- run_log.txt",
        ]
    )
    (RESULTS_DIR / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", nargs="+", type=int, default=list(DEFAULT_SCALES))
    parser.add_argument("--instances-per-scale", type=int, default=DEFAULT_INSTANCES_PER_SCALE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_started = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    results: list[InstanceResult] = []
    for scale in args.scales:
        for offset in range(args.instances_per_scale):
            seed = args.seed + scale * 1000 + offset
            instance = generate_instance(scale, seed)
            results.append(run_instance(instance))
    write_outputs(results, args, run_started, sys.argv)
    print(json.dumps({"results_dir": str(RESULTS_DIR), "runs": len(results)}, indent=2))


if __name__ == "__main__":
    main()
