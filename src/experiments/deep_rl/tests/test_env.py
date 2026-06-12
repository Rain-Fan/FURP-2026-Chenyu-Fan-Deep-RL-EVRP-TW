import torch

from src.env.evrp_tw_env import EVRPTWEnv


def small_instance() -> dict[str, torch.Tensor]:
    return {
        "coords": torch.tensor([[[0.0, 0.0], [1.0, 0.0], [0.5, 0.0]]]),
        "node_type": torch.tensor([[0, 1, 2]]),
        "demand": torch.tensor([[0.0, 2.0, 0.0]]),
        "ready_time": torch.zeros(1, 3),
        "due_time": torch.full((1, 3), 10.0),
        "service_time": torch.zeros(1, 3),
        "vehicle_capacity": torch.tensor([3.0]),
        "battery_capacity": torch.tensor([1.0]),
        "energy_rate": torch.tensor([1.0]),
        "speed": torch.tensor([1.0]),
        "charging_rate": torch.tensor([2.0]),
        "num_vehicles": torch.tensor([1]),
        "time_horizon": torch.tensor([10.0]),
    }


def test_station_enables_energy_feasible_route():
    env = EVRPTWEnv(small_instance())

    assert env.action_mask()[0].tolist() == [False, False, True]
    env.step(torch.tensor([2]))
    assert env.state.battery.item() == 1.0
    assert env.action_mask()[0, 1]
    env.step(torch.tensor([1]))
    env.step(torch.tensor([2]))
    env.step(torch.tensor([0]))

    assert env.state.done.item()
    assert env.state.visited[0, 1].item()


def test_capacity_masks_customer():
    data = small_instance()
    data["vehicle_capacity"] = torch.tensor([1.0])
    env = EVRPTWEnv(data)

    env.step(torch.tensor([2]))

    assert not env.action_mask()[0, 1]
