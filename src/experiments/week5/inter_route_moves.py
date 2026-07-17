#!/usr/bin/env python3
"""Week 5 route-improvement operators: feasibility-aware inter-route moves.

Week 4 added intra-route 2-opt, which only reorders customers *inside* one
route.  The Week 4 report found that Method C still trailed the nearest-customer
baseline on the medium (50-customer) scale, and named inter-route local search
(or-opt relocation and customer swap) as the next step to close that gap.

This module implements two classic inter-route neighbourhoods:

* ``relocate`` (or-opt-1): move a single customer out of its current route and
  insert it at the best feasible position in another route.
* ``swap``: exchange one customer in route ``i`` with one customer in route
  ``j``.

Both operators are feasibility-aware: a move is accepted only when an injected
checker confirms every affected route stays feasible *and* the total distance
strictly decreases.  The checker is passed in by the runner so this module does
not depend on the instance data classes.
"""

from __future__ import annotations

from typing import Callable

# A checker takes a candidate route (list of node ids) and returns
# ``(is_feasible, route_distance)`` -- identical contract to the Week 4 2-opt.
RouteChecker = Callable[[list[int]], "tuple[bool, float]"]


def _route_customers(route: list[int], customer_ids: set[int]) -> list[int]:
    """Return the positions in ``route`` that hold customer nodes."""
    return [pos for pos, node_id in enumerate(route) if node_id in customer_ids]


def _best_relocate_into(
    receiver: list[int],
    customer_id: int,
    customer_ids: set[int],
    checker: RouteChecker,
    current_distance: float,
) -> tuple[list[int], float] | None:
    """Try inserting ``customer_id`` at every gap in ``receiver``.

    Returns the best feasible ``(new_route, new_distance)`` or ``None`` if no
    insertion is feasible.  Insertion positions run from just after the depot to
    just before the closing depot so the route stays depot-anchored.
    """
    best: tuple[list[int], float] | None = None
    for pos in range(1, len(receiver)):
        candidate = receiver[:pos] + [customer_id] + receiver[pos:]
        ok, dist = checker(candidate)
        if not ok:
            continue
        if best is None or dist < best[1]:
            best = (candidate, dist)
    if best is None:
        return None
    # Only report an insertion that does not by itself exceed the caller's
    # accounting; the accept/reject decision on the whole move is made outside.
    return best


def relocate_pass(
    routes: list[list[int]],
    customer_ids: set[int],
    checker: RouteChecker,
) -> tuple[list[list[int]], int]:
    """One sweep of or-opt-1 relocations across all ordered route pairs.

    For every customer in every donor route, try moving it into every other
    route.  Accept the first move that keeps both routes feasible and strictly
    lowers the combined distance of the two routes.  Returns the updated route
    list and the number of relocations applied.
    """
    routes = [list(route) for route in routes]
    moves = 0
    for i in range(len(routes)):
        donor_positions = _route_customers(routes[i], customer_ids)
        # Iterate over a snapshot because routes[i] mutates as we accept moves.
        for pos in list(donor_positions):
            if pos >= len(routes[i]):
                continue
            customer_id = routes[i][pos]
            if customer_id not in customer_ids:
                continue
            reduced_donor = routes[i][:pos] + routes[i][pos + 1 :]
            donor_ok, donor_dist = checker(reduced_donor)
            if not donor_ok:
                continue
            _old_donor_ok, old_donor_dist = checker(routes[i])
            for j in range(len(routes)):
                if j == i:
                    continue
                old_recv_ok, old_recv_dist = checker(routes[j])
                if not old_recv_ok:
                    continue
                inserted = _best_relocate_into(
                    routes[j], customer_id, customer_ids, checker, old_recv_dist
                )
                if inserted is None:
                    continue
                new_recv, new_recv_dist = inserted
                before = old_donor_dist + old_recv_dist
                after = donor_dist + new_recv_dist
                if after + 1e-9 < before:
                    routes[i] = reduced_donor
                    routes[j] = new_recv
                    moves += 1
                    break
    # Drop routes that no longer contain any customer (donor emptied out).
    routes = [r for r in routes if _route_customers(r, customer_ids)]
    return routes, moves


def swap_pass(
    routes: list[list[int]],
    customer_ids: set[int],
    checker: RouteChecker,
) -> tuple[list[list[int]], int]:
    """One sweep of inter-route customer swaps.

    For every pair of routes (i, j) and every pair of customers (one from each),
    exchange them in place and accept the swap when both routes stay feasible
    and the combined distance strictly decreases.
    """
    routes = [list(route) for route in routes]
    moves = 0
    for i in range(len(routes)):
        for j in range(i + 1, len(routes)):
            positions_i = _route_customers(routes[i], customer_ids)
            positions_j = _route_customers(routes[j], customer_ids)
            _ok_i, dist_i = checker(routes[i])
            _ok_j, dist_j = checker(routes[j])
            for pi in positions_i:
                for pj in positions_j:
                    cand_i = list(routes[i])
                    cand_j = list(routes[j])
                    cand_i[pi], cand_j[pj] = cand_j[pj], cand_i[pi]
                    ok_i, new_dist_i = checker(cand_i)
                    if not ok_i:
                        continue
                    ok_j, new_dist_j = checker(cand_j)
                    if not ok_j:
                        continue
                    if new_dist_i + new_dist_j + 1e-9 < dist_i + dist_j:
                        routes[i] = cand_i
                        routes[j] = cand_j
                        moves += 1
                        # Recompute the baselines for the outer loops after a
                        # successful swap so later moves compare against the
                        # improved routes.
                        dist_i, dist_j = new_dist_i, new_dist_j
    return routes, moves


def inter_route_optimize(
    routes: list[list[int]],
    customer_ids: set[int],
    checker: RouteChecker,
    max_rounds: int = 10,
) -> tuple[list[list[int]], int]:
    """Alternate relocate and swap sweeps until neither improves the solution.

    Returns the improved route list and the total number of accepted moves
    (relocations + swaps).  The loop is bounded by ``max_rounds`` so it always
    terminates even if floating-point ties cause tiny oscillations.
    """
    total_moves = 0
    for _round in range(max_rounds):
        routes, relocations = relocate_pass(routes, customer_ids, checker)
        routes, swaps = swap_pass(routes, customer_ids, checker)
        round_moves = relocations + swaps
        total_moves += round_moves
        if round_moves == 0:
            break
    return routes, total_moves
