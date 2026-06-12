import math

import torch

from src.algorithms.baseline import greedy_solve
from src.algorithms.ppo import collect_trajectory, ppo_step
from src.algorithms.reinforce import reinforce_step
from src.models.policy_network import PolicyNetwork
from src.utils.data_loader import DataConfig, generate_batch


def tiny_batch(batch_size: int = 4):
    config = DataConfig(
        num_customers=3,
        num_stations=1,
        num_vehicles=2,
        vehicle_capacity=20,
        battery_capacity=2,
    )
    return generate_batch(batch_size, config, seed=12)


def test_greedy_baseline_returns_feasible_solutions():
    result = greedy_solve(tiny_batch())

    assert result["feasible"].all()
    assert torch.isfinite(result["cost"]).all()


def test_reinforce_updates_model():
    data = tiny_batch()
    model = PolicyNetwork(embedding_dim=32, num_heads=4, num_layers=1)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    metrics = reinforce_step(model, optimizer, data)

    assert math.isfinite(metrics["loss"])
    assert 0 <= metrics["feasibility_rate"] <= 1


def test_ppo_updates_model():
    data = tiny_batch(batch_size=2)
    model = PolicyNetwork(embedding_dim=32, num_heads=4, num_layers=1)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    metrics = ppo_step(model, optimizer, data, update_epochs=1)

    assert math.isfinite(metrics["loss"])
    assert 0 <= metrics["feasibility_rate"] <= 1


def test_ppo_records_terminal_rewards():
    data = tiny_batch(batch_size=2)
    model = PolicyNetwork(embedding_dim=32, num_heads=4, num_layers=1)

    trajectory, _, _ = collect_trajectory(model, data)

    rewards = torch.stack(trajectory.rewards)
    assert (rewards < 0).any()
