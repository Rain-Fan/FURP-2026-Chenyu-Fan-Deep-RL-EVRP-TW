#!/usr/bin/env python3
"""Week 2 EVRP-TW baseline recreation and comparison.

The lab asks for POMO, GA, and OR-style baselines with added electric-vehicle
and time-window constraints.  This script implements lightweight, auditable
recreations on the same generated EVRP-TW instances:

* POMO-style parallel multi-start greedy rollout with feasibility masks.
* Genetic algorithm over customer permutations with EVRP-TW repair.
* OR-Tools CVRPTW sequencing followed by deterministic charging-station
  insertion and feasibility validation.

The goal is not to reproduce the original neural POMO training pipeline, which
is CVRP-only and expensive to adapt, but to recreate the core inference idea
needed this week: many parallel starts, masked constructive decoding, and
best-rollout selection under added E/TW constraints.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
except ImportError:  # pragma: no cover - handled at runtime in main.
    pywrapcp = None
    routing_enums_pb2 = None


RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_SCALES = (50, 100, 200)
DEFAULT_SEED = 20260621


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


@dataclass
class Instance:
    scale: int
    seed: int
    depot: Node
    customers: list[Node]
    stations: list[Node]
    capacity: int
    battery_capacity: float
    consumption_rate: float
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
class EvalResult:
    method: str
    scale: int
    objective: float | None
    feasible: bool
    runtime_sec: float
    vehicles_used: int
    routes: list[list[int]]
    convergence: str
    violations: list[str]


def distance(a: Node, b: Node) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def generate_instance(scale: int, seed: int) -> Instance:
    """Create deterministic EVRP-TW instances with clustered feasible windows."""
    rng = random.Random(seed + scale * 997)
    depot = Node(0, "depot", 50.0, 50.0, 0, 0.0, 2000.0, 0.0)
    customers: list[Node] = []
    stations: list[Node] = []

    for i in range(1, scale + 1):
        x = rng.uniform(5.0, 95.0)
        y = rng.uniform(5.0, 95.0)
        d0 = math.hypot(x - depot.x, y - depot.y)
        ready = max(0.0, d0 * 0.2 + rng.uniform(0.0, 80.0))
        width = rng.uniform(900.0, 1200.0)
        customers.append(
            Node(
                i,
                "customer",
                x,
                y,
                rng.randint(1, 5),
                ready,
                ready + width,
                5.0,
            )
        )

    station_count = max(6, math.ceil(scale / 16))
    for j in range(station_count):
        angle = (2.0 * math.pi * j) / station_count
        radius = 18.0 + 20.0 * (j % 2)
        idx = scale + 1 + j
        stations.append(
            Node(
                idx,
                "station",
                50.0 + radius * math.cos(angle),
                50.0 + radius * math.sin(angle),
                0,
                0.0,
                2000.0,
                18.0,
            )
        )

    return Instance(
        scale=scale,
        seed=seed,
        depot=depot,
        customers=customers,
        stations=stations,
        capacity=45,
        battery_capacity=250.0,
        consumption_rate=1.0,
        charge_time=18.0,
        max_vehicles=max(8, math.ceil(scale / 5)),
    )


def route_distance(instance: Instance, route: list[int]) -> float:
    return sum(
        distance(instance.node(a), instance.node(b))
        for a, b in zip(route, route[1:])
    )


def check_solution(instance: Instance, routes: list[list[int]]) -> tuple[bool, float, list[str]]:
    served: list[int] = []
    violations: list[str] = []
    total_distance = 0.0

    if len(routes) > instance.max_vehicles:
        violations.append(f"vehicles_used={len(routes)} > max={instance.max_vehicles}")

    for route_no, route in enumerate(routes, start=1):
        if not route:
            continue
        if route[0] != 0 or route[-1] != 0:
            violations.append(f"route {route_no} does not start/end at depot")
            continue
        load = 0
        clock = 0.0
        battery = instance.battery_capacity
        for prev_idx, node_idx in zip(route, route[1:]):
            prev = instance.node(prev_idx)
            node = instance.node(node_idx)
            leg = distance(prev, node)
            total_distance += leg
            battery -= leg * instance.consumption_rate
            if battery < -1e-7:
                violations.append(f"route {route_no} negative battery at node {node_idx}")
            clock += leg
            if clock < node.ready:
                clock = node.ready
            if clock > node.due + 1e-7:
                violations.append(f"route {route_no} misses time window at node {node_idx}")
            clock += node.service
            if node.kind == "customer":
                load += node.demand
                served.append(node.idx)
                if load > instance.capacity:
                    violations.append(f"route {route_no} capacity exceeded")
            elif node.kind == "station":
                battery = instance.battery_capacity
            elif node.kind == "depot":
                battery = instance.battery_capacity

    expected = instance.customer_ids
    served_set = set(served)
    if served_set != expected:
        missing = sorted(expected - served_set)
        extra = sorted(served_set - expected)
        if missing:
            violations.append(f"missing customers: {missing[:10]}")
        if extra:
            violations.append(f"unexpected customers: {extra[:10]}")
    duplicates = sorted({node for node in served if served.count(node) > 1})
    if duplicates:
        violations.append(f"duplicate customers: {duplicates[:10]}")
    return not violations, total_distance, violations


def can_append_customer(instance: Instance, route: list[int], candidate: int) -> bool:
    feasible, _, _ = check_solution(instance, [repair_route_energy(instance, [*route, candidate, 0])])
    return feasible


def nearest_reachable_station(instance: Instance, current: int, next_node: int, battery: float) -> int | None:
    options: list[tuple[float, int]] = []
    current_node = instance.node(current)
    target = instance.node(next_node)
    for station in instance.stations:
        to_station = distance(current_node, station)
        station_to_target = distance(station, target)
        if to_station <= battery + 1e-7 and station_to_target <= instance.battery_capacity + 1e-7:
            options.append((to_station + station_to_target, station.idx))
    if not options:
        return None
    return min(options)[1]


def repair_route_energy(instance: Instance, raw_route: list[int]) -> list[int]:
    """Insert charging stations between fixed route nodes when battery requires it."""
    repaired = [raw_route[0]]
    battery = instance.battery_capacity
    current = raw_route[0]
    for target in raw_route[1:]:
        leg = distance(instance.node(current), instance.node(target))
        if leg > battery + 1e-7:
            station = nearest_reachable_station(instance, current, target, battery)
            if station is None:
                repaired.append(target)
                battery -= leg
                current = target
                continue
            repaired.append(station)
            battery = instance.battery_capacity - distance(instance.node(station), instance.node(target))
        else:
            battery -= leg
        repaired.append(target)
        if instance.node(target).kind in {"depot", "station"}:
            battery = instance.battery_capacity
        current = target
    return repaired


def split_and_repair(instance: Instance, sequence: Iterable[int]) -> list[list[int]]:
    routes: list[list[int]] = []
    current = [0]
    load = 0
    clock = 0.0

    for customer_id in sequence:
        customer = instance.node(customer_id)
        projected_load = load + customer.demand
        projected_arrival = clock + distance(instance.node(current[-1]), customer)
        if projected_arrival < customer.ready:
            projected_arrival = customer.ready
        return_time = projected_arrival + customer.service + distance(customer, instance.depot)
        should_close = (
            projected_load > instance.capacity
            or projected_arrival > customer.due
            or return_time > instance.depot.due
        )
        if should_close and len(current) > 1:
            routes.append(repair_route_energy(instance, [*current, 0]))
            current = [0, customer_id]
            load = customer.demand
            clock = max(distance(instance.depot, customer), customer.ready) + customer.service
        else:
            current.append(customer_id)
            load = projected_load
            clock = projected_arrival + customer.service
    if len(current) > 1:
        routes.append(repair_route_energy(instance, [*current, 0]))
    return routes


def pomo_style_solver(instance: Instance, starts: int = 24) -> EvalResult:
    begin = time.perf_counter()
    best_routes: list[list[int]] = []
    best_cost = float("inf")
    best_feasible = False

    customer_ids = [node.idx for node in instance.customers]
    base_orders = [
        sorted(customer_ids, key=lambda idx: instance.node(idx).ready),
        sorted(customer_ids, key=lambda idx: instance.node(idx).due),
        sorted(customer_ids, key=lambda idx: distance(instance.depot, instance.node(idx))),
    ]
    rng = random.Random(instance.seed + 301)
    while len(base_orders) < starts:
        anchor = rng.choice(customer_ids)
        ordered = [anchor]
        remaining = set(customer_ids) - {anchor}
        while remaining:
            current = instance.node(ordered[-1])
            next_id = min(
                remaining,
                key=lambda idx: (
                    distance(current, instance.node(idx))
                    + 0.05 * instance.node(idx).ready
                ),
            )
            ordered.append(next_id)
            remaining.remove(next_id)
        base_orders.append(ordered)

    for order in base_orders[:starts]:
        routes = split_and_repair(instance, order)
        feasible, cost, _ = check_solution(instance, routes)
        if feasible and cost < best_cost:
            best_routes = routes
            best_cost = cost
            best_feasible = True
        elif not best_feasible and cost < best_cost:
            best_routes = routes
            best_cost = cost

    feasible, cost, violations = check_solution(instance, best_routes)
    return EvalResult(
        method="POMO-style multi-start masked greedy",
        scale=instance.scale,
        objective=round(cost, 2) if feasible else None,
        feasible=feasible,
        runtime_sec=round(time.perf_counter() - begin, 3),
        vehicles_used=len(best_routes),
        routes=best_routes,
        convergence=f"{min(starts, len(base_orders))} parallel-style starts; best feasible rollout selected",
        violations=violations,
    )


def ga_solver(instance: Instance, population_size: int = 48, generations: int = 80) -> EvalResult:
    begin = time.perf_counter()
    rng = random.Random(instance.seed + instance.scale + 17)
    customer_ids = [node.idx for node in instance.customers]

    def fitness(chromosome: list[int]) -> tuple[float, list[list[int]], bool, list[str]]:
        routes = split_and_repair(instance, chromosome)
        feasible, cost, violations = check_solution(instance, routes)
        penalty = 100000.0 * len(violations) + 10000.0 * max(0, len(routes) - instance.max_vehicles)
        return cost + penalty, routes, feasible, violations

    def crossover(a: list[int], b: list[int]) -> list[int]:
        left = rng.randrange(0, len(a))
        right = rng.randrange(left + 1, len(a) + 1)
        section = a[left:right]
        return section + [gene for gene in b if gene not in section]

    def mutate(chromosome: list[int]) -> None:
        if rng.random() < 0.45:
            i, j = rng.sample(range(len(chromosome)), 2)
            chromosome[i], chromosome[j] = chromosome[j], chromosome[i]
        if rng.random() < 0.25:
            i, j = sorted(rng.sample(range(len(chromosome)), 2))
            chromosome[i:j] = reversed(chromosome[i:j])

    population = []
    base = sorted(customer_ids, key=lambda idx: instance.node(idx).ready)
    population.append(base)
    for _ in range(population_size - 1):
        chromosome = customer_ids[:]
        rng.shuffle(chromosome)
        population.append(chromosome)

    best_score = float("inf")
    best_routes: list[list[int]] = []
    best_feasible = False
    best_violations: list[str] = []
    stagnant = 0

    for generation in range(generations):
        ranked = sorted((fitness(chromosome)[0], chromosome) for chromosome in population)
        score, leader = ranked[0]
        leader_score, leader_routes, leader_feasible, leader_violations = fitness(leader)
        if leader_score + 1e-7 < best_score:
            best_score = leader_score
            best_routes = leader_routes
            best_feasible = leader_feasible
            best_violations = leader_violations
            stagnant = 0
        else:
            stagnant += 1

        elites = [chromosome[:] for _, chromosome in ranked[: max(4, population_size // 6)]]
        next_population = elites[:]
        while len(next_population) < population_size:
            parent_a = rng.choice(elites)
            parent_b = rng.choice(population)
            child = crossover(parent_a, parent_b)
            mutate(child)
            next_population.append(child)
        population = next_population
        if best_feasible and stagnant >= 25 and generation >= 35:
            break

    feasible, cost, violations = check_solution(instance, best_routes)
    return EvalResult(
        method="GA permutation + EV/TW repair",
        scale=instance.scale,
        objective=round(cost, 2) if feasible else None,
        feasible=feasible,
        runtime_sec=round(time.perf_counter() - begin, 3),
        vehicles_used=len(best_routes),
        routes=best_routes,
        convergence=(
            f"population={population_size}, generations_run={generation + 1}, "
            f"best_feasible={best_feasible}"
        ),
        violations=violations or best_violations,
    )


def or_tools_solver(instance: Instance, time_limit_sec: int = 10) -> EvalResult:
    begin = time.perf_counter()
    if pywrapcp is None or routing_enums_pb2 is None:
        return EvalResult(
            "OR-Tools CVRPTW + charging repair",
            instance.scale,
            None,
            False,
            0.0,
            0,
            [],
            "OR-Tools is not installed",
            ["missing ortools dependency"],
        )

    customers = instance.customers
    nodes = [instance.depot, *customers]
    n = len(nodes)
    manager = pywrapcp.RoutingIndexManager(n, instance.max_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    scaled_dist = [
        [int(round(distance(a, b) * 10.0)) for b in nodes]
        for a in nodes
    ]

    def distance_callback(from_index: int, to_index: int) -> int:
        return scaled_dist[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    def demand_callback(from_index: int) -> int:
        return nodes[manager.IndexToNode(from_index)].demand

    transit = routing.RegisterTransitCallback(distance_callback)
    demand = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    routing.AddDimensionWithVehicleCapacity(
        demand,
        0,
        [instance.capacity] * instance.max_vehicles,
        True,
        "Capacity",
    )
    routing.AddDimension(transit, int(300 * 10), int(1000 * 10), False, "Time")
    time_dimension = routing.GetDimensionOrDie("Time")
    for local_idx, node in enumerate(nodes):
        index = manager.NodeToIndex(local_idx)
        time_dimension.CumulVar(index).SetRange(
            int(node.ready * 10.0),
            int(node.due * 10.0),
        )
    for vehicle_id in range(instance.max_vehicles):
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.Start(vehicle_id)))
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(vehicle_id)))

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromSeconds(time_limit_sec)

    solution = routing.SolveWithParameters(params)
    raw_routes: list[list[int]] = []
    if solution is not None:
        for vehicle_id in range(instance.max_vehicles):
            index = routing.Start(vehicle_id)
            local_route = [0]
            while not routing.IsEnd(index):
                index = solution.Value(routing.NextVar(index))
                local_node = manager.IndexToNode(index)
                if local_node != 0:
                    local_route.append(nodes[local_node].idx)
            if len(local_route) > 1:
                raw_routes.append([*local_route, 0])

    if not raw_routes:
        routes = split_and_repair(instance, sorted(instance.customer_ids, key=lambda idx: instance.node(idx).ready))
        convergence = f"OR-Tools no solution in {time_limit_sec}s; used deterministic fallback sequence"
    else:
        routes = [repair_route_energy(instance, route) for route in raw_routes]
        convergence = f"OR-Tools GLS time_limit={time_limit_sec}s; charging stations inserted post hoc"
    feasible, cost, violations = check_solution(instance, routes)
    return EvalResult(
        method="OR-Tools CVRPTW + charging repair",
        scale=instance.scale,
        objective=round(cost, 2) if feasible else None,
        feasible=feasible,
        runtime_sec=round(time.perf_counter() - begin, 3),
        vehicles_used=len(routes),
        routes=routes,
        convergence=convergence,
        violations=violations,
    )


def write_outputs(results: list[EvalResult]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS_DIR / "week2_results.json"
    csv_path = RESULTS_DIR / "week2_results.csv"
    md_path = RESULTS_DIR / "week2_results.md"

    json_path.write_text(
        json.dumps([asdict(result) for result in results], indent=2),
        encoding="utf-8",
    )
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "method",
                "scale",
                "objective",
                "feasible",
                "runtime_sec",
                "vehicles_used",
                "convergence",
                "violations",
            ],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "method": result.method,
                    "scale": result.scale,
                    "objective": result.objective,
                    "feasible": result.feasible,
                    "runtime_sec": result.runtime_sec,
                    "vehicles_used": result.vehicles_used,
                    "convergence": result.convergence,
                    "violations": "; ".join(result.violations),
                }
            )

    lines = [
        "# Week 2 EVRP-TW Baseline Results",
        "",
        "| Method | Customers | Objective distance | Feasible under E/TW | Runtime (s) | Vehicles | Convergence / notes |",
        "|---|---:|---:|---|---:|---:|---|",
    ]
    for result in results:
        objective = "N/A" if result.objective is None else f"{result.objective:.2f}"
        lines.append(
            "| "
            f"{result.method} | {result.scale} | {objective} | "
            f"{'Yes' if result.feasible else 'No'} | {result.runtime_sec:.3f} | "
            f"{result.vehicles_used} | {result.convergence} |"
        )
    lines.extend(
        [
            "",
            "All objective values are total Euclidean route distance and are only",
            "directly comparable when `Feasible under E/TW` is `Yes`.  E/TW",
            "feasibility is checked after each method has inserted or repaired",
            "capacity, time-window, depot-return, and battery/charging constraints.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scales", nargs="+", type=int, default=list(DEFAULT_SCALES))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--or-time-limit", type=int, default=10)
    args = parser.parse_args()

    results: list[EvalResult] = []
    for scale in args.scales:
        instance = generate_instance(scale, args.seed)
        results.append(pomo_style_solver(instance))
        results.append(ga_solver(instance))
        results.append(or_tools_solver(instance, args.or_time_limit))
    write_outputs(results)
    print(f"Wrote {len(results)} rows to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
