"""REINFORCE with a greedy self-critical rollout baseline."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch.distributions import Categorical

from src.env.evrp_tw_env import EVRPTWEnv
from src.models.policy_network import PolicyNetwork


@dataclass
class Rollout:
    cost: torch.Tensor
    log_probability: torch.Tensor
    entropy: torch.Tensor
    feasible: torch.Tensor
    actions: torch.Tensor


def policy_rollout(
    model: PolicyNetwork,
    data: dict[str, torch.Tensor],
    decode_type: str = "sampling",
    max_steps: int | None = None,
) -> Rollout:
    env = EVRPTWEnv(data, max_steps=max_steps)
    embeddings = model.encode(data)
    log_probabilities = []
    entropies = []
    actions = []

    for _ in range(env.max_steps):
        if env.state.done.all():
            break
        mask = env.action_mask()
        dead_end = ~env.state.done & ~mask.any(dim=1)
        env.terminate_failed(dead_end)
        mask = env.action_mask()
        logits, _ = model.decode(embeddings, data, env.state, mask)
        distribution = Categorical(logits=logits)
        action = (
            distribution.sample()
            if decode_type == "sampling"
            else logits.argmax(dim=-1)
        )
        action = torch.where(env.state.done, torch.zeros_like(action), action)
        active = (~env.state.done).float()
        log_probabilities.append(distribution.log_prob(action) * active)
        entropies.append(distribution.entropy() * active)
        actions.append(action)
        env.step(action)

    zeros = torch.zeros(data["coords"].size(0), device=data["coords"].device)
    log_probability = torch.stack(log_probabilities).sum(dim=0) if log_probabilities else zeros
    entropy = torch.stack(entropies).sum(dim=0) if entropies else zeros
    action_tensor = (
        torch.stack(actions, dim=1)
        if actions
        else torch.empty(data["coords"].size(0), 0, dtype=torch.long, device=zeros.device)
    )
    return Rollout(
        cost=env.solution_cost(),
        log_probability=log_probability,
        entropy=entropy,
        feasible=env.feasible,
        actions=action_tensor,
    )


def reinforce_step(
    model: PolicyNetwork,
    optimizer: torch.optim.Optimizer,
    data: dict[str, torch.Tensor],
    entropy_coefficient: float = 0.01,
    max_grad_norm: float = 1.0,
) -> dict[str, float]:
    model.train()
    sampled = policy_rollout(model, data, decode_type="sampling")
    with torch.no_grad():
        greedy = policy_rollout(model, data, decode_type="greedy")

    advantage = (sampled.cost - greedy.cost).detach()
    policy_loss = (advantage * sampled.log_probability).mean()
    entropy_bonus = sampled.entropy.mean()
    loss = policy_loss - entropy_coefficient * entropy_bonus

    optimizer.zero_grad()
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
    optimizer.step()

    return {
        "loss": float(loss.detach()),
        "cost": float(sampled.cost.mean().detach()),
        "baseline_cost": float(greedy.cost.mean().detach()),
        "feasibility_rate": float(sampled.feasible.float().mean()),
        "entropy": float(entropy_bonus.detach()),
        "gradient_norm": float(grad_norm),
    }
