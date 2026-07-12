#!/usr/bin/env python3
"""Week 4 route-improvement operator: feasibility-aware 2-opt.

Greedy construction fixes the order in which customers are appended to a
route, but that order is rarely locally optimal for distance.  Classic 2-opt
repeatedly reverses a segment of the visiting order and keeps the change when
it shortens the tour.

For EVRP-TW a shorter tour is not automatically valid: reversing a segment can
break a time window or leave the battery unable to reach the next node.  This
module therefore only accepts a 2-opt move when an external feasibility check
confirms the whole route is still feasible.  The check itself is injected by
the runner so the operator stays independent of the instance data classes.
"""

from __future__ import annotations

from typing import Callable

# A checker takes a candidate route (list of node ids) and returns
# ``(is_feasible, route_distance)``.
RouteChecker = Callable[[list[int]], "tuple[bool, float]"]


def customer_positions(route: list[int], customer_ids: set[int]) -> list[int]:
    """Return the indices in ``route`` that hold customer nodes."""
    return [pos for pos, node_id in enumerate(route) if node_id in customer_ids]


def two_opt_route(
    route: list[int],
    customer_ids: set[int],
    checker: RouteChecker,
    max_passes: int = 20,
) -> tuple[list[int], float, int]:
    """Improve a single route with feasibility-aware 2-opt.

    Segment endpoints are restricted to customer positions so the depot anchors
    and any inserted charging stations keep their roles.  A reversal is applied
    only when the checker reports the new route is feasible and strictly
    shorter.  Returns ``(best_route, best_distance, moves_applied)``.
    """
    best_route = list(route)
    feasible, best_distance = checker(best_route)
    if not feasible:
        # Never touch an already-infeasible route: 2-opt cannot repair coverage
        # or fleet violations, and reversing segments could mask the real cause.
        return best_route, best_distance, 0

    moves_applied = 0
    for _pass in range(max_passes):
        improved = False
        positions = customer_positions(best_route, customer_ids)
        for a_index in range(len(positions) - 1):
            for b_index in range(a_index + 1, len(positions)):
                i = positions[a_index]
                k = positions[b_index]
                candidate = best_route[:i] + best_route[i : k + 1][::-1] + best_route[k + 1 :]
                ok, candidate_distance = checker(candidate)
                if ok and candidate_distance + 1e-9 < best_distance:
                    best_route = candidate
                    best_distance = candidate_distance
                    moves_applied += 1
                    improved = True
        if not improved:
            break
    return best_route, best_distance, moves_applied
