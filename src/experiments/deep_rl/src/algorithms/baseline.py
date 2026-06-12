"""Deterministic feasibility-first baseline."""

from __future__ import annotations

import torch

from src.env.evrp_tw_env import CUSTOMER, DEPOT, STATION, EVRPTWEnv


@torch.no_grad()
def greedy_solve(
    data: dict[str, torch.Tensor],
    max_steps: int | None = None,
) -> dict[str, object]:
    env = EVRPTWEnv(data, max_steps=max_steps)
    routes: list[list[list[int]]] = [
        [[DEPOT]] for _ in range(data["coords"].size(0))
    ]

    for _ in range(env.max_steps):
        if env.state.done.all():
            break
        mask = env.action_mask()
        dead_end = ~env.state.done & ~mask.any(dim=1)
        env.terminate_failed(dead_end)
        mask = env.action_mask()
        batch_idx = torch.arange(env.batch_size, device=env.device)
        current = env.state.current_node
        distances = env.distances[batch_idx, current].clone()

        customer = data["node_type"].eq(CUSTOMER) & mask
        due_priority = data["due_time"] + distances * 0.1
        scores = torch.where(customer, due_priority, torch.inf)
        action = scores.argmin(dim=1)

        no_customer = ~customer.any(dim=1)
        station = data["node_type"].eq(STATION) & mask
        station_scores = torch.where(station, distances, torch.inf)
        use_station = no_customer & station.any(dim=1) & ~mask[:, DEPOT]
        action = torch.where(use_station, station_scores.argmin(dim=1), action)
        action = torch.where(no_customer & ~use_station, torch.zeros_like(action), action)
        action = torch.where(env.state.done, torch.zeros_like(action), action)

        active_before = ~env.state.done.clone()
        env.step(action)
        for batch in torch.where(active_before)[0].tolist():
            selected = int(action[batch])
            routes[batch][-1].append(selected)
            if selected == DEPOT and not env.state.done[batch]:
                routes[batch].append([DEPOT])

    return {
        "cost": env.solution_cost(),
        "distance": env.state.total_distance,
        "feasible": env.feasible,
        "vehicles_used": env.state.vehicles_used,
        "routes": routes,
    }
