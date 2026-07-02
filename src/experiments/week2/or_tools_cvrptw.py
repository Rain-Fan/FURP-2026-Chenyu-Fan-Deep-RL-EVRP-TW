"""Week 2 OR-Tools CVRPTW baseline with charging-station repair."""

from __future__ import annotations

import time

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
except ImportError:  # pragma: no cover - handled at runtime.
    pywrapcp = None
    routing_enums_pb2 = None

from evrp_tw_common import (
    EvalResult,
    Instance,
    check_solution,
    distance,
    repair_route_energy,
    split_and_repair,
)


def solve_or_tools_cvrptw(instance: Instance, time_limit_sec: int = 10) -> EvalResult:
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
    manager = pywrapcp.RoutingIndexManager(len(nodes), instance.max_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)
    scaled_dist = [[int(round(distance(a, b) * 10.0)) for b in nodes] for a in nodes]

    def distance_callback(from_index: int, to_index: int) -> int:
        return scaled_dist[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    def demand_callback(from_index: int) -> int:
        return nodes[manager.IndexToNode(from_index)].demand

    transit = routing.RegisterTransitCallback(distance_callback)
    demand = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    routing.AddDimensionWithVehicleCapacity(
        demand, 0, [instance.capacity] * instance.max_vehicles, True, "Capacity"
    )
    routing.AddDimension(transit, int(300 * 10), int(1000 * 10), False, "Time")
    time_dimension = routing.GetDimensionOrDie("Time")
    for local_idx, node in enumerate(nodes):
        time_dimension.CumulVar(manager.NodeToIndex(local_idx)).SetRange(
            int(node.ready * 10.0), int(node.due * 10.0)
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
        ordered = sorted(instance.customer_ids, key=lambda idx: instance.node(idx).ready)
        routes = split_and_repair(instance, ordered)
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
