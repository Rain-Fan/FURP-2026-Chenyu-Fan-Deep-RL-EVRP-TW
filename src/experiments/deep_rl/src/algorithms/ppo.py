"""Clipped PPO for the attention policy."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch.distributions import Categorical

from src.env.evrp_tw_env import EVRPTWEnv
from src.env.state import EVRPTWState
from src.models.policy_network import PolicyNetwork


@dataclass
class PPOTrajectory:
    states: list[EVRPTWState]
    masks: list[torch.Tensor]
    actions: list[torch.Tensor]
    old_log_probs: list[torch.Tensor]
    old_values: list[torch.Tensor]
    rewards: list[torch.Tensor]
    active: list[torch.Tensor]


@torch.no_grad()
def collect_trajectory(
    model: PolicyNetwork,
    data: dict[str, torch.Tensor],
    max_steps: int | None = None,
) -> tuple[PPOTrajectory, torch.Tensor, torch.Tensor]:
    env = EVRPTWEnv(data, max_steps=max_steps)
    embeddings = model.encode(data)
    trajectory = PPOTrajectory([], [], [], [], [], [], [])

    for step in range(env.max_steps):
        if env.state.done.all():
            break
        mask = env.action_mask()
        dead_end = ~env.state.done & ~mask.any(dim=1)
        if dead_end.any():
            env.terminate_failed(dead_end)
            if trajectory.rewards:
                penalty = env.solution_cost()
                trajectory.rewards[-1][dead_end] -= penalty[dead_end]
        if env.state.done.all():
            break
        state = env.state.clone()
        mask = env.action_mask()
        logits, value = model.decode(embeddings, data, state, mask)
        distribution = Categorical(logits=logits)
        action = distribution.sample()
        action = torch.where(state.done, torch.zeros_like(action), action)
        active = ~state.done
        env.step(action)

        reward = torch.zeros(env.batch_size, device=env.device)
        completed = active & env.state.done
        reward[completed] = -env.state.total_distance[completed]
        if step == env.max_steps - 1:
            unfinished = active & ~env.state.done
            reward[unfinished] = -env.solution_cost()[unfinished]

        trajectory.states.append(state)
        trajectory.masks.append(mask)
        trajectory.actions.append(action)
        trajectory.old_log_probs.append(distribution.log_prob(action))
        trajectory.old_values.append(value)
        trajectory.rewards.append(reward)
        trajectory.active.append(active)

    return trajectory, env.solution_cost(), env.feasible


def _advantages(
    trajectory: PPOTrajectory,
    gamma: float,
    gae_lambda: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    rewards = torch.stack(trajectory.rewards)
    values = torch.stack(trajectory.old_values)
    active = torch.stack(trajectory.active)
    advantages = torch.zeros_like(rewards)
    gae = torch.zeros(rewards.size(1), device=rewards.device)

    for step in reversed(range(rewards.size(0))):
        next_value = values[step + 1] if step + 1 < values.size(0) else torch.zeros_like(gae)
        next_active = active[step + 1] if step + 1 < active.size(0) else torch.zeros_like(
            active[step]
        )
        delta = rewards[step] + gamma * next_value * next_active - values[step]
        gae = delta + gamma * gae_lambda * next_active * gae
        advantages[step] = gae

    returns = advantages + values
    valid_advantages = advantages[active]
    advantages = (advantages - valid_advantages.mean()) / (
        valid_advantages.std(unbiased=False) + 1e-8
    )
    return advantages, returns


def ppo_step(
    model: PolicyNetwork,
    optimizer: torch.optim.Optimizer,
    data: dict[str, torch.Tensor],
    update_epochs: int = 4,
    clip_epsilon: float = 0.2,
    value_coefficient: float = 0.5,
    entropy_coefficient: float = 0.01,
    gamma: float = 1.0,
    gae_lambda: float = 0.95,
    max_grad_norm: float = 1.0,
) -> dict[str, float]:
    model.eval()
    trajectory, costs, feasible = collect_trajectory(model, data)
    advantages, returns = _advantages(trajectory, gamma, gae_lambda)
    old_log_probs = torch.stack(trajectory.old_log_probs)
    active = torch.stack(trajectory.active)

    last_loss = torch.tensor(0.0, device=costs.device)
    policy_value = entropy_value = value_value = 0.0
    for _ in range(update_epochs):
        model.train()
        embeddings = model.encode(data)
        new_log_probs = []
        new_values = []
        entropies = []
        for state, mask, action in zip(
            trajectory.states,
            trajectory.masks,
            trajectory.actions,
            strict=True,
        ):
            logits, value = model.decode(embeddings, data, state, mask)
            distribution = Categorical(logits=logits)
            new_log_probs.append(distribution.log_prob(action))
            new_values.append(value)
            entropies.append(distribution.entropy())

        new_log_probs_tensor = torch.stack(new_log_probs)
        values_tensor = torch.stack(new_values)
        entropy_tensor = torch.stack(entropies)
        ratio = (new_log_probs_tensor - old_log_probs).exp()
        objective = ratio * advantages
        clipped = ratio.clamp(1 - clip_epsilon, 1 + clip_epsilon) * advantages
        policy_loss = -torch.minimum(objective, clipped)[active].mean()
        value_loss = torch.nn.functional.mse_loss(values_tensor[active], returns[active])
        entropy = entropy_tensor[active].mean()
        loss = policy_loss + value_coefficient * value_loss - entropy_coefficient * entropy

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
        optimizer.step()
        last_loss = loss.detach()
        policy_value = float(policy_loss.detach())
        value_value = float(value_loss.detach())
        entropy_value = float(entropy.detach())

    return {
        "loss": float(last_loss),
        "policy_loss": policy_value,
        "value_loss": value_value,
        "entropy": entropy_value,
        "cost": float(costs.mean()),
        "feasibility_rate": float(feasible.float().mean()),
    }
