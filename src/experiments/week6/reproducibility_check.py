#!/usr/bin/env python3
"""Verify fixed-seed reproducibility of all Week 6 methods."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for relative in ("src/experiments/week3", "src/experiments/week4", "src/experiments/week6"):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from compare_week3_baselines import generate_instance  # noqa: E402
from compare_week4_methods import PARAMETER_PROFILES, apply_profile  # noqa: E402
from portfolio_solver import METHODS, solve_method  # noqa: E402

DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "results"


def solution_signature(result) -> tuple[object, ...]:
    """Return deterministic algorithmic output, intentionally excluding time."""

    trace = tuple(
        (
            record.action,
            round(record.objective_before, 9),
            round(record.objective_after, 9),
            round(record.reward, 12),
            record.accepted,
            record.moves,
            record.feasible,
            record.termination_reason,
        )
        for record in result.trace
    )
    return (
        result.routes,
        result.feasible,
        round(result.objective, 9) if result.feasible else None,
        result.selected_source,
        trace,
        result.termination_reason,
    )


def _json_signature(signature: tuple[object, ...]) -> list[object]:
    return json.loads(json.dumps(signature))


def run_checks(
    *,
    scales: list[int],
    profiles: list[str],
    instances_per_scale: int,
    repeats: int,
    base_seed: int,
    adaptive_steps: int = 12,
    patience: int = 4,
) -> dict[str, object]:
    if repeats < 2:
        raise ValueError("repeats must be at least 2")
    mismatches: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    checks = 0
    for profile in profiles:
        if profile not in PARAMETER_PROFILES:
            raise ValueError(f"unknown profile: {profile}")
        for scale in scales:
            for offset in range(instances_per_scale):
                seed = base_seed + scale * 1000 + offset
                instance = apply_profile(generate_instance(scale, seed), profile)
                for method in METHODS:
                    signatures = [
                        solution_signature(
                            solve_method(
                                instance,
                                method,
                                adaptive_steps=adaptive_steps,
                                patience=patience,
                            )
                        )
                        for _repeat in range(repeats)
                    ]
                    matches = all(signature == signatures[0] for signature in signatures[1:])
                    checks += 1
                    record = {
                        "profile": profile,
                        "scale": scale,
                        "seed": seed,
                        "method": method,
                        "repeats": repeats,
                        "matches": matches,
                        "signature": _json_signature(signatures[0]),
                    }
                    records.append(record)
                    if not matches:
                        mismatches.append(
                            {
                                **record,
                                "all_signatures": [_json_signature(item) for item in signatures],
                            }
                        )
    return {
        "passed": not mismatches,
        "checks": checks,
        "repeats": repeats,
        "profiles": profiles,
        "scales": scales,
        "instances_per_scale": instances_per_scale,
        "base_seed": base_seed,
        "mismatches": mismatches,
        "records": records,
    }


def write_report(report: dict[str, object], output_dir: Path = DEFAULT_RESULTS_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "reproducibility_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    status = "PASS" if report["passed"] else "FAIL"
    lines = [
        "# Week 6 Reproducibility Check",
        "",
        f"**Status:** {status}",
        "",
        f"- Method-instance checks: {report['checks']}",
        f"- Repeats per check: {report['repeats']}",
        f"- Mismatches: {len(report['mismatches'])}",
        f"- Profiles: {', '.join(report['profiles'])}",
        f"- Scales: {', '.join(str(value) for value in report['scales'])}",
        "",
        "The deterministic signature includes routes, feasibility, rounded objective, "
        "selected construction source, adaptive action outcomes, and termination reason. "
        "Wall-clock runtime is intentionally excluded.",
    ]
    if report["mismatches"]:
        lines.extend(["", "## Mismatches", ""])
        for mismatch in report["mismatches"]:
            lines.append(
                f"- {mismatch['profile']} n={mismatch['scale']} seed={mismatch['seed']} "
                f"method={mismatch['method']}"
            )
    (output_dir / "reproducibility_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", nargs="+", type=int, default=[20, 50, 100])
    parser.add_argument("--profiles", nargs="+", default=list(PARAMETER_PROFILES))
    parser.add_argument("--instances-per-scale", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260813)
    parser.add_argument("--adaptive-steps", type=int, default=12)
    parser.add_argument("--patience", type=int, default=4)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_checks(
        scales=args.scales,
        profiles=args.profiles,
        instances_per_scale=args.instances_per_scale,
        repeats=args.repeats,
        base_seed=args.seed,
        adaptive_steps=args.adaptive_steps,
        patience=args.patience,
    )
    write_report(report, args.output_dir)
    print(json.dumps({"passed": report["passed"], "checks": report["checks"], "mismatches": len(report["mismatches"])}, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
