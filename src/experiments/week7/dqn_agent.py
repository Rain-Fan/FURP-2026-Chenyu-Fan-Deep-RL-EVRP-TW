#!/usr/bin/env python3
"""Small deterministic NumPy Double DQN used by the Week 7 prototype."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


def _finite_array(value, shape: tuple[int, ...] | None = None, name: str = "array") -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if shape is not None and array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {array.shape}")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    return array


def compute_double_dqn_targets(
    rewards: np.ndarray,
    dones: np.ndarray,
    online_next_q: np.ndarray,
    target_next_q: np.ndarray,
    gamma: float,
) -> np.ndarray:
    """Select next actions online and evaluate them with the target network."""

    rewards = _finite_array(rewards, name="rewards")
    dones = np.asarray(dones, dtype=bool)
    online_next_q = _finite_array(online_next_q, name="online next Q")
    target_next_q = _finite_array(target_next_q, name="target next Q")
    if rewards.ndim != 1 or dones.shape != rewards.shape:
        raise ValueError("rewards and dones must be same-length vectors")
    if online_next_q.shape != target_next_q.shape or online_next_q.shape[0] != len(rewards):
        raise ValueError("next-Q matrices must match each other and the batch")
    if not 0.0 <= gamma <= 1.0:
        raise ValueError("gamma must be between zero and one")
    actions = np.argmax(online_next_q, axis=1)
    bootstrap = target_next_q[np.arange(len(rewards)), actions]
    return rewards + gamma * (~dones) * bootstrap


class ReplayBuffer:
    def __init__(self, capacity: int, state_dim: int, *, seed: int):
        if capacity <= 0 or state_dim <= 0:
            raise ValueError("capacity and state_dim must be positive")
        self.capacity = int(capacity)
        self.state_dim = int(state_dim)
        self.rng = np.random.default_rng(seed)
        self.states = np.zeros((capacity, state_dim), dtype=np.float64)
        self.actions = np.zeros(capacity, dtype=np.int64)
        self.rewards = np.zeros(capacity, dtype=np.float64)
        self.next_states = np.zeros((capacity, state_dim), dtype=np.float64)
        self.dones = np.zeros(capacity, dtype=bool)
        self.position = 0
        self.size = 0

    def add(self, state, action: int, reward: float, next_state, done: bool) -> None:
        state = _finite_array(state, (self.state_dim,), "state")
        next_state = _finite_array(next_state, (self.state_dim,), "next state")
        if not isinstance(action, (int, np.integer)) or int(action) < 0:
            raise ValueError("action must be a nonnegative integer")
        if not math.isfinite(float(reward)):
            raise ValueError("reward must be finite")
        index = self.position
        self.states[index] = state
        self.actions[index] = int(action)
        self.rewards[index] = float(reward)
        self.next_states[index] = next_state
        self.dones[index] = bool(done)
        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size: int) -> dict[str, np.ndarray]:
        if self.size == 0:
            raise ValueError("cannot sample an empty replay buffer")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        indices = self.rng.choice(self.size, size=min(batch_size, self.size), replace=False)
        return {
            "states": self.states[indices].copy(),
            "actions": self.actions[indices].copy(),
            "rewards": self.rewards[indices].copy(),
            "next_states": self.next_states[indices].copy(),
            "dones": self.dones[indices].copy(),
        }

    def __len__(self) -> int:
        return self.size


@dataclass
class QNetwork:
    state_dim: int
    hidden_dim: int
    action_dim: int
    parameters: dict[str, np.ndarray]

    @classmethod
    def initialize(cls, state_dim: int, hidden_dim: int, action_dim: int, rng) -> "QNetwork":
        if min(state_dim, hidden_dim, action_dim) <= 0:
            raise ValueError("network dimensions must be positive")
        w1_scale = math.sqrt(2.0 / state_dim)
        w2_scale = math.sqrt(2.0 / hidden_dim)
        return cls(
            state_dim,
            hidden_dim,
            action_dim,
            {
                "w1": rng.normal(0.0, w1_scale, size=(state_dim, hidden_dim)),
                "b1": np.zeros(hidden_dim, dtype=np.float64),
                "w2": rng.normal(0.0, w2_scale, size=(hidden_dim, action_dim)),
                "b2": np.zeros(action_dim, dtype=np.float64),
            },
        )

    def forward(self, states, *, cache: bool = False):
        states = _finite_array(states, name="states")
        single = states.ndim == 1
        if single:
            states = states[None, :]
        if states.ndim != 2 or states.shape[1] != self.state_dim:
            raise ValueError(f"states must have trailing dimension {self.state_dim}")
        z1 = states @ self.parameters["w1"] + self.parameters["b1"]
        hidden = np.maximum(z1, 0.0)
        q_values = hidden @ self.parameters["w2"] + self.parameters["b2"]
        if not np.isfinite(q_values).all():
            raise ValueError("network produced nonfinite Q values")
        output = q_values[0] if single else q_values
        if cache:
            return output, (states, z1, hidden)
        return output

    def copy_from(self, other: "QNetwork") -> None:
        if (self.state_dim, self.hidden_dim, self.action_dim) != (other.state_dim, other.hidden_dim, other.action_dim):
            raise ValueError("network dimensions do not match")
        for name in self.parameters:
            self.parameters[name][...] = other.parameters[name]


class DQNAgent:
    def __init__(
        self,
        *,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 32,
        seed: int = 0,
        replay_capacity: int = 5000,
        learning_rate: float = 0.001,
        gamma: float = 0.95,
        target_sync: int = 100,
        gradient_clip: float = 5.0,
    ):
        if learning_rate <= 0.0 or target_sync <= 0 or gradient_clip <= 0.0:
            raise ValueError("learning_rate, target_sync, and gradient_clip must be positive")
        if not 0.0 <= gamma <= 1.0:
            raise ValueError("gamma must be between zero and one")
        self.state_dim = int(state_dim)
        self.action_dim = int(action_dim)
        self.hidden_dim = int(hidden_dim)
        self.seed = int(seed)
        self.learning_rate = float(learning_rate)
        self.gamma = float(gamma)
        self.target_sync = int(target_sync)
        self.gradient_clip = float(gradient_clip)
        self.rng = np.random.default_rng(seed)
        self.online = QNetwork.initialize(state_dim, hidden_dim, action_dim, self.rng)
        self.target = QNetwork.initialize(state_dim, hidden_dim, action_dim, self.rng)
        self.target.copy_from(self.online)
        self.replay = ReplayBuffer(replay_capacity, state_dim, seed=seed + 1)
        self.train_steps = 0
        self._adam_m = {name: np.zeros_like(value) for name, value in self.online.parameters.items()}
        self._adam_v = {name: np.zeros_like(value) for name, value in self.online.parameters.items()}

    def q_values(self, state) -> np.ndarray:
        return np.asarray(self.online.forward(state), dtype=np.float64)

    def select_action(self, state, *, epsilon: float = 0.0) -> int:
        state = _finite_array(state, (self.state_dim,), "state")
        if not 0.0 <= epsilon <= 1.0:
            raise ValueError("epsilon must be between zero and one")
        if self.rng.random() < epsilon:
            return int(self.rng.integers(self.action_dim))
        return int(np.argmax(self.online.forward(state)))

    def observe(self, state, action: int, reward: float, next_state, done: bool) -> None:
        if not 0 <= int(action) < self.action_dim:
            raise ValueError("action is outside the action space")
        self.replay.add(state, int(action), reward, next_state, done)

    def train_step(self, *, batch_size: int = 32) -> float | None:
        if len(self.replay) < batch_size:
            return None
        batch = self.replay.sample(batch_size)
        q_values, cache = self.online.forward(batch["states"], cache=True)
        online_next = self.online.forward(batch["next_states"])
        target_next = self.target.forward(batch["next_states"])
        targets = compute_double_dqn_targets(
            batch["rewards"], batch["dones"], online_next, target_next, self.gamma
        )
        chosen = q_values[np.arange(len(targets)), batch["actions"]]
        errors = chosen - targets
        abs_errors = np.abs(errors)
        loss = float(np.mean(np.where(abs_errors <= 1.0, 0.5 * errors**2, abs_errors - 0.5)))

        grad_q = np.zeros_like(q_values)
        grad_q[np.arange(len(targets)), batch["actions"]] = np.clip(errors, -1.0, 1.0) / len(targets)
        states, z1, hidden = cache
        gradients = {
            "w2": hidden.T @ grad_q,
            "b2": grad_q.sum(axis=0),
        }
        grad_hidden = grad_q @ self.online.parameters["w2"].T
        grad_z1 = grad_hidden * (z1 > 0.0)
        gradients["w1"] = states.T @ grad_z1
        gradients["b1"] = grad_z1.sum(axis=0)
        norm = math.sqrt(sum(float(np.sum(gradient**2)) for gradient in gradients.values()))
        if not math.isfinite(norm):
            raise ValueError("gradient norm is nonfinite")
        scale = min(1.0, self.gradient_clip / max(norm, 1e-12))
        self.train_steps += 1
        beta1, beta2 = 0.9, 0.999
        for name, gradient in gradients.items():
            gradient *= scale
            self._adam_m[name] = beta1 * self._adam_m[name] + (1.0 - beta1) * gradient
            self._adam_v[name] = beta2 * self._adam_v[name] + (1.0 - beta2) * (gradient**2)
            m_hat = self._adam_m[name] / (1.0 - beta1**self.train_steps)
            v_hat = self._adam_v[name] / (1.0 - beta2**self.train_steps)
            self.online.parameters[name] -= self.learning_rate * m_hat / (np.sqrt(v_hat) + 1e-8)
            if not np.isfinite(self.online.parameters[name]).all():
                raise ValueError("model parameters became nonfinite")
        if self.train_steps % self.target_sync == 0:
            self.target.copy_from(self.online)
        return loss

    def parameter_hash(self) -> str:
        digest = hashlib.sha256()
        for name in sorted(self.online.parameters):
            digest.update(name.encode("utf-8"))
            digest.update(np.ascontiguousarray(self.online.parameters[name]).tobytes())
        return digest.hexdigest()

    def save(self, path: Path, *, actions: tuple[str, ...]) -> dict[str, object]:
        if len(actions) != self.action_dim or len(set(actions)) != len(actions):
            raise ValueError("action order must match the action dimension")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "format": "week7_numpy_double_dqn_v1",
            "state_dim": self.state_dim,
            "hidden_dim": self.hidden_dim,
            "action_dim": self.action_dim,
            "action_order": list(actions),
            "seed": self.seed,
            "train_steps": self.train_steps,
            "gamma": self.gamma,
            "sha256": self.parameter_hash(),
        }
        np.savez_compressed(
            path,
            metadata=np.asarray(json.dumps(manifest)),
            **{f"online_{name}": value for name, value in self.online.parameters.items()},
        )
        return manifest

    @classmethod
    def load(cls, path: Path, *, expected_actions: tuple[str, ...]) -> "DQNAgent":
        with np.load(Path(path), allow_pickle=False) as data:
            manifest = json.loads(str(data["metadata"]))
            if manifest.get("format") != "week7_numpy_double_dqn_v1":
                raise ValueError("unsupported checkpoint format")
            if manifest.get("action_order") != list(expected_actions):
                raise ValueError("checkpoint action order does not match")
            agent = cls(
                state_dim=int(manifest["state_dim"]),
                hidden_dim=int(manifest["hidden_dim"]),
                action_dim=int(manifest["action_dim"]),
                seed=int(manifest["seed"]),
                gamma=float(manifest["gamma"]),
            )
            for name, parameter in agent.online.parameters.items():
                key = f"online_{name}"
                if key not in data or data[key].shape != parameter.shape:
                    raise ValueError(f"checkpoint parameter shape mismatch: {name}")
                parameter[...] = _finite_array(data[key], parameter.shape, name)
            agent.target.copy_from(agent.online)
            agent.train_steps = int(manifest.get("train_steps", 0))
        if agent.parameter_hash() != manifest.get("sha256"):
            raise ValueError("checkpoint parameter hash mismatch")
        return agent
