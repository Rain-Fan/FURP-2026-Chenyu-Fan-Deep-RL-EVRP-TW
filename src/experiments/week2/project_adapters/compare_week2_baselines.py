#!/usr/bin/env python3
"""Run and compare the Week 2 EVRP-TW baselines."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

from evrp_tw_common import DEFAULT_SCALES, DEFAULT_SEED, EvalResult, generate_instance
from genetic_algorithm import solve_genetic_algorithm
from or_tools_cvrptw import solve_or_tools_cvrptw
from pomo_style import solve_pomo_style


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def run_comparison(scales: list[int], seed: int, or_time_limit: int) -> list[EvalResult]:
    results: list[EvalResult] = []
    for scale in scales:
        instance = generate_instance(scale, seed)
        results.append(solve_pomo_style(instance))
        results.append(solve_genetic_algorithm(instance))
        results.append(solve_or_tools_cvrptw(instance, or_time_limit))
    return results


def write_outputs(results: list[EvalResult]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "week2_results.json").write_text(
        json.dumps([asdict(result) for result in results], indent=2),
        encoding="utf-8",
    )
    with (RESULTS_DIR / "week2_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "method",
                "scale",
                "objective",
                "feasible",
                "runtime_sec",
                "vehicles_used",
                "convergence",
                "violations",
            ],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "method": result.method,
                    "scale": result.scale,
                    "objective": result.objective,
                    "feasible": result.feasible,
                    "runtime_sec": result.runtime_sec,
                    "vehicles_used": result.vehicles_used,
                    "convergence": result.convergence,
                    "violations": "; ".join(result.violations),
                }
            )

    lines = [
        "# Week 2 EVRP-TW Baseline Results",
        "",
        "| Method | Customers | Objective distance | Feasible under E/TW | Runtime (s) | Vehicles | Convergence / notes |",
        "|---|---:|---:|---|---:|---:|---|",
    ]
    for result in results:
        objective = "N/A" if result.objective is None else f"{result.objective:.2f}"
        lines.append(
            "| "
            f"{result.method} | {result.scale} | {objective} | "
            f"{'Yes' if result.feasible else 'No'} | {result.runtime_sec:.3f} | "
            f"{result.vehicles_used} | {result.convergence} |"
        )
    lines.extend(
        [
            "",
            "All objective values are total Euclidean route distance and are only",
            "directly comparable when `Feasible under E/TW` is `Yes`. E/TW",
            "feasibility is checked after each method has inserted or repaired",
            "capacity, time-window, depot-return, and battery/charging constraints.",
        ]
    )
    (RESULTS_DIR / "week2_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scales", nargs="+", type=int, default=list(DEFAULT_SCALES))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--or-time-limit", type=int, default=10)
    args = parser.parse_args()

    results = run_comparison(args.scales, args.seed, args.or_time_limit)
    write_outputs(results)
    print(f"Wrote {len(results)} rows to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
