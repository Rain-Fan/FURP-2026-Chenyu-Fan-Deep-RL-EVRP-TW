#!/usr/bin/env python3
"""Reproduce the Google OR-Tools TSP, VRP, CVRP, and VRPTW baselines.

The 17-node instances and modelling choices are adapted from the official
Google OR-Tools routing guides:
https://developers.google.com/optimization/routing/
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


BLOCK_LOCATIONS = [
    (4, 4),
    (2, 0),
    (8, 0),
    (0, 1),
    (1, 1),
    (5, 2),
    (7, 2),
    (3, 3),
    (6, 3),
    (5, 5),
    (8, 5),
    (1, 6),
    (2, 6),
    (3, 7),
    (6, 7),
    (0, 8),
    (7, 8),
]

METRE_LOCATIONS = [(x * 114, y * 80) for x, y in BLOCK_LOCATIONS]
DISTANCE_MATRIX = [
    [0, 548, 776, 696, 582, 274, 502, 194, 308, 194, 536, 502, 388, 354, 468, 776, 662],
    [548, 0, 684, 308, 194, 502, 730, 354, 696, 742, 1084, 594, 480, 674, 1016, 868, 1210],
    [776, 684, 0, 992, 878, 502, 274, 810, 468, 742, 400, 1278, 1164, 1130, 788, 1552, 754],
    [696, 308, 992, 0, 114, 650, 878, 502, 844, 890, 1232, 514, 628, 822, 1164, 560, 1358],
    [582, 194, 878, 114, 0, 536, 764, 388, 730, 776, 1118, 400, 514, 708, 1050, 674, 1244],
    [274, 502, 502, 650, 536, 0, 228, 308, 194, 240, 582, 776, 662, 628, 514, 1050, 708],
    [502, 730, 274, 878, 764, 228, 0, 536, 194, 468, 354, 1004, 890, 856, 514, 1278, 480],
    [194, 354, 810, 502, 388, 308, 536, 0, 342, 388, 730, 468, 354, 320, 662, 742, 856],
    [308, 696, 468, 844, 730, 194, 194, 342, 0, 274, 388, 810, 696, 662, 320, 1084, 514],
    [194, 742, 742, 890, 776, 240, 468, 388, 274, 0, 342, 536, 422, 388, 274, 810, 468],
    [536, 1084, 400, 1232, 1118, 582, 354, 730, 388, 342, 0, 878, 764, 730, 388, 1152, 354],
    [502, 594, 1278, 514, 400, 776, 1004, 468, 810, 536, 878, 0, 114, 308, 650, 274, 844],
    [388, 480, 1164, 628, 514, 662, 890, 354, 696, 422, 764, 114, 0, 194, 536, 388, 730],
    [354, 674, 1130, 822, 708, 628, 856, 320, 662, 388, 730, 308, 194, 0, 342, 422, 536],
    [468, 1016, 788, 1164, 1050, 514, 514, 662, 320, 274, 388, 650, 536, 342, 0, 764, 194],
    [776, 868, 1552, 560, 674, 1050, 1278, 742, 1084, 810, 1152, 274, 388, 422, 764, 0, 798],
    [662, 1210, 754, 1358, 1244, 708, 480, 856, 514, 468, 354, 844, 730, 536, 194, 798, 0],
]

TIME_MATRIX = [
    [0, 6, 9, 8, 7, 3, 6, 2, 3, 2, 6, 6, 4, 4, 5, 9, 7],
    [6, 0, 8, 3, 2, 6, 8, 4, 8, 8, 13, 7, 5, 10, 12, 10, 14],
    [9, 8, 0, 11, 10, 6, 3, 9, 5, 8, 4, 15, 13, 14, 8, 16, 8],
    [8, 3, 11, 0, 1, 7, 10, 6, 10, 10, 14, 6, 7, 9, 13, 9, 15],
    [7, 2, 10, 1, 0, 6, 9, 4, 8, 9, 13, 4, 6, 8, 12, 8, 14],
    [3, 6, 6, 7, 6, 0, 2, 3, 2, 2, 7, 8, 7, 7, 4, 10, 7],
    [6, 8, 3, 10, 9, 2, 0, 6, 2, 5, 4, 11, 10, 10, 5, 13, 4],
    [2, 4, 9, 6, 4, 3, 6, 0, 4, 4, 8, 5, 4, 6, 7, 8, 10],
    [3, 8, 5, 10, 8, 2, 2, 4, 0, 3, 4, 9, 9, 9, 3, 12, 5],
    [2, 8, 8, 10, 9, 2, 5, 4, 3, 0, 4, 6, 5, 4, 3, 9, 5],
    [6, 13, 4, 14, 13, 7, 4, 8, 4, 4, 0, 12, 12, 10, 6, 14, 3],
    [6, 7, 15, 6, 4, 8, 11, 5, 9, 6, 12, 0, 1, 4, 10, 4, 12],
    [4, 5, 13, 7, 6, 7, 10, 4, 9, 5, 12, 1, 0, 2, 8, 4, 11],
    [4, 10, 14, 9, 8, 7, 10, 6, 9, 4, 10, 4, 2, 0, 6, 5, 9],
    [5, 12, 8, 13, 12, 4, 5, 7, 3, 3, 6, 10, 8, 6, 0, 9, 4],
    [9, 10, 16, 9, 8, 10, 13, 8, 12, 9, 14, 4, 4, 5, 9, 0, 9],
    [7, 14, 8, 15, 14, 7, 4, 10, 5, 5, 3, 12, 11, 9, 4, 9, 0],
]

DEMANDS = [0, 1, 1, 2, 4, 2, 4, 8, 8, 1, 2, 1, 2, 4, 4, 8, 8]
VEHICLE_CAPACITIES = [15, 15, 15, 15]
TIME_WINDOWS = [
    (0, 5),
    (7, 12),
    (10, 15),
    (16, 18),
    (10, 13),
    (0, 5),
    (5, 10),
    (0, 4),
    (5, 10),
    (0, 3),
    (10, 16),
    (10, 15),
    (0, 5),
    (5, 10),
    (7, 8),
    (10, 15),
    (11, 15),
]

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def default_search_parameters() -> pywrapcp.RoutingSearchParameters:
    parameters = pywrapcp.DefaultRoutingSearchParameters()
    parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    return parameters


def extract_routes(manager, routing, solution, matrix, dimension=None):
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
                cumul.append(
                    [solution.Min(time_var), solution.Max(time_var)]
                )
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )
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


def solve_tsp():
    manager = pywrapcp.RoutingIndexManager(len(METRE_LOCATIONS), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return DISTANCE_MATRIX[
            manager.IndexToNode(from_index)
        ][manager.IndexToNode(to_index)]

    transit = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    solution = routing.SolveWithParameters(default_search_parameters())
    if solution is None:
        raise RuntimeError("TSP baseline did not find a solution")
    routes = extract_routes(manager, routing, solution, DISTANCE_MATRIX)
    return {
        "problem": "TSP",
        "objective": solution.ObjectiveValue(),
        "objective_interpretation": "total distance (m)",
        "routes": routes,
    }


def solve_vrp():
    manager = pywrapcp.RoutingIndexManager(len(DISTANCE_MATRIX), 4, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return DISTANCE_MATRIX[
            manager.IndexToNode(from_index)
        ][manager.IndexToNode(to_index)]

    transit = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    routing.AddDimension(transit, 0, 3000, True, "Distance")
    routing.GetDimensionOrDie("Distance").SetGlobalSpanCostCoefficient(100)
    solution = routing.SolveWithParameters(default_search_parameters())
    if solution is None:
        raise RuntimeError("VRP baseline did not find a solution")
    routes = extract_routes(manager, routing, solution, DISTANCE_MATRIX)
    return {
        "problem": "VRP",
        "objective": solution.ObjectiveValue(),
        "objective_interpretation": (
            "total distance + 100 x longest-route distance"
        ),
        "total_distance": sum(route["distance"] for route in routes),
        "maximum_route_distance": max(route["distance"] for route in routes),
        "routes": routes,
    }


def solve_cvrp():
    manager = pywrapcp.RoutingIndexManager(
        len(DISTANCE_MATRIX), len(VEHICLE_CAPACITIES), 0
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return DISTANCE_MATRIX[
            manager.IndexToNode(from_index)
        ][manager.IndexToNode(to_index)]

    def demand_callback(from_index):
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
    routes = extract_routes(manager, routing, solution, DISTANCE_MATRIX)
    for route in routes:
        route["load"] = sum(DEMANDS[node] for node in route["nodes"])
    return {
        "problem": "CVRP",
        "objective": solution.ObjectiveValue(),
        "objective_interpretation": "total distance (m)",
        "total_distance": sum(route["distance"] for route in routes),
        "routes": routes,
    }


def solve_vrptw():
    manager = pywrapcp.RoutingIndexManager(len(TIME_MATRIX), 4, 0)
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        return TIME_MATRIX[
            manager.IndexToNode(from_index)
        ][manager.IndexToNode(to_index)]

    transit = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    routing.AddDimension(transit, 30, 30, False, "Time")
    time_dimension = routing.GetDimensionOrDie("Time")
    for node, time_window in enumerate(TIME_WINDOWS):
        if node == 0:
            continue
        index = manager.NodeToIndex(node)
        time_dimension.CumulVar(index).SetRange(*time_window)
    for vehicle_id in range(4):
        start_index = routing.Start(vehicle_id)
        time_dimension.CumulVar(start_index).SetRange(*TIME_WINDOWS[0])
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(start_index)
        )
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.End(vehicle_id))
        )
    solution = routing.SolveWithParameters(default_search_parameters())
    if solution is None:
        raise RuntimeError("VRPTW baseline did not find a solution")
    routes = extract_routes(
        manager, routing, solution, TIME_MATRIX, time_dimension
    )
    return {
        "problem": "VRPTW",
        "objective": solution.ObjectiveValue(),
        "objective_interpretation": "total travel time",
        "total_travel_time": sum(route["distance"] for route in routes),
        "routes": routes,
    }


def plot_results(results):
    colors = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 11), constrained_layout=True)
    for ax, result in zip(axes.flat, results):
        for route_index, route in enumerate(result["routes"]):
            points = [BLOCK_LOCATIONS[node] for node in route["nodes"]]
            xs, ys = zip(*points)
            ax.plot(
                xs,
                ys,
                marker="o",
                linewidth=2,
                color=colors[route_index % len(colors)],
                label=f"Vehicle {route['vehicle']}",
            )
        for node, (x, y) in enumerate(BLOCK_LOCATIONS):
            marker = "s" if node == 0 else "o"
            color = "black" if node == 0 else "white"
            ax.scatter(
                x, y, marker=marker, s=75, facecolor=color,
                edgecolor="black", zorder=5
            )
            ax.annotate(
                str(node), (x, y), xytext=(5, 5),
                textcoords="offset points", fontsize=9
            )
        ax.set_title(result["problem"])
        ax.set_xlabel("x-coordinate (block units)")
        ax.set_ylabel("y-coordinate (block units)")
        ax.grid(alpha=0.25)
        ax.set_aspect("equal", adjustable="box")
        ax.legend(loc="best", fontsize=8)
    fig.suptitle("Google OR-Tools Routing Baselines", fontsize=16)
    fig.savefig(RESULTS_DIR / "baseline_routes.png", dpi=180)
    plt.close(fig)


def write_route_tables(results):
    lines = [
        "# OR-Tools Baseline Route Tables",
        "",
        "Generated by `run_baselines.py` using OR-Tools "
        f"`{__import__('ortools').__version__}`.",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"## {result['problem']}",
                "",
                f"- Solver objective: `{result['objective']}` "
                f"({result['objective_interpretation']})",
            ]
        )
        if "total_distance" in result:
            lines.append(
                f"- Total route distance: `{result['total_distance']} m`"
            )
        if "maximum_route_distance" in result:
            lines.append(
                "- Maximum route distance: "
                f"`{result['maximum_route_distance']} m`"
            )
        lines.extend(
            [
                "",
                "| Vehicle | Route | Distance / travel time | Load | "
                "Service-time ranges |",
                "|---:|---|---:|---:|---|",
            ]
        )
        for route in result["routes"]:
            route_text = " -> ".join(map(str, route["nodes"]))
            load = route.get("load", "-")
            times = route.get("cumulative_time")
            time_text = (
                "; ".join(
                    f"{node}: [{bounds[0]}, {bounds[1]}]"
                    for node, bounds in zip(route["nodes"], times)
                )
                if times
                else "-"
            )
            lines.append(
                f"| {route['vehicle']} | `{route_text}` | "
                f"{route['distance']} | {load} | {time_text} |"
            )
        lines.append("")
    (RESULTS_DIR / "route_tables.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results = [solve_tsp(), solve_vrp(), solve_cvrp(), solve_vrptw()]
    (RESULTS_DIR / "baseline_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    write_route_tables(results)
    plot_results(results)
    for result in results:
        print(
            f"{result['problem']}: objective={result['objective']}, "
            f"routes={len(result['routes'])}"
        )


if __name__ == "__main__":
    main()
