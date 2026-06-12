"""Vectorised EVRP-TW construction environment."""

from __future__ import annotations

from typing import Any

import torch

from src.env.state import EVRPTWState

DEPOT = 0
CUSTOMER = 1
STATION = 2
EPS = 1e-7


class EVRPTWEnv:
    """Constructs routes while enforcing capacity, time, energy, and fleet limits.

    The depot and charging stations restore the battery to full. Returning to
    the depot before all customers are served starts a new vehicle route and
    resets capacity and route time.
    """

    def __init__(self, data: dict[str, torch.Tensor], max_steps: int | None = None):
        self.data = data
        self.device = data["coords"].device
        self.batch_size, self.num_nodes, _ = data["coords"].shape
        self.max_steps = max_steps or self.num_nodes * 4
        self.distances = torch.cdist(data["coords"], data["coords"], p=2)
        self.state = self.reset()

    def reset(self) -> EVRPTWState:
        batch = self.batch_size
        self.state = EVRPTWState(
            current_node=torch.zeros(batch, dtype=torch.long, device=self.device),
            used_capacity=torch.zeros(batch, device=self.device),
            battery=self.data["battery_capacity"].clone(),
            time=torch.zeros(batch, device=self.device),
            visited=self.data["node_type"].ne(CUSTOMER),
            vehicles_used=torch.ones(batch, dtype=torch.long, device=self.device),
            route_has_customer=torch.zeros(batch, dtype=torch.bool, device=self.device),
            total_distance=torch.zeros(batch, device=self.device),
            done=torch.zeros(batch, dtype=torch.bool, device=self.device),
            failed=torch.zeros(batch, dtype=torch.bool, device=self.device),
        )
        return self.state

    @property
    def all_customers_served(self) -> torch.Tensor:
        customer_mask = self.data["node_type"].eq(CUSTOMER)
        return (self.state.visited | ~customer_mask).all(dim=1)

    @property
    def feasible(self) -> torch.Tensor:
        return self.state.done & ~self.state.failed & self.all_customers_served

    def terminate_failed(self, failed: torch.Tensor) -> None:
        failed = failed.to(self.device, dtype=torch.bool) & ~self.state.done
        self.state.failed |= failed
        self.state.done |= failed

    def _gather(self, values: torch.Tensor, indices: torch.Tensor) -> torch.Tensor:
        return values.gather(1, indices[:, None]).squeeze(1)

    def action_mask(self, state: EVRPTWState | None = None) -> torch.Tensor:
        state = state or self.state
        batch_idx = torch.arange(self.batch_size, device=self.device)
        current = state.current_node
        node_type = self.data["node_type"]
        customer = node_type.eq(CUSTOMER)
        station = node_type.eq(STATION)

        travel = self.distances[batch_idx, current]
        energy = travel * self.data["energy_rate"][:, None]
        arrival = state.time[:, None] + travel / self.data["speed"][:, None]
        service_start = torch.maximum(arrival, self.data["ready_time"])
        battery_after = state.battery[:, None] - energy

        mask = battery_after.ge(-EPS)
        mask &= service_start.le(self.data["due_time"] + EPS)
        mask &= torch.arange(self.num_nodes, device=self.device)[None, :].ne(current[:, None])

        remaining = self.data["vehicle_capacity"] - state.used_capacity
        customer_ok = ~state.visited
        customer_ok &= self.data["demand"].le(remaining[:, None] + EPS)

        recharge_mask = node_type.ne(CUSTOMER)
        distance_to_recharge = self.distances.masked_fill(
            ~recharge_mask[:, None, :],
            torch.inf,
        )
        reserve = distance_to_recharge.min(dim=2).values
        reserve_energy = reserve * self.data["energy_rate"][:, None]
        customer_ok &= battery_after.ge(reserve_energy - EPS)
        mask &= ~customer | customer_ok

        station_ok = battery_after.lt(self.data["battery_capacity"][:, None] - EPS)
        mask &= ~station | station_ok

        all_served = (state.visited | ~customer).all(dim=1)
        can_open_vehicle = state.vehicles_used.lt(self.data["num_vehicles"])
        depot_ok = state.route_has_customer & (all_served | can_open_vehicle)
        mask[:, DEPOT] = depot_ok

        mask[state.done] = False
        mask[state.done, DEPOT] = True
        return mask

    def step(self, action: torch.Tensor) -> tuple[EVRPTWState, torch.Tensor, torch.Tensor]:
        action = action.to(self.device, dtype=torch.long)
        active = ~self.state.done
        mask = self.action_mask()
        valid = mask.gather(1, action[:, None]).squeeze(1)
        if not torch.all(valid | ~active):
            bad = torch.where(active & ~valid)[0].tolist()
            raise ValueError(f"Infeasible actions for batch indices: {bad}")

        batch_idx = torch.arange(self.batch_size, device=self.device)
        current = self.state.current_node
        travel = self.distances[batch_idx, current, action]
        travel = torch.where(active, travel, torch.zeros_like(travel))
        energy = travel * self.data["energy_rate"]
        arrival = self.state.time + travel / self.data["speed"]
        ready = self._gather(self.data["ready_time"], action)
        service = self._gather(self.data["service_time"], action)
        target_type = self._gather(self.data["node_type"], action)

        self.state.total_distance += travel
        self.state.battery -= energy
        self.state.time = torch.maximum(arrival, ready) + service
        self.state.current_node = torch.where(active, action, current)

        is_customer = active & target_type.eq(CUSTOMER)
        is_station = active & target_type.eq(STATION)
        is_depot = active & target_type.eq(DEPOT)
        demand = self._gather(self.data["demand"], action)

        self.state.used_capacity += torch.where(
            is_customer, demand, torch.zeros_like(demand)
        )
        self.state.visited[batch_idx[is_customer], action[is_customer]] = True
        self.state.route_has_customer |= is_customer

        charge_needed = self.data["battery_capacity"] - self.state.battery
        charge_time = charge_needed / self.data["charging_rate"]
        self.state.time += torch.where(is_station, charge_time, torch.zeros_like(charge_time))
        self.state.battery = torch.where(
            is_station, self.data["battery_capacity"], self.state.battery
        )

        served_after = self.all_customers_served
        completed = is_depot & served_after
        new_route = is_depot & ~served_after
        self.state.done |= completed
        self.state.vehicles_used += new_route.long()
        self.state.used_capacity = torch.where(
            new_route, torch.zeros_like(self.state.used_capacity), self.state.used_capacity
        )
        self.state.battery = torch.where(
            new_route, self.data["battery_capacity"], self.state.battery
        )
        self.state.time = torch.where(new_route, torch.zeros_like(self.state.time), self.state.time)
        self.state.route_has_customer &= ~new_route
        self.state.step_count += 1

        reward = -travel
        return self.state, reward, self.state.done.clone()

    def solution_cost(self, unfinished_penalty: float = 100.0) -> torch.Tensor:
        unfinished = (~self.feasible).float()
        unserved = (
            self.data["node_type"].eq(CUSTOMER) & ~self.state.visited
        ).sum(dim=1)
        return self.state.total_distance + unfinished * (
            unfinished_penalty + unserved.float() * 10.0
        )

    def state_dict(self) -> dict[str, Any]:
        return {
            "current_node": self.state.current_node,
            "used_capacity": self.state.used_capacity,
            "battery": self.state.battery,
            "time": self.state.time,
            "visited": self.state.visited,
            "vehicles_used": self.state.vehicles_used,
            "done": self.state.done,
            "failed": self.state.failed,
        }
