"""Week 2 POMO-style multi-start masked greedy baseline."""

from __future__ import annotations

import random
import time

from evrp_tw_common import EvalResult, Instance, check_solution, distance, split_and_repair


def solve_pomo_style(instance: Instance, starts: int = 24) -> EvalResult:
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
                key=lambda idx: distance(current, instance.node(idx)) + 0.05 * instance.node(idx).ready,
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
