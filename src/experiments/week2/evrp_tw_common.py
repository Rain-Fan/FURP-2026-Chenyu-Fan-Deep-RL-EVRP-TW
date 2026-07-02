"""Shared EVRP-TW instance and repair utilities for Week 2."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable

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
        # Customers are sampled in a square around the depot. Wide time windows
        # keep the focus on method comparison rather than impossible instances.
        x = rng.uniform(5.0, 95.0)
        y = rng.uniform(5.0, 95.0)
        d0 = math.hypot(x - depot.x, y - depot.y)
        ready = max(0.0, d0 * 0.2 + rng.uniform(0.0, 80.0))
        width = rng.uniform(900.0, 1200.0)
        customers.append(
            Node(i, "customer", x, y, rng.randint(1, 5), ready, ready + width, 5.0)
        )

    station_count = max(6, math.ceil(scale / 16))
    for j in range(station_count):
        # Stations alternate between two radii around the depot, giving repair
        # logic reachable charging options in several directions.
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


def check_solution(instance: Instance, routes: list[list[int]]) -> tuple[bool, float, list[str]]:
    """Validate route feasibility and compute total route distance."""
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
            # Simulate the route leg by leg so violations can be attributed to
            # the exact route and node where they occur.
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
            elif node.kind in {"station", "depot"}:
                # This simplified baseline assumes a full recharge at stations
                # and a fresh battery when returning to the depot.
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


def nearest_reachable_station(
    instance: Instance, current: int, next_node: int, battery: float
) -> int | None:
    options: list[tuple[float, int]] = []
    current_node = instance.node(current)
    target = instance.node(next_node)
    for station in instance.stations:
        # A station is useful only if the vehicle can reach it now and can then
        # reach the intended next customer/depot after charging.
        to_station = distance(current_node, station)
        station_to_target = distance(station, target)
        if (
            to_station <= battery + 1e-7
            and station_to_target <= instance.battery_capacity + 1e-7
        ):
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
    """Split a customer sequence into routes, then repair battery feasibility."""
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
        # Close the current route before adding a customer that would violate
        # capacity, miss its due time, or prevent returning to the depot in time.
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
