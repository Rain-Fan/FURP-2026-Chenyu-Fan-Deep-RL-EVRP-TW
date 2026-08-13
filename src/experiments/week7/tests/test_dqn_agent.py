#!/usr/bin/env python3
"""Behavior tests for the dependency-light NumPy Double DQN."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

WEEK7_DIR = Path(__file__).resolve().parents[1]
if str(WEEK7_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK7_DIR))

from dqn_agent import DQNAgent, ReplayBuffer, compute_double_dqn_targets  # noqa: E402


class DoubleDQNTargetTests(unittest.TestCase):
    def test_online_network_selects_and_target_network_evaluates(self) -> None:
        rewards = np.array([1.0, -0.5])
        dones = np.array([False, True])
        online_next = np.array([[1.0, 3.0, 2.0], [4.0, 1.0, 0.0]])
        target_next = np.array([[10.0, 20.0, 30.0], [7.0, 8.0, 9.0]])
        targets = compute_double_dqn_targets(rewards, dones, online_next, target_next, 0.5)
        np.testing.assert_allclose(targets, np.array([11.0, -0.5]))


class ReplayBufferTests(unittest.TestCase):
    def test_empty_buffer_rejects_sampling(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty replay"):
            ReplayBuffer(10, 12, seed=1).sample(1)


class DQNAgentTests(unittest.TestCase):
    def test_training_reduces_loss_on_repeated_terminal_target(self) -> None:
        agent = DQNAgent(state_dim=12, action_dim=3, hidden_dim=16, seed=7)
        state = np.zeros(12, dtype=np.float64)
        for _ in range(80):
            agent.observe(state, 1, 1.0, state, True)
        first = agent.train_step(batch_size=16)
        for _ in range(80):
            last = agent.train_step(batch_size=16)
        self.assertIsNotNone(first)
        self.assertIsNotNone(last)
        self.assertLess(float(last), float(first))

    def test_checkpoint_round_trip_preserves_q_values_and_action_order(self) -> None:
        agent = DQNAgent(state_dim=12, action_dim=3, hidden_dim=16, seed=11)
        state = np.linspace(0.0, 1.0, 12)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "agent.npz"
            manifest = agent.save(path, actions=("two_opt", "relocate", "swap"))
            loaded = DQNAgent.load(path, expected_actions=("two_opt", "relocate", "swap"))
        np.testing.assert_allclose(agent.q_values(state), loaded.q_values(state))
        self.assertEqual(manifest["action_order"], ["two_opt", "relocate", "swap"])
        self.assertEqual(manifest["sha256"], agent.parameter_hash())

    def test_nonfinite_state_is_rejected(self) -> None:
        agent = DQNAgent(state_dim=12, action_dim=3, seed=3)
        state = np.zeros(12)
        state[4] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            agent.select_action(state, epsilon=0.0)


if __name__ == "__main__":
    unittest.main()
