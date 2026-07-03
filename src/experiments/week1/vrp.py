"""Week 1 VRP baseline."""

from __future__ import annotations

from ortools.constraint_solver import pywrapcp

from or_tools_common import default_search_parameters, extract_routes
from routing_data import DISTANCE_MATRIX


def solve_vrp() -> dict[str, object]:
    # VRP keeps the same locations as TSP, but allows four vehicles to split
    # the customer visits. All vehicles still start and end at depot 0.
    manager = pywrapcp.RoutingIndexManager(len(DISTANCE_MATRIX), 4, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        return DISTANCE_MATRIX[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)

    # The Distance dimension tracks per-route distance. The global span
    # coefficient penalizes the longest route, so the solver balances vehicles
    # instead of only minimizing the sum of all arcs.
    routing.AddDimension(transit, 0, 3000, True, "Distance")
    routing.GetDimensionOrDie("Distance").SetGlobalSpanCostCoefficient(100)
    solution = routing.SolveWithParameters(default_search_parameters())
    if solution is None:
        raise RuntimeError("VRP baseline did not find a solution")
    routes = extract_routes(manager, routing, solution)
    return {
        "problem": "VRP",
        "objective": solution.ObjectiveValue(),
        "objective_interpretation": "total distance + 100 x longest-route distance",
        "total_distance": sum(route["distance"] for route in routes),
        "maximum_route_distance": max(route["distance"] for route in routes),
        "routes": routes,
    }


if __name__ == "__main__":
    result = solve_vrp()
    print(f"{result['problem']}: objective={result['objective']}, routes={len(result['routes'])}")
