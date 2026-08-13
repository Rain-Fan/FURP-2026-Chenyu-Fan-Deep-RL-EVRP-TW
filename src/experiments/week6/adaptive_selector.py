#!/usr/bin/env python3
"""Deterministic UCB1 operator selection for the Week 6 experiment.

The selector is intentionally domain independent.  The EVRP-TW portfolio
solver injects route operators, objective calculation, and validation so this
module can be unit tested with small scalar examples.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, replace
from typing import Callable, Generic, Mapping, TypeVar

SolutionT = TypeVar("SolutionT")


@dataclass(frozen=True)
class ActionOutcome(Generic[SolutionT]):
    """Candidate returned by one bounded operator application."""

    solution: SolutionT
    moves: int
    feasible: bool
    runtime_sec: float


@dataclass(frozen=True)
class TraceRecord:
    """One inspectable decision in an adaptive search episode."""

    step: int
    action: str
    ucb_score: float | None
    objective_before: float
    objective_after: float
    reward: float
    accepted: bool
    moves: int
    feasible: bool
    action_runtime_sec: float
    cumulative_runtime_sec: float
    context: dict[str, object]
    termination_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SearchResult(Generic[SolutionT]):
    solution: SolutionT
    objective: float
    trace: tuple[TraceRecord, ...]
    termination_reason: str
    accepted_moves: int
    runtime_sec: float


def normalized_reward(before: float, after: float, feasible: bool) -> float:
    """Return relative objective improvement, or a fixed infeasibility penalty."""

    if not math.isfinite(before) or not math.isfinite(after) or before <= 0.0:
        raise ValueError("objectives must be finite and the starting objective positive")
    if not feasible:
        return -1.0
    return (before - after) / before


class UCB1Policy:
    """Small deterministic UCB1 policy with explicit selection reservations."""

    def __init__(self, actions: tuple[str, ...], exploration_weight: float = 0.7):
        if not actions or len(set(actions)) != len(actions):
            raise ValueError("actions must be a nonempty ordered set")
        if exploration_weight < 0.0:
            raise ValueError("exploration_weight must be nonnegative")
        self.actions = actions
        self.exploration_weight = exploration_weight
        self.pulls = {action: 0 for action in actions}
        self.reward_sums = {action: 0.0 for action in actions}
        self._pending = {action: 0 for action in actions}

    def scores(self) -> dict[str, float]:
        total = sum(self.pulls.values())
        values: dict[str, float] = {}
        for action in self.actions:
            pulls = self.pulls[action]
            if pulls == 0:
                values[action] = math.inf
                continue
            mean_reward = self.reward_sums[action] / pulls
            exploration = 0.0
            if total > 1:
                exploration = self.exploration_weight * math.sqrt(math.log(total) / pulls)
            values[action] = mean_reward + exploration
        return values

    def select(self) -> str:
        values = self.scores()
        selected = max(self.actions, key=lambda action: values[action])
        self.pulls[selected] += 1
        self._pending[selected] += 1
        return selected

    def update(self, action: str, reward: float) -> None:
        if action not in self.pulls:
            raise ValueError(f"unknown action: {action}")
        if self._pending[action] <= 0:
            raise ValueError(f"action was not selected before update: {action}")
        if not math.isfinite(reward):
            raise ValueError("reward must be finite")
        self._pending[action] -= 1
        self.reward_sums[action] += reward


def adaptive_search(
    initial: SolutionT,
    actions: Mapping[str, Callable[[SolutionT], ActionOutcome[SolutionT]]],
    objective: Callable[[SolutionT], float],
    validate: Callable[[SolutionT], bool],
    *,
    max_steps: int = 12,
    patience: int = 4,
    exploration_weight: float = 0.7,
    context: Mapping[str, object] | None = None,
) -> SearchResult[SolutionT]:
    """Apply bounded actions selected by UCB1 and keep strict feasible gains."""

    if max_steps <= 0 or patience <= 0:
        raise ValueError("max_steps and patience must be positive")
    if not actions:
        raise ValueError("at least one action is required")
    if not validate(initial):
        raise ValueError("adaptive search requires a feasible initial solution")

    current = initial
    current_objective = float(objective(current))
    if not math.isfinite(current_objective) or current_objective <= 0.0:
        raise ValueError("initial objective must be finite and positive")

    policy = UCB1Policy(tuple(actions), exploration_weight)
    trace: list[TraceRecord] = []
    no_improvement = 0
    accepted_moves = 0
    cumulative_runtime = 0.0
    termination_reason = "budget"
    shared_context = dict(context or {})

    for step in range(max_steps):
        pre_scores = policy.scores()
        action = policy.select()
        raw_score = pre_scores[action]
        ucb_score = raw_score if math.isfinite(raw_score) else None
        outcome = actions[action](current)
        candidate_objective = float(objective(outcome.solution))
        feasible = bool(outcome.feasible and validate(outcome.solution))
        reward = normalized_reward(current_objective, candidate_objective, feasible)
        accepted = feasible and candidate_objective + 1e-9 < current_objective
        policy.update(action, reward)

        cumulative_runtime += max(0.0, float(outcome.runtime_sec))
        record = TraceRecord(
            step=step,
            action=action,
            ucb_score=ucb_score,
            objective_before=current_objective,
            objective_after=candidate_objective,
            reward=reward,
            accepted=accepted,
            moves=max(0, int(outcome.moves)),
            feasible=feasible,
            action_runtime_sec=max(0.0, float(outcome.runtime_sec)),
            cumulative_runtime_sec=cumulative_runtime,
            context=dict(shared_context),
        )

        if accepted:
            current = outcome.solution
            current_objective = candidate_objective
            accepted_moves += max(0, int(outcome.moves))
            no_improvement = 0
        else:
            no_improvement += 1

        if no_improvement >= patience:
            termination_reason = "patience"
            trace.append(replace(record, termination_reason=termination_reason))
            break
        trace.append(record)
    else:
        if trace:
            trace[-1] = replace(trace[-1], termination_reason=termination_reason)

    return SearchResult(
        solution=current,
        objective=current_objective,
        trace=tuple(trace),
        termination_reason=termination_reason,
        accepted_moves=accepted_moves,
        runtime_sec=cumulative_runtime,
    )
