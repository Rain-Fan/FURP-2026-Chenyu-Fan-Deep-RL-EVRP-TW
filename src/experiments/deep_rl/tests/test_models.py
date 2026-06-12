import torch

from src.env.evrp_tw_env import EVRPTWEnv
from src.models.policy_network import PolicyNetwork
from src.utils.data_loader import DataConfig, generate_batch


def test_policy_outputs_masked_logits_and_values():
    data = generate_batch(2, DataConfig(num_customers=4, num_stations=1), seed=3)
    env = EVRPTWEnv(data)
    mask = env.action_mask()
    model = PolicyNetwork(embedding_dim=32, num_heads=4, num_layers=1)

    logits, values = model(data, env.state, mask)

    assert logits.shape == (2, 6)
    assert values.shape == (2,)
    assert torch.isfinite(logits[mask]).all()
    assert (logits[~mask] < -1e20).all()
