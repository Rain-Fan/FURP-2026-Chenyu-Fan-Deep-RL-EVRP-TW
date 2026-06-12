"""Route and training-history plots."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import torch


def plot_routes(
    coords: torch.Tensor,
    node_type: torch.Tensor,
    routes: list[list[int]],
    output: str | Path,
    title: str = "EVRP-TW routes",
) -> None:
    coordinates = coords.detach().cpu()
    types = node_type.detach().cpu()
    figure, axis = plt.subplots(figsize=(7, 7))
    axis.scatter(
        coordinates[types == 1, 0],
        coordinates[types == 1, 1],
        marker="o",
        label="Customer",
    )
    axis.scatter(
        coordinates[types == 2, 0],
        coordinates[types == 2, 1],
        marker="s",
        label="Charging station",
    )
    axis.scatter(
        coordinates[0, 0],
        coordinates[0, 1],
        marker="*",
        s=180,
        label="Depot",
    )
    colors = plt.cm.tab10.colors
    for route_idx, route in enumerate(routes):
        points = coordinates[route]
        axis.plot(points[:, 0], points[:, 1], color=colors[route_idx % len(colors)])
        for node in route:
            axis.annotate(str(node), coordinates[node], xytext=(4, 4), textcoords="offset points")
    axis.set_title(title)
    axis.set_aspect("equal")
    axis.legend()
    axis.grid(alpha=0.2)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(figure)


def plot_training_history(history: list[dict[str, float]], output: str | Path) -> None:
    steps = range(1, len(history) + 1)
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(steps, [row["cost"] for row in history])
    axes[0].set_title("Training cost")
    axes[0].set_xlabel("Iteration")
    axes[0].set_ylabel("Mean cost")
    axes[1].plot(steps, [row["feasibility_rate"] for row in history])
    axes[1].set_title("Feasibility rate")
    axes[1].set_xlabel("Iteration")
    axes[1].set_ylim(0, 1.05)
    for axis in axes:
        axis.grid(alpha=0.2)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(figure)
