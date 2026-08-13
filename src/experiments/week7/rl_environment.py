#!/usr/bin/env python3
"""Stateful EVRP-TW operator-selection MDP for the Week 7 RL prototype."""

from __future__ import annotations

import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for relative in (
    "src/experiments/week3",
    "src/experiments/week4",
    "src/experiments/week6",
):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from compare_week3_baselines import Instance  # noqa: E402
from compare_week4_methods import (  # noqa: E402
    COMPOSITE_METHOD,
    NEAREST_METHOD,
    apply_two_opt,
    greedy_solve,
)
from portfolio_solver import (  # noqa: E402
    _operator_actions,
    raw_solution_distance,
    validate_routes,
)

ACTIONS = ("two_opt", "relocate", "swap")
SOURCE_METHODS = {"nearest": NEAREST_METHOD, "composite": COMPOSITE_METHOD}
STATE_DIM = 12


def _route_tuple(routes) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(node) for node in route) for route in routes)


@dataclass(frozen=True)
class WarmStart:
    source: str
    routes: tuple[tuple[int, ...], ...]
    construction_objective: float
    objective: float
    two_opt_moves: int


@dataclass(frozen=True)
class Transition:
    step: int
    state: np.ndarray
    action_index: int
    action: str
    reward: float
    next_state: np.ndarray
    done: bool
    accepted: bool
    feasible: bool
    objective_before: float
    candidate_objective: float
    objective_after: float
    moves: int
    runtime_sec: float
    termination_reason: str | None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["state"] = self.state.tolist()
        data["next_state"] = self.next_state.tolist()
        return data


@dataclass(frozen=True)
class EpisodeResult:
    routes: tuple[tuple[int, ...], ...]
    objective: float
    transitions: tuple[Transition, ...]
    termination_reason: str
    accepted_steps: int
    accepted_moves: int
    runtime_sec: float


def build_warm_start(instance: Instance, source: str) -> WarmStart | None:
    """Construct and 2-opt one feasible candidate, or return None explicitly."""

    if source not in SOURCE_METHODS:
        raise ValueError(f"unknown construction source: {source}")
    routes, construction_violations = greedy_solve(instance, SOURCE_METHODS[source])
    initial = validate_routes(instance, routes)
    if construction_violations or not initial.feasible:
        return None
    warmed, moves, _gain = apply_two_opt(instance, routes)
    validation = validate_routes(instance, warmed)
    if not validation.feasible:
        return None
    return WarmStart(
        source=source,
        routes=_route_tuple(warmed),
        construction_objective=initial.objective,
        objective=validation.objective,
        two_opt_moves=int(moves),
    )


class OperatorSelectionEnv:
    """A deterministic, finite-horizon MDP over real local-search operators."""

    def __init__(
        self,
        instance: Instance,
        routes,
        source: str,
        *,
        max_steps: int = 12,
        patience: int = 4,
    ):
        if source not in SOURCE_METHODS:
            raise ValueError(f"unknown construction source: {source}")
        if max_steps <= 0 or patience <= 0:
            raise ValueError("max_steps and patience must be positive")
        validation = validate_routes(instance, routes)
        if not validation.feasible:
            raise ValueError("environment requires a feasible warm start")
        self.instance = instance
        self.source = source
        self.max_steps = int(max_steps)
        self.patience = int(patience)
        self._initial_routes = _route_tuple(routes)
        self.warm_start_objective = float(validation.objective)
        self._actions = _operator_actions(instance)
        self.reset()

    def reset(self) -> np.ndarray:
        self.routes = self._initial_routes
        self.objective = self.warm_start_objective
        self.validation = validate_routes(self.instance, self.routes)
        self.step_count = 0
        self.no_improvement = 0
        self.accepted_steps = 0
        self.accepted_moves = 0
        self.last_reward = 0.0
        self.last_action_index: int | None = None
        self.total_runtime_sec = 0.0
        self.done = False
        self.termination_reason: str | None = None
        self.transitions: list[Transition] = []
        return self.state

    @property
    def state(self) -> np.ndarray:
        last_action = [0.0, 0.0, 0.0]
        if self.last_action_index is not None:
            last_action[self.last_action_index] = 1.0
        improvement = (self.warm_start_objective - self.objective) / self.warm_start_objective
        acceptance_rate = self.accepted_steps / self.step_count if self.step_count else 0.0
        values = np.asarray(
            [
                self.instance.scale / 100.0,
                len(self.routes) / max(1, self.instance.max_vehicles),
                self.objective / self.warm_start_objective,
                improvement,
                self.step_count / self.max_steps,
                self.no_improvement / self.patience,
                float(np.clip(self.last_reward, -1.0, 1.0)),
                acceptance_rate,
                *last_action,
                1.0 if self.source == "composite" else 0.0,
            ],
            dtype=np.float64,
        )
        if values.shape != (STATE_DIM,) or not np.isfinite(values).all():
            raise ValueError("state must be a finite 12-value vector")
        return values

    def step(self, action_index: int) -> Transition:
        if self.done:
            raise ValueError("episode is already terminated")
        if not isinstance(action_index, (int, np.integer)) or not 0 <= int(action_index) < len(ACTIONS):
            raise ValueError(f"action index must be in [0, {len(ACTIONS) - 1}]")
        action_index = int(action_index)
        action = ACTIONS[action_index]
        state = self.state.copy()
        before = self.objective
        outcome = self._actions[action](self.routes)
        candidate_objective = float(raw_solution_distance(self.instance, outcome.solution))
        candidate_validation = validate_routes(self.instance, outcome.solution)
        feasible = bool(outcome.feasible and candidate_validation.feasible and math.isfinite(candidate_objective))
        accepted = feasible and candidate_objective + 1e-9 < before
        if not feasible:
            reward = -1.0
        elif accepted:
            reward = (before - candidate_objective) / self.warm_start_objective
        else:
            reward = -0.001

        if accepted:
            self.routes = _route_tuple(outcome.solution)
            self.objective = candidate_objective
            self.validation = candidate_validation
            self.accepted_steps += 1
            self.accepted_moves += max(0, int(outcome.moves))
            self.no_improvement = 0
        else:
            self.no_improvement += 1

        self.step_count += 1
        self.last_action_index = action_index
        self.last_reward = reward
        self.total_runtime_sec += max(0.0, float(outcome.runtime_sec))
        if self.no_improvement >= self.patience:
            self.done = True
            self.termination_reason = "patience"
        elif self.step_count >= self.max_steps:
            self.done = True
            self.termination_reason = "budget"

        transition = Transition(
            step=self.step_count - 1,
            state=state,
            action_index=action_index,
            action=action,
            reward=float(reward),
            next_state=self.state.copy(),
            done=self.done,
            accepted=accepted,
            feasible=feasible,
            objective_before=before,
            candidate_objective=candidate_objective,
            objective_after=self.objective,
            moves=max(0, int(outcome.moves)),
            runtime_sec=max(0.0, float(outcome.runtime_sec)),
            termination_reason=self.termination_reason,
        )
        self.transitions.append(transition)
        return transition

    def result(self) -> EpisodeResult:
        if not self.done:
            raise ValueError("episode has not terminated")
        return EpisodeResult(
            routes=self.routes,
            objective=self.objective,
            transitions=tuple(self.transitions),
            termination_reason=str(self.termination_reason),
            accepted_steps=self.accepted_steps,
            accepted_moves=self.accepted_moves,
            runtime_sec=self.total_runtime_sec,
        )
