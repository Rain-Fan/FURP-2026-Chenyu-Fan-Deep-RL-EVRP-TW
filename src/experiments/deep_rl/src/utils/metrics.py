"""Evaluation metrics and JSON-safe summaries."""

from __future__ import annotations

from typing import Any

import torch


def summarize(
    cost: torch.Tensor,
    feasible: torch.Tensor,
    distance: torch.Tensor | None = None,
    vehicles_used: torch.Tensor | None = None,
) -> dict[str, float]:
    result = {
        "mean_cost": float(cost.float().mean()),
        "std_cost": float(cost.float().std(unbiased=False)),
        "feasibility_rate": float(feasible.float().mean()),
    }
    if feasible.any():
        result["mean_feasible_cost"] = float(cost[feasible].float().mean())
    else:
        result["mean_feasible_cost"] = float("nan")
    if distance is not None:
        result["mean_distance"] = float(distance.float().mean())
    if vehicles_used is not None:
        result["mean_vehicles_used"] = float(vehicles_used.float().mean())
    return result


def detach_record(record: dict[str, Any]) -> dict[str, Any]:
    converted = {}
    for key, value in record.items():
        if isinstance(value, torch.Tensor):
            converted[key] = value.detach().cpu().tolist()
        else:
            converted[key] = value
    return converted
