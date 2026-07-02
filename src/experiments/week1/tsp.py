"""Week 1 TSP baseline."""

from __future__ import annotations

from ortools.constraint_solver import pywrapcp

from or_tools_common import default_search_parameters, extract_routes
from routing_data import DISTANCE_MATRIX, METRE_LOCATIONS


def solve_tsp() -> dict[str, object]:
    # TSP uses one vehicle and depot 0. OR-Tools needs a manager to translate
    # between solver indices and the node ids used in the distance matrix.
    manager = pywrapcp.RoutingIndexManager(len(METRE_LOCATIONS), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        # The callback is the objective cost for each possible arc.
        return DISTANCE_MATRIX[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)

    # PATH_CHEAPEST_ARC gives a deterministic smoke-test baseline that is easy
    # to reproduce before comparing more complex vehicle-routing algorithms.
    solution = routing.SolveWithParameters(default_search_parameters())
    if solution is None:
        raise RuntimeError("TSP baseline did not find a solution")
    return {
        "problem": "TSP",
        "objective": solution.ObjectiveValue(),
        "objective_interpretation": "total distance (m)",
        "routes": extract_routes(manager, routing, solution),
    }


if __name__ == "__main__":
    result = solve_tsp()
    print(f"{result['problem']}: objective={result['objective']}, routes={len(result['routes'])}")
