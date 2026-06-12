"""Synthetic EVRP-TW generation and dataset persistence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
import torch


@dataclass(frozen=True)
class DataConfig:
    num_customers: int = 10
    num_stations: int = 2
    num_vehicles: int = 3
    vehicle_capacity: float = 30.0
    battery_capacity: float = 2.0
    energy_rate: float = 1.0
    speed: float = 1.0
    charging_rate: float = 2.0
    service_time: float = 0.05
    time_horizon: float = 5.0
    time_window_width: float = 2.5
    demand_min: int = 1
    demand_max: int = 9


def generate_batch(
    batch_size: int,
    config: DataConfig,
    device: torch.device | str = "cpu",
    seed: int | None = None,
) -> dict[str, torch.Tensor]:
    generator = torch.Generator(device="cpu")
    if seed is not None:
        generator.manual_seed(seed)

    customers = config.num_customers
    stations = config.num_stations
    nodes = 1 + customers + stations
    coords = torch.rand(batch_size, nodes, 2, generator=generator)
    coords[:, 0] = 0.5

    node_type = torch.ones(batch_size, nodes, dtype=torch.long)
    node_type[:, 0] = 0
    if stations:
        node_type[:, -stations:] = 2
        angles = torch.linspace(0, 2 * torch.pi, stations + 1)[:-1]
        station_coords = torch.stack(
            (0.5 + 0.22 * torch.cos(angles), 0.5 + 0.22 * torch.sin(angles)),
            dim=-1,
        )
        coords[:, -stations:] = station_coords

    demand = torch.zeros(batch_size, nodes)
    demand[:, 1 : customers + 1] = torch.randint(
        config.demand_min,
        config.demand_max + 1,
        (batch_size, customers),
        generator=generator,
    ).float()

    depot_distance = torch.linalg.vector_norm(coords - coords[:, :1], dim=-1)
    ready_time = torch.zeros(batch_size, nodes)
    random_offset = torch.rand(batch_size, customers, generator=generator) * 0.5
    ready_time[:, 1 : customers + 1] = depot_distance[:, 1 : customers + 1] + random_offset
    due_time = torch.full((batch_size, nodes), config.time_horizon)
    due_time[:, 1 : customers + 1] = torch.clamp(
        ready_time[:, 1 : customers + 1] + config.time_window_width,
        max=config.time_horizon,
    )
    service_time = torch.zeros(batch_size, nodes)
    service_time[:, 1 : customers + 1] = config.service_time

    scalar = lambda value, dtype=torch.float32: torch.full(  # noqa: E731
        (batch_size,), value, dtype=dtype
    )
    data = {
        "coords": coords,
        "node_type": node_type,
        "demand": demand,
        "ready_time": ready_time,
        "due_time": due_time,
        "service_time": service_time,
        "vehicle_capacity": scalar(config.vehicle_capacity),
        "battery_capacity": scalar(config.battery_capacity),
        "energy_rate": scalar(config.energy_rate),
        "speed": scalar(config.speed),
        "charging_rate": scalar(config.charging_rate),
        "num_vehicles": scalar(config.num_vehicles, torch.long),
        "time_horizon": scalar(config.time_horizon),
    }
    return {key: value.to(device) for key, value in data.items()}


def save_dataset(
    path: str | Path,
    batches: list[dict[str, torch.Tensor]],
    config: DataConfig,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    arrays = {
        key: torch.cat([batch[key].cpu() for batch in batches]).numpy()
        for key in batches[0]
    }
    arrays["config"] = np.asarray(asdict(config), dtype=object)
    np.savez_compressed(output, **arrays)


def load_dataset(
    path: str | Path,
    device: torch.device | str = "cpu",
) -> dict[str, torch.Tensor]:
    with np.load(path, allow_pickle=True) as archive:
        return {
            key: torch.from_numpy(archive[key]).to(device)
            for key in archive.files
            if key != "config"
        }


def iter_minibatches(
    data: dict[str, torch.Tensor],
    batch_size: int,
    shuffle: bool = True,
) -> Iterator[dict[str, torch.Tensor]]:
    size = data["coords"].size(0)
    indices = torch.randperm(size, device=data["coords"].device) if shuffle else torch.arange(
        size, device=data["coords"].device
    )
    for start in range(0, size, batch_size):
        selected = indices[start : start + batch_size]
        yield {key: value[selected] for key, value in data.items()}
