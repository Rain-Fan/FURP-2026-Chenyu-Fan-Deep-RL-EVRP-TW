#!/usr/bin/env python3
"""Controlled Week 6 comparison of fixed and adaptive EVRP-TW portfolios."""

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

ROOT = Path(__file__).resolve().parents[3]
for relative in ("src/experiments/week3", "src/experiments/week4", "src/experiments/week6"):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from compare_week3_baselines import generate_instance  # noqa: E402
from compare_week4_methods import PARAMETER_PROFILES, apply_profile  # noqa: E402
from portfolio_solver import (  # noqa: E402
    B_METHOD,
    D_METHOD,
    E_ADAPTIVE_METHOD,
    E_FIXED_METHOD,
    METHODS,
    solve_method,
)

DEFAULT_SEED = 20260813
DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "results"


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
    two_opt_moves: int
    inter_route_moves: int
    trace: tuple[dict[str, object], ...]
    routes: tuple[tuple[int, ...], ...]
    termination_reason: str
    candidates: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["objective"] = self.objective if self.feasible else None
        data["initial_objective"] = (
            self.initial_objective if math.isfinite(self.initial_objective) else None
        )
        data["routes"] = [list(route) for route in self.routes]
        data["violations"] = list(self.violations)
        data["trace"] = list(self.trace)
        data["candidates"] = list(self.candidates)
        return data


@dataclass(frozen=True)
class ExperimentBundle:
    metadata: dict[str, object]
    aggregate: tuple[dict[str, object], ...]
    comparisons: tuple[dict[str, object], ...]
    instances: tuple[InstanceResult, ...]
    diagnostics: tuple[dict[str, object], ...]
    adaptive_trace: tuple[dict[str, object], ...]


def _instance_result(profile: str, result, instance) -> InstanceResult:
    traces: list[dict[str, object]] = []
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
            traces.append(row)
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
        two_opt_moves=result.two_opt_moves,
        inter_route_moves=result.inter_route_moves,
        trace=tuple(traces),
        routes=result.routes,
        termination_reason=result.termination_reason,
        candidates=tuple(candidate.to_dict() for candidate in result.candidates),
    )


def aggregate_results(results: list[InstanceResult] | tuple[InstanceResult, ...]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    profiles = sorted({r.profile for r in results}, key=list(PARAMETER_PROFILES).index)
    for profile in profiles:
        scales = sorted({r.scale for r in results if r.profile == profile})
        for scale in scales:
            for method in METHODS:
                subset = [
                    r for r in results
                    if r.profile == profile and r.scale == scale and r.method == method
                ]
                if not subset:
                    continue
                feasible = [r for r in subset if r.feasible]
                objectives = [r.objective for r in feasible]
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
                        "mean_runtime_sec": mean(r.runtime_sec for r in subset),
                        "max_runtime_sec": max(r.runtime_sec for r in subset),
                        "mean_vehicles_used": mean(r.vehicles_used for r in subset),
                        "mean_initial_objective": mean(
                            r.initial_objective for r in feasible
                            if math.isfinite(r.initial_objective)
                        ) if any(math.isfinite(r.initial_objective) for r in feasible) else None,
                        "mean_improvement_from_initial_pct": mean(
                            100.0 * (r.initial_objective - r.objective) / r.initial_objective
                            for r in feasible if r.initial_objective > 0.0
                        ) if any(r.initial_objective > 0.0 for r in feasible) else None,
                        "total_accepted_moves": sum(r.accepted_moves for r in subset),
                        "mean_two_opt_moves": mean(r.two_opt_moves for r in subset),
                        "mean_inter_route_moves": mean(r.inter_route_moves for r in subset),
                        "violation_instances": sum(not r.feasible for r in subset),
                    }
                )
    return rows


def compare_results(
    aggregates: list[dict[str, object]],
    instances: list[InstanceResult] | tuple[InstanceResult, ...],
) -> list[dict[str, object]]:
    comparisons: list[dict[str, object]] = []
    keys = sorted({(r.profile, r.scale) for r in instances})
    for profile, scale in keys:
        for tested in (E_FIXED_METHOD, E_ADAPTIVE_METHOD):
            for reference in (B_METHOD, D_METHOD):
                test_row = next(
                    r for r in aggregates
                    if r["profile"] == profile and r["scale"] == scale and r["method"] == tested
                )
                ref_row = next(
                    r for r in aggregates
                    if r["profile"] == profile and r["scale"] == scale and r["method"] == reference
                )
                pairs: list[tuple[float, float]] = []
                seeds = sorted({r.seed for r in instances if r.profile == profile and r.scale == scale})
                for seed in seeds:
                    t = next(r for r in instances if r.profile == profile and r.scale == scale and r.seed == seed and r.method == tested)
                    ref = next(r for r in instances if r.profile == profile and r.scale == scale and r.seed == seed and r.method == reference)
                    if t.feasible and ref.feasible:
                        pairs.append((t.objective, ref.objective))
                wins = sum(t + 1e-9 < ref for t, ref in pairs)
                losses = sum(t > ref + 1e-9 for t, ref in pairs)
                ties = len(pairs) - wins - losses
                test_obj = test_row["mean_objective_feasible"]
                ref_obj = ref_row["mean_objective_feasible"]
                comparisons.append(
                    {
                        "profile": profile,
                        "scale": scale,
                        "tested_method": tested,
                        "reference_method": reference,
                        "feasibility_rate_delta": test_row["feasibility_rate"] - ref_row["feasibility_rate"],
                        "mean_feasible_objective_delta": (
                            test_obj - ref_obj if test_obj is not None and ref_obj is not None else None
                        ),
                        "mean_feasible_objective_pct": (
                            100.0 * (test_obj - ref_obj) / ref_obj
                            if test_obj is not None and ref_obj not in (None, 0.0) else None
                        ),
                        "mean_runtime_delta_sec": test_row["mean_runtime_sec"] - ref_row["mean_runtime_sec"],
                        "jointly_feasible_instances": len(pairs),
                        "wins": wins,
                        "ties": ties,
                        "losses": losses,
                    }
                )
    return comparisons


def _diagnostics(results: list[InstanceResult]) -> list[dict[str, object]]:
    cases = [r for r in results if not r.feasible]
    cases.extend(
        sorted(
            [r for r in results if r.feasible and r.method == E_ADAPTIVE_METHOD],
            key=lambda row: row.runtime_sec,
            reverse=True,
        )[:4]
    )
    return [
        {
            "profile": row.profile,
            "scale": row.scale,
            "seed": row.seed,
            "method": row.method,
            "feasible": row.feasible,
            "objective": row.objective if row.feasible else None,
            "runtime_sec": row.runtime_sec,
            "violations": list(row.violations),
            "termination_reason": row.termination_reason,
        }
        for row in cases[:20]
    ]


def run_experiment(
    *,
    scales: list[int],
    profiles: list[str],
    instances_per_scale: int,
    base_seed: int,
    adaptive_steps: int,
    patience: int,
) -> ExperimentBundle:
    started = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    results: list[InstanceResult] = []
    for profile in profiles:
        if profile not in PARAMETER_PROFILES:
            raise ValueError(f"unknown profile: {profile}")
        for scale in scales:
            for offset in range(instances_per_scale):
                seed = base_seed + scale * 1000 + offset
                instance = apply_profile(generate_instance(scale, seed), profile)
                for method in METHODS:
                    solved = solve_method(
                        instance,
                        method,
                        adaptive_steps=adaptive_steps,
                        patience=patience,
                    )
                    results.append(_instance_result(profile, solved, instance))
    aggregate = aggregate_results(results)
    comparisons = compare_results(aggregate, results)
    traces = tuple(record for result in results for record in result.trace)
    metadata = {
        "run_started": started,
        "research_question": (
            "Does a nearest/composite portfolio improve on Method D, and can "
            "UCB1 adaptive operator selection improve the quality/runtime trade-off?"
        ),
        "scales": scales,
        "profiles": profiles,
        "instances_per_scale": instances_per_scale,
        "base_seed": base_seed,
        "adaptive_steps": adaptive_steps,
        "patience": patience,
        "methods": METHODS,
        "total_method_runs": len(results),
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    return ExperimentBundle(
        metadata=metadata,
        aggregate=tuple(aggregate),
        comparisons=tuple(comparisons),
        instances=tuple(results),
        diagnostics=tuple(_diagnostics(results)),
        adaptive_trace=traces,
    )


def _write_csv(path: Path, rows: list[dict[str, object]] | tuple[dict[str, object], ...]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _fmt(value: object, digits: int = 3) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):.{digits}f}"


def _markdown(bundle: ExperimentBundle) -> str:
    lines = [
        "# Week 6 Results: Integrated Portfolio and Adaptive Operator Selection",
        "",
        f"Run started: `{bundle.metadata['run_started']}`",
        "",
        str(bundle.metadata["research_question"]),
        "",
        "## Aggregate results",
        "",
        "| Profile | n | Method | Feasible | Rate | Mean objective | Median | Best | Runtime (s) | Initial improvement (%) |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in bundle.aggregate:
        lines.append(
            f"| {row['profile']} | {row['scale']} | {row['method']} | "
            f"{row['feasible_instances']}/{row['instances']} | {row['feasibility_rate']:.3f} | "
            f"{_fmt(row['mean_objective_feasible'])} | {_fmt(row['median_objective_feasible'])} | "
            f"{_fmt(row['best_objective_feasible'])} | {row['mean_runtime_sec']:.6f} | "
            f"{_fmt(row['mean_improvement_from_initial_pct'], 2)} |"
        )
    lines.extend(
        [
            "",
            "## Portfolio comparisons",
            "",
            "Negative objective percentage means the tested method is shorter.",
            "",
            "| Profile | n | Tested | Reference | Feasibility delta | Objective delta (%) | Runtime delta (s) | W/T/L |",
            "|---|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in bundle.comparisons:
        lines.append(
            f"| {row['profile']} | {row['scale']} | {row['tested_method']} | "
            f"{row['reference_method']} | {row['feasibility_rate_delta']:.3f} | "
            f"{_fmt(row['mean_feasible_objective_pct'], 2)} | {row['mean_runtime_delta_sec']:.6f} | "
            f"{row['wins']}/{row['ties']}/{row['losses']} |"
        )
    lines.extend(["", "## Diagnostics", ""])
    if not bundle.diagnostics:
        lines.append("No infeasible or slow diagnostic cases were recorded.")
    for case in bundle.diagnostics:
        lines.append(
            f"- `{case['profile']}` n={case['scale']} seed={case['seed']} "
            f"method={case['method']}: feasible={case['feasible']}, "
            f"runtime={case['runtime_sec']:.6f}s, termination={case['termination_reason']}, "
            f"violations={case['violations']}"
        )
    return "\n".join(lines) + "\n"


def write_outputs(
    bundle: ExperimentBundle,
    output_dir: Path = DEFAULT_RESULTS_DIR,
    *,
    command: list[str] | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": bundle.metadata,
        "aggregate": list(bundle.aggregate),
        "comparisons": list(bundle.comparisons),
        "instances": [result.to_dict() for result in bundle.instances],
        "diagnostics": list(bundle.diagnostics),
        "adaptive_trace": list(bundle.adaptive_trace),
    }
    (output_dir / "week6_results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_csv(output_dir / "week6_aggregate.csv", bundle.aggregate)
    _write_csv(output_dir / "week6_comparison.csv", bundle.comparisons)
    (output_dir / "adaptive_trace.json").write_text(json.dumps(list(bundle.adaptive_trace), indent=2) + "\n", encoding="utf-8")
    _write_csv(output_dir / "adaptive_trace.csv", bundle.adaptive_trace)
    (output_dir / "week6_results.md").write_text(_markdown(bundle), encoding="utf-8")
    command = command or sys.argv
    log = [
        "Week 6 integrated portfolio experiment local run log",
        "",
        f"Run started: {bundle.metadata['run_started']}",
        f"Command: {' '.join(shlex.quote(part) for part in command)}",
        f"Python: {bundle.metadata['python']}",
        f"Platform: {bundle.metadata['platform']}",
        f"Method runs: {bundle.metadata['total_method_runs']}",
        f"Adaptive trace rows: {len(bundle.adaptive_trace)}",
        "",
        "Aggregate results:",
    ]
    for row in bundle.aggregate:
        log.append(
            f"- profile={row['profile']}, scale={row['scale']}, method={row['method']}, "
            f"feasible={row['feasible_instances']}/{row['instances']}, "
            f"mean_objective={row['mean_objective_feasible']}, runtime={row['mean_runtime_sec']:.6f}"
        )
    (output_dir / "run_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", nargs="+", type=int, default=[20, 50, 100])
    parser.add_argument("--profiles", nargs="+", default=list(PARAMETER_PROFILES))
    parser.add_argument("--instances-per-scale", type=int, default=12)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--adaptive-steps", type=int, default=12)
    parser.add_argument("--patience", type=int, default=4)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundle = run_experiment(
        scales=args.scales,
        profiles=args.profiles,
        instances_per_scale=args.instances_per_scale,
        base_seed=args.seed,
        adaptive_steps=args.adaptive_steps,
        patience=args.patience,
    )
    write_outputs(bundle, args.output_dir, command=sys.argv)
    print(json.dumps({"output_dir": str(args.output_dir), "method_runs": len(bundle.instances), "trace_rows": len(bundle.adaptive_trace)}, indent=2))


if __name__ == "__main__":
    main()
