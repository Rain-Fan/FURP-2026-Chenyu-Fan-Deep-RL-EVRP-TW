#!/usr/bin/env python3
"""Train and evaluate the Week 7 Double-DQN EVRP-TW operator selector."""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import shlex
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, median, pstdev

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for relative in (
    "src/experiments/week3",
    "src/experiments/week4",
    "src/experiments/week6",
    "src/experiments/week7",
):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from compare_week3_baselines import generate_instance  # noqa: E402
from compare_week4_methods import PARAMETER_PROFILES, apply_profile  # noqa: E402
from dqn_agent import DQNAgent  # noqa: E402
from portfolio_solver import (  # noqa: E402
    CandidateSolution,
    D_METHOD,
    E_ADAPTIVE_METHOD,
    E_FIXED_METHOD,
    SolveResult,
    choose_best_candidate,
    solve_method,
    validate_routes,
)
from rl_environment import (  # noqa: E402
    ACTIONS,
    STATE_DIM,
    SOURCE_METHODS,
    OperatorSelectionEnv,
    build_warm_start,
)

F_DQN_METHOD = "F_dqn_portfolio"
METHODS = {
    D_METHOD: {"role": "week5_reference", "description": "Week 5 fixed inter-route search."},
    E_FIXED_METHOD: {"role": "week6_fixed_reference", "description": "Week 6 fixed two-source portfolio."},
    E_ADAPTIVE_METHOD: {"role": "week6_ucb1_reference", "description": "Week 6 UCB1 two-source portfolio."},
    F_DQN_METHOD: {"role": "tested_method", "description": "Week 7 Double-DQN two-source portfolio."},
}
DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "results"


@dataclass(frozen=True)
class TrainingConfig:
    scales: tuple[int, ...] = (20, 50, 100)
    profiles: tuple[str, ...] = tuple(PARAMETER_PROFILES)
    train_instances: int = 8
    eval_instances: int = 6
    train_seed: int = 20270013
    eval_seed: int = 20280013
    epochs: int = 3
    max_steps: int = 12
    patience: int = 4
    hidden_dim: int = 32
    batch_size: int = 32
    replay_capacity: int = 5000
    learning_rate: float = 0.001
    gamma: float = 0.95
    target_sync: int = 100
    agent_seed: int = 20260813
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05


@dataclass(frozen=True)
class InstanceResult:
    profile: str
    method: str
    method_role: str
    instance: str
    scale: int
    seed: int
    feasible: bool
    objective: float
    runtime_sec: float
    vehicles_used: int
    violations: tuple[str, ...]
    selected_source: str
    initial_objective: float
    accepted_moves: int
    trace: tuple[dict[str, object], ...]
    routes: tuple[tuple[int, ...], ...]
    termination_reason: str
    independent_validation: bool

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["objective"] = self.objective if self.feasible else None
        data["initial_objective"] = self.initial_objective if math.isfinite(self.initial_objective) else None
        data["routes"] = [list(route) for route in self.routes]
        data["violations"] = list(self.violations)
        data["trace"] = list(self.trace)
        return data


@dataclass(frozen=True)
class ExperimentBundle:
    metadata: dict[str, object]
    training_history: tuple[dict[str, object], ...]
    aggregate: tuple[dict[str, object], ...]
    comparisons: tuple[dict[str, object], ...]
    instances: tuple[InstanceResult, ...]
    action_trace: tuple[dict[str, object], ...]
    diagnostics: tuple[dict[str, object], ...]


def _validate_config(config: TrainingConfig) -> tuple[set[int], set[int]]:
    if not config.scales or min(config.scales) <= 0:
        raise ValueError("scales must be positive")
    if not config.profiles or any(profile not in PARAMETER_PROFILES for profile in config.profiles):
        raise ValueError("profiles contain an unknown profile")
    positive = (
        config.train_instances,
        config.eval_instances,
        config.epochs,
        config.max_steps,
        config.patience,
        config.hidden_dim,
        config.batch_size,
        config.replay_capacity,
        config.target_sync,
    )
    if min(positive) <= 0:
        raise ValueError("counts, dimensions, and budgets must be positive")
    if config.learning_rate <= 0.0 or not 0.0 <= config.gamma <= 1.0:
        raise ValueError("learning rate and gamma are invalid")
    if not 0.0 <= config.epsilon_end <= config.epsilon_start <= 1.0:
        raise ValueError("epsilon schedule is invalid")
    train_seeds = {
        config.train_seed + scale * 1000 + offset
        for scale in config.scales for offset in range(config.train_instances)
    }
    eval_seeds = {
        config.eval_seed + scale * 1000 + offset
        for scale in config.scales for offset in range(config.eval_instances)
    }
    overlap = train_seeds & eval_seeds
    if overlap:
        raise ValueError(f"training/evaluation seed overlap: {sorted(overlap)}")
    return train_seeds, eval_seeds


def _training_episodes(config: TrainingConfig):
    episodes = []
    for profile in config.profiles:
        for scale in config.scales:
            for offset in range(config.train_instances):
                seed = config.train_seed + scale * 1000 + offset
                instance = apply_profile(generate_instance(scale, seed), profile)
                for source in SOURCE_METHODS:
                    warm = build_warm_start(instance, source)
                    if warm is not None:
                        episodes.append((profile, instance, warm))
    return episodes


def train_agent(config: TrainingConfig) -> tuple[DQNAgent, list[dict[str, object]], dict[str, object]]:
    """Train online on deterministic local instances with a disjoint seed split."""

    _validate_config(config)
    agent = DQNAgent(
        state_dim=STATE_DIM,
        action_dim=len(ACTIONS),
        hidden_dim=config.hidden_dim,
        seed=config.agent_seed,
        replay_capacity=config.replay_capacity,
        learning_rate=config.learning_rate,
        gamma=config.gamma,
        target_sync=config.target_sync,
    )
    base_episodes = _training_episodes(config)
    if not base_episodes:
        raise ValueError("no feasible training warm starts")
    schedule_rng = np.random.default_rng(config.agent_seed + 17)
    total_episodes = config.epochs * len(base_episodes)
    history: list[dict[str, object]] = []
    episode_index = 0
    started = time.perf_counter()
    for epoch in range(config.epochs):
        order = schedule_rng.permutation(len(base_episodes))
        for position in order:
            profile, instance, warm = base_episodes[int(position)]
            fraction = episode_index / max(1, total_episodes - 1)
            epsilon = config.epsilon_start + fraction * (config.epsilon_end - config.epsilon_start)
            env = OperatorSelectionEnv(
                instance,
                warm.routes,
                warm.source,
                max_steps=config.max_steps,
                patience=config.patience,
            )
            losses: list[float] = []
            total_reward = 0.0
            while not env.done:
                state = env.state.copy()
                action = agent.select_action(state, epsilon=epsilon)
                transition = env.step(action)
                agent.observe(state, action, transition.reward, transition.next_state, transition.done)
                loss = agent.train_step(batch_size=config.batch_size)
                if loss is not None:
                    losses.append(loss)
                total_reward += transition.reward
            result = env.result()
            history.append(
                {
                    "epoch": epoch,
                    "episode": episode_index,
                    "profile": profile,
                    "scale": instance.scale,
                    "seed": instance.seed,
                    "source": warm.source,
                    "epsilon": epsilon,
                    "return": total_reward,
                    "steps": len(result.transitions),
                    "accepted_steps": result.accepted_steps,
                    "improvement_pct": 100.0 * (warm.objective - result.objective) / warm.objective,
                    "mean_loss": mean(losses) if losses else None,
                    "termination_reason": result.termination_reason,
                }
            )
            episode_index += 1
    training_meta = {
        "candidate_episodes_per_epoch": len(base_episodes),
        "episodes": len(history),
        "transitions": len(agent.replay),
        "optimizer_steps": agent.train_steps,
        "runtime_sec": time.perf_counter() - started,
    }
    return agent, history, training_meta


def solve_dqn_portfolio(instance, agent: DQNAgent, *, max_steps: int, patience: int) -> SolveResult:
    """Search both portfolio candidates greedily with a trained DQN."""

    started = time.perf_counter()
    candidates: list[CandidateSolution] = []
    for source in SOURCE_METHODS:
        candidate_started = time.perf_counter()
        warm = build_warm_start(instance, source)
        if warm is None:
            candidates.append(
                CandidateSolution(
                    source=source,
                    routes=(),
                    initial_objective=math.inf,
                    final_objective=math.inf,
                    feasible=False,
                    violations=("infeasible construction or warm start",),
                    runtime_sec=time.perf_counter() - candidate_started,
                    termination_reason="infeasible_warm_start",
                )
            )
            continue
        env = OperatorSelectionEnv(
            instance,
            warm.routes,
            source,
            max_steps=max_steps,
            patience=patience,
        )
        while not env.done:
            env.step(agent.select_action(env.state, epsilon=0.0))
        episode = env.result()
        validation = validate_routes(instance, episode.routes)
        inter_moves = sum(
            transition.moves for transition in episode.transitions
            if transition.accepted and transition.action in ("relocate", "swap")
        )
        candidates.append(
            CandidateSolution(
                source=source,
                routes=episode.routes,
                initial_objective=warm.construction_objective,
                final_objective=validation.objective,
                feasible=validation.feasible,
                violations=validation.violations,
                two_opt_moves=warm.two_opt_moves,
                inter_route_moves=inter_moves,
                accepted_moves=warm.two_opt_moves + episode.accepted_moves,
                runtime_sec=time.perf_counter() - candidate_started,
                trace=episode.transitions,
                termination_reason=episode.termination_reason,
            )
        )
    selected = choose_best_candidate(candidates)
    return SolveResult(
        method=F_DQN_METHOD,
        routes=selected.routes,
        feasible=selected.feasible,
        objective=selected.final_objective,
        violations=selected.violations,
        selected_source=selected.source,
        initial_objective=selected.initial_objective,
        runtime_sec=time.perf_counter() - started,
        two_opt_moves=selected.two_opt_moves,
        inter_route_moves=selected.inter_route_moves,
        accepted_moves=selected.accepted_moves,
        trace=tuple(record for candidate in candidates for record in candidate.trace),
        termination_reason=selected.termination_reason,
        candidates=tuple(candidates),
    )


def _instance_result(profile: str, instance, result: SolveResult) -> InstanceResult:
    trace: list[dict[str, object]] = []
    for candidate in result.candidates:
        for record in candidate.trace:
            row = record.to_dict()
            row.update(
                {
                    "profile": profile,
                    "method": result.method,
                    "instance": instance.name,
                    "instance_seed": instance.seed,
                    "construction_source": candidate.source,
                }
            )
            trace.append(row)
    validation = validate_routes(instance, result.routes)
    valid_match = validation.feasible == result.feasible
    if result.feasible:
        valid_match = valid_match and abs(validation.objective - result.objective) <= 1e-8
    return InstanceResult(
        profile=profile,
        method=result.method,
        method_role=str(METHODS[result.method]["role"]),
        instance=instance.name,
        scale=instance.scale,
        seed=instance.seed,
        feasible=result.feasible,
        objective=result.objective,
        runtime_sec=result.runtime_sec,
        vehicles_used=len(result.routes),
        violations=result.violations,
        selected_source=result.selected_source,
        initial_objective=result.initial_objective,
        accepted_moves=result.accepted_moves,
        trace=tuple(trace),
        routes=result.routes,
        termination_reason=result.termination_reason,
        independent_validation=valid_match,
    )


def aggregate_results(results: list[InstanceResult]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for profile in PARAMETER_PROFILES:
        for scale in sorted({row.scale for row in results}):
            for method in METHODS:
                subset = [row for row in results if row.profile == profile and row.scale == scale and row.method == method]
                if not subset:
                    continue
                feasible = [row for row in subset if row.feasible]
                objectives = [row.objective for row in feasible]
                rows.append(
                    {
                        "profile": profile,
                        "scale": scale,
                        "method": method,
                        "method_role": METHODS[method]["role"],
                        "instances": len(subset),
                        "feasible_instances": len(feasible),
                        "feasibility_rate": len(feasible) / len(subset),
                        "mean_objective_feasible": mean(objectives) if objectives else None,
                        "median_objective_feasible": median(objectives) if objectives else None,
                        "best_objective_feasible": min(objectives) if objectives else None,
                        "std_objective_feasible": pstdev(objectives) if objectives else None,
                        "mean_runtime_sec": mean(row.runtime_sec for row in subset),
                        "mean_vehicles_used": mean(row.vehicles_used for row in subset),
                        "mean_accepted_moves": mean(row.accepted_moves for row in subset),
                        "validation_failures": sum(not row.independent_validation for row in subset),
                    }
                )
    return rows


def compare_results(aggregate: list[dict[str, object]], instances: list[InstanceResult]) -> list[dict[str, object]]:
    comparisons = []
    for profile in PARAMETER_PROFILES:
        for scale in sorted({row.scale for row in instances}):
            tested_row = next((row for row in aggregate if row["profile"] == profile and row["scale"] == scale and row["method"] == F_DQN_METHOD), None)
            if tested_row is None:
                continue
            for reference in (D_METHOD, E_FIXED_METHOD, E_ADAPTIVE_METHOD):
                reference_row = next(row for row in aggregate if row["profile"] == profile and row["scale"] == scale and row["method"] == reference)
                pairs = []
                for seed in sorted({row.seed for row in instances if row.profile == profile and row.scale == scale}):
                    tested = next(row for row in instances if row.profile == profile and row.scale == scale and row.seed == seed and row.method == F_DQN_METHOD)
                    ref = next(row for row in instances if row.profile == profile and row.scale == scale and row.seed == seed and row.method == reference)
                    if tested.feasible and ref.feasible:
                        pairs.append((tested.objective, ref.objective))
                tested_obj = tested_row["mean_objective_feasible"]
                ref_obj = reference_row["mean_objective_feasible"]
                wins = sum(test + 1e-9 < ref for test, ref in pairs)
                losses = sum(test > ref + 1e-9 for test, ref in pairs)
                comparisons.append(
                    {
                        "profile": profile,
                        "scale": scale,
                        "tested_method": F_DQN_METHOD,
                        "reference_method": reference,
                        "feasibility_rate_delta": tested_row["feasibility_rate"] - reference_row["feasibility_rate"],
                        "mean_feasible_objective_delta": tested_obj - ref_obj if tested_obj is not None and ref_obj is not None else None,
                        "mean_feasible_objective_pct": 100.0 * (tested_obj - ref_obj) / ref_obj if tested_obj is not None and ref_obj not in (None, 0.0) else None,
                        "mean_runtime_delta_sec": tested_row["mean_runtime_sec"] - reference_row["mean_runtime_sec"],
                        "jointly_feasible_instances": len(pairs),
                        "wins": wins,
                        "ties": len(pairs) - wins - losses,
                        "losses": losses,
                    }
                )
    return comparisons


def _diagnostics(instances: list[InstanceResult]) -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    for row in instances:
        if not row.feasible or not row.independent_validation:
            diagnostics.append({
                "kind": "infeasible_or_validation",
                "profile": row.profile, "scale": row.scale, "seed": row.seed,
                "method": row.method, "feasible": row.feasible,
                "objective_gap_vs_ucb1": None, "runtime_sec": row.runtime_sec,
                "violations": list(row.violations),
            })
    for tested in [row for row in instances if row.method == F_DQN_METHOD and row.feasible]:
        reference = next(row for row in instances if row.profile == tested.profile and row.scale == tested.scale and row.seed == tested.seed and row.method == E_ADAPTIVE_METHOD)
        if reference.feasible:
            diagnostics.append({
                "kind": "dqn_vs_ucb1",
                "profile": tested.profile, "scale": tested.scale, "seed": tested.seed,
                "method": tested.method, "feasible": True,
                "objective_gap_vs_ucb1": tested.objective - reference.objective,
                "runtime_sec": tested.runtime_sec,
                "violations": [],
            })
    diagnostics.sort(key=lambda row: (row["kind"] != "infeasible_or_validation", -(row["objective_gap_vs_ucb1"] or 0.0), -row["runtime_sec"]))
    return diagnostics[:20]


def run_experiment(config: TrainingConfig) -> tuple[ExperimentBundle, DQNAgent]:
    train_seeds, eval_seeds = _validate_config(config)
    run_started = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    wall_started = time.perf_counter()
    agent, training_history, training_meta = train_agent(config)
    instances: list[InstanceResult] = []
    for profile in config.profiles:
        for scale in config.scales:
            for offset in range(config.eval_instances):
                seed = config.eval_seed + scale * 1000 + offset
                instance = apply_profile(generate_instance(scale, seed), profile)
                for method in METHODS:
                    if method == F_DQN_METHOD:
                        solved = solve_dqn_portfolio(instance, agent, max_steps=config.max_steps, patience=config.patience)
                    else:
                        solved = solve_method(instance, method, adaptive_steps=config.max_steps, patience=config.patience)
                    instances.append(_instance_result(profile, instance, solved))
    aggregate = aggregate_results(instances)
    comparisons = compare_results(aggregate, instances)
    trace = tuple(record for result in instances if result.method == F_DQN_METHOD for record in result.trace)
    metadata = {
        "run_started": run_started,
        "research_question": "Can a seed-separated Double DQN improve the Week 6 UCB1 operator selector on held-out EVRP-TW instances?",
        "config": asdict(config),
        "methods": METHODS,
        "state_dim": STATE_DIM,
        "actions": list(ACTIONS),
        "train_seeds": sorted(train_seeds),
        "eval_seeds": sorted(eval_seeds),
        "seed_overlap": sorted(train_seeds & eval_seeds),
        "training": training_meta,
        "held_out_method_runs": len(instances),
        "held_out_instances": len(eval_seeds) * len(config.profiles),
        "action_trace_rows": len(trace),
        "independent_validation_failures": sum(not row.independent_validation for row in instances),
        "model_parameter_hash": agent.parameter_hash(),
        "total_runtime_sec": time.perf_counter() - wall_started,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
    }
    bundle = ExperimentBundle(
        metadata=metadata,
        training_history=tuple(training_history),
        aggregate=tuple(aggregate),
        comparisons=tuple(comparisons),
        instances=tuple(instances),
        action_trace=trace,
        diagnostics=tuple(_diagnostics(instances)),
    )
    return bundle, agent


def _write_csv(path: Path, rows) -> None:
    rows = list(rows)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _fmt(value: object, digits: int = 3) -> str:
    return "N/A" if value is None else f"{float(value):.{digits}f}"


def _markdown(bundle: ExperimentBundle) -> str:
    lines = [
        "# Week 7 Results: Double-DQN Operator Selection",
        "",
        f"Run started: `{bundle.metadata['run_started']}`",
        "",
        str(bundle.metadata["research_question"]),
        "",
        "Training and evaluation seed overlap: **0**.",
        "",
        "## Held-out aggregate results",
        "",
        "| Profile | n | Method | Feasible | Mean objective | Runtime (s) |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for row in bundle.aggregate:
        lines.append(
            f"| {row['profile']} | {row['scale']} | {row['method']} | "
            f"{row['feasible_instances']}/{row['instances']} | {_fmt(row['mean_objective_feasible'])} | "
            f"{row['mean_runtime_sec']:.6f} |"
        )
    lines.extend([
        "", "## F-DQN comparisons", "",
        "Negative objective percentage means DQN is shorter.", "",
        "| Profile | n | Reference | Feasibility delta | Objective delta (%) | Runtime delta (s) | W/T/L |",
        "|---|---:|---|---:|---:|---:|---:|",
    ])
    for row in bundle.comparisons:
        lines.append(
            f"| {row['profile']} | {row['scale']} | {row['reference_method']} | "
            f"{row['feasibility_rate_delta']:+.3f} | {_fmt(row['mean_feasible_objective_pct'], 2)} | "
            f"{row['mean_runtime_delta_sec']:+.6f} | {row['wins']}/{row['ties']}/{row['losses']} |"
        )
    lines.extend(["", "## Failure and limitation cases", ""])
    for row in bundle.diagnostics[:6]:
        lines.append(
            f"- `{row['kind']}` profile={row['profile']}, n={row['scale']}, seed={row['seed']}: "
            f"gap_vs_UCB1={row['objective_gap_vs_ucb1']}, runtime={row['runtime_sec']:.6f}s, "
            f"violations={row['violations']}"
        )
    lines.extend([
        "", "## Interpretation rule", "",
        "This prototype is judged against fixed and UCB1 references on held-out seeds. "
        "It is not claimed to be state of the art, and losses are retained in the tables.", "",
    ])
    return "\n".join(lines)


def write_outputs(bundle: ExperimentBundle, agent: DQNAgent, output_dir: Path = DEFAULT_RESULTS_DIR, *, command: list[str] | None = None) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": bundle.metadata,
        "training_history": list(bundle.training_history),
        "aggregate": list(bundle.aggregate),
        "comparisons": list(bundle.comparisons),
        "instances": [row.to_dict() for row in bundle.instances],
        "action_trace": list(bundle.action_trace),
        "diagnostics": list(bundle.diagnostics),
    }
    (output_dir / "week7_results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_csv(output_dir / "week7_aggregate.csv", bundle.aggregate)
    _write_csv(output_dir / "week7_comparison.csv", bundle.comparisons)
    _write_csv(output_dir / "week7_training_history.csv", bundle.training_history)
    instance_rows = []
    for row in bundle.instances:
        data = row.to_dict()
        for key in ("routes", "trace", "violations"):
            data[key] = json.dumps(data[key], separators=(",", ":"))
        instance_rows.append(data)
    _write_csv(output_dir / "week7_instances.csv", instance_rows)
    (output_dir / "week7_results.md").write_text(_markdown(bundle), encoding="utf-8")
    manifest = agent.save(output_dir / "dqn_checkpoint.npz", actions=ACTIONS)
    (output_dir / "dqn_checkpoint_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    log = [
        "Week 7 Double-DQN local run log", "",
        f"Run started: {bundle.metadata['run_started']}",
        f"Command: {' '.join(shlex.quote(part) for part in (command or sys.argv))}",
        f"Python: {bundle.metadata['python']}",
        f"NumPy: {bundle.metadata['numpy']}",
        f"Platform: {bundle.metadata['platform']}",
        f"Training episodes: {bundle.metadata['training']['episodes']}",
        f"Held-out method runs: {bundle.metadata['held_out_method_runs']}",
        f"Seed overlap: {bundle.metadata['seed_overlap']}",
        f"Independent validation failures: {bundle.metadata['independent_validation_failures']}",
        f"Model parameter hash: {bundle.metadata['model_parameter_hash']}",
    ]
    (output_dir / "run_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", nargs="+", type=int, default=[20, 50, 100])
    parser.add_argument("--profiles", nargs="+", default=list(PARAMETER_PROFILES))
    parser.add_argument("--train-instances", type=int, default=8)
    parser.add_argument("--eval-instances", type=int, default=6)
    parser.add_argument("--train-seed", type=int, default=20270013)
    parser.add_argument("--eval-seed", type=int, default=20280013)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--max-steps", type=int, default=12)
    parser.add_argument("--patience", type=int, default=4)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--replay-capacity", type=int, default=5000)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--gamma", type=float, default=0.95)
    parser.add_argument("--target-sync", type=int, default=100)
    parser.add_argument("--agent-seed", type=int, default=20260813)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = TrainingConfig(
        scales=tuple(args.scales), profiles=tuple(args.profiles),
        train_instances=args.train_instances, eval_instances=args.eval_instances,
        train_seed=args.train_seed, eval_seed=args.eval_seed, epochs=args.epochs,
        max_steps=args.max_steps, patience=args.patience, hidden_dim=args.hidden_dim,
        batch_size=args.batch_size, replay_capacity=args.replay_capacity,
        learning_rate=args.learning_rate, gamma=args.gamma,
        target_sync=args.target_sync, agent_seed=args.agent_seed,
    )
    bundle, agent = run_experiment(config)
    write_outputs(bundle, agent, args.output_dir, command=sys.argv)
    print(json.dumps({
        "output_dir": str(args.output_dir),
        "training_episodes": bundle.metadata["training"]["episodes"],
        "held_out_method_runs": len(bundle.instances),
        "seed_overlap": bundle.metadata["seed_overlap"],
        "model_hash": bundle.metadata["model_parameter_hash"],
    }, indent=2))


if __name__ == "__main__":
    main()
