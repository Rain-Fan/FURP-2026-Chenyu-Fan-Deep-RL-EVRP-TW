"""Batched EVRP-TW environment state."""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass
class EVRPTWState:
    current_node: torch.Tensor
    used_capacity: torch.Tensor
    battery: torch.Tensor
    time: torch.Tensor
    visited: torch.Tensor
    vehicles_used: torch.Tensor
    route_has_customer: torch.Tensor
    total_distance: torch.Tensor
    done: torch.Tensor
    failed: torch.Tensor
    step_count: int = 0

    def clone(self) -> "EVRPTWState":
        return EVRPTWState(
            current_node=self.current_node.clone(),
            used_capacity=self.used_capacity.clone(),
            battery=self.battery.clone(),
            time=self.time.clone(),
            visited=self.visited.clone(),
            vehicles_used=self.vehicles_used.clone(),
            route_has_customer=self.route_has_customer.clone(),
            total_distance=self.total_distance.clone(),
            done=self.done.clone(),
            failed=self.failed.clone(),
            step_count=self.step_count,
        )

    def to(self, device: torch.device | str) -> "EVRPTWState":
        return EVRPTWState(
            current_node=self.current_node.to(device),
            used_capacity=self.used_capacity.to(device),
            battery=self.battery.to(device),
            time=self.time.to(device),
            visited=self.visited.to(device),
            vehicles_used=self.vehicles_used.to(device),
            route_has_customer=self.route_has_customer.to(device),
            total_distance=self.total_distance.to(device),
            done=self.done.to(device),
            failed=self.failed.to(device),
            step_count=self.step_count,
        )
