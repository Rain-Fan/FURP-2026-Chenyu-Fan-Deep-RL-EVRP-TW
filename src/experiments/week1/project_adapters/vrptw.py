"""Week 1 VRPTW baseline."""

from __future__ import annotations

from ortools.constraint_solver import pywrapcp

from or_tools_common import default_search_parameters, extract_routes
from routing_data import TIME_MATRIX, TIME_WINDOWS


def solve_vrptw() -> dict[str, object]:
    # VRPTW replaces distance cost with travel-time cost and constrains when
    # each customer may be served.
    manager = pywrapcp.RoutingIndexManager(len(TIME_MATRIX), 4, 0)
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index: int, to_index: int) -> int:
        return TIME_MATRIX[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)

    # The Time dimension stores arrival/service times. Slack allows waiting
    # when a vehicle arrives before a customer's ready time.
    routing.AddDimension(transit, 30, 30, False, "Time")
    time_dimension = routing.GetDimensionOrDie("Time")
    for node, time_window in enumerate(TIME_WINDOWS):
        if node == 0:
            continue
        # Each non-depot node must be reached inside its service window.
        time_dimension.CumulVar(manager.NodeToIndex(node)).SetRange(*time_window)
    for vehicle_id in range(4):
        start_index = routing.Start(vehicle_id)
        time_dimension.CumulVar(start_index).SetRange(*TIME_WINDOWS[0])
        # Finalizers ask OR-Tools to choose tighter start/end times when several
        # routes have the same objective value.
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(start_index))
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(vehicle_id)))
    solution = routing.SolveWithParameters(default_search_parameters())
    if solution is None:
        raise RuntimeError("VRPTW baseline did not find a solution")
    routes = extract_routes(manager, routing, solution, time_dimension)
    return {
        "problem": "VRPTW",
        "objective": solution.ObjectiveValue(),
        "objective_interpretation": "total travel time",
        "total_travel_time": sum(route["distance"] for route in routes),
        "routes": routes,
    }


if __name__ == "__main__":
    result = solve_vrptw()
    print(f"{result['problem']}: objective={result['objective']}, routes={len(result['routes'])}")
