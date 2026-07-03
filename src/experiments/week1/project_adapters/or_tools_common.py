"""Shared Week 1 OR-Tools helpers."""

from __future__ import annotations

from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def default_search_parameters() -> pywrapcp.RoutingSearchParameters:
    parameters = pywrapcp.DefaultRoutingSearchParameters()
    parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    return parameters


def extract_routes(manager, routing, solution, dimension=None):
    routes = []
    for vehicle_id in range(manager.GetNumberOfVehicles()):
        if not routing.IsVehicleUsed(solution, vehicle_id):
            continue
        index = routing.Start(vehicle_id)
        nodes = []
        cumul = []
        distance = 0
        while not routing.IsEnd(index):
            nodes.append(manager.IndexToNode(index))
            if dimension is not None:
                time_var = dimension.CumulVar(index)
                cumul.append([solution.Min(time_var), solution.Max(time_var)])
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        nodes.append(manager.IndexToNode(index))
        if dimension is not None:
            time_var = dimension.CumulVar(index)
            cumul.append([solution.Min(time_var), solution.Max(time_var)])
        routes.append(
            {
                "vehicle": vehicle_id,
                "nodes": nodes,
                "distance": distance,
                "cumulative_time": cumul,
            }
        )
    return routes
