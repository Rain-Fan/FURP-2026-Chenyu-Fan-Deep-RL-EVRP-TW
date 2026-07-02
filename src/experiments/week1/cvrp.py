"""Week 1 CVRP baseline."""

from __future__ import annotations

from ortools.constraint_solver import pywrapcp

from or_tools_common import default_search_parameters, extract_routes
from routing_data import DEMANDS, DISTANCE_MATRIX, VEHICLE_CAPACITIES


def solve_cvrp() -> dict[str, object]:
    manager = pywrapcp.RoutingIndexManager(
        len(DISTANCE_MATRIX), len(VEHICLE_CAPACITIES), 0
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        return DISTANCE_MATRIX[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    def demand_callback(from_index: int) -> int:
        return DEMANDS[manager.IndexToNode(from_index)]

    transit = routing.RegisterTransitCallback(distance_callback)
    demand = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    routing.AddDimensionWithVehicleCapacity(
        demand, 0, VEHICLE_CAPACITIES, True, "Capacity"
    )
    solution = routing.SolveWithParameters(default_search_parameters())
    if solution is None:
        raise RuntimeError("CVRP baseline did not find a solution")
    routes = extract_routes(manager, routing, solution)
    for route in routes:
        route["load"] = sum(DEMANDS[node] for node in route["nodes"])
    return {
        "problem": "CVRP",
        "objective": solution.ObjectiveValue(),
        "objective_interpretation": "total distance (m)",
        "total_distance": sum(route["distance"] for route in routes),
        "routes": routes,
    }


if __name__ == "__main__":
    result = solve_cvrp()
    print(f"{result['problem']}: objective={result['objective']}, routes={len(result['routes'])}")
