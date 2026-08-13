#!/usr/bin/env python3
"""Deterministic training/evaluation checks for the Week 7 RL prototype."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from train_week7_rl import TrainingConfig, run_experiment

DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "results"


def result_signature(bundle) -> str:
    """Hash deterministic scientific outputs, excluding runtime and timestamps."""

    rows = []
    for result in bundle.instances:
        rows.append(
            {
                "profile": result.profile,
                "scale": result.scale,
                "seed": result.seed,
                "method": result.method,
                "feasible": result.feasible,
                "objective": round(result.objective, 9) if result.feasible else None,
                "routes": [list(route) for route in result.routes],
                "actions": [record.get("action") for record in result.trace],
                "accepted": [record.get("accepted") for record in result.trace],
            }
        )
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_reproducibility_check(config: TrainingConfig, *, repeats: int = 2) -> dict[str, object]:
    if repeats < 2:
        raise ValueError("repeats must be at least two")
    model_hashes: list[str] = []
    result_hashes: list[str] = []
    run_summaries = []
    for repeat in range(repeats):
        bundle, agent = run_experiment(config)
        model_hashes.append(agent.parameter_hash())
        result_hashes.append(result_signature(bundle))
        run_summaries.append(
            {
                "repeat": repeat,
                "model_hash": model_hashes[-1],
                "result_hash": result_hashes[-1],
                "training_episodes": bundle.metadata["training"]["episodes"],
                "held_out_method_runs": bundle.metadata["held_out_method_runs"],
            }
        )
    mismatch_count = int(len(set(model_hashes)) != 1) + int(len(set(result_hashes)) != 1)
    return {
        "checks": 2,
        "repeats": repeats,
        "mismatch_count": mismatch_count,
        "model_hashes": model_hashes,
        "result_hashes": result_hashes,
        "runs": run_summaries,
        "config": {
            **config.__dict__,
            "scales": list(config.scales),
            "profiles": list(config.profiles),
        },
    }


def write_report(report: dict[str, object], output_dir: Path = DEFAULT_RESULTS_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "reproducibility_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    status = "PASS" if report["mismatch_count"] == 0 else "FAIL"
    lines = [
        "# Week 7 Reproducibility Report", "",
        f"Status: **{status}**", "",
        f"Repeated deterministic checks: {report['checks']}",
        f"Mismatch count: {report['mismatch_count']}", "",
        "## Runs", "",
        "| Repeat | Model hash | Result hash | Training episodes | Held-out method runs |",
        "|---:|---|---|---:|---:|",
    ]
    for row in report["runs"]:
        lines.append(
            f"| {row['repeat']} | `{row['model_hash']}` | `{row['result_hash']}` | "
            f"{row['training_episodes']} | {row['held_out_method_runs']} |"
        )
    lines.extend(["", "Runtime and timestamps are intentionally excluded from signatures.", ""])
    (output_dir / "reproducibility_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--repeats", type=int, default=2)
    args = parser.parse_args()
    config = TrainingConfig(
        scales=(20, 50), profiles=("baseline", "tight_tw"),
        train_instances=2, eval_instances=2,
        train_seed=30300013, eval_seed=40400013,
        epochs=2, max_steps=6, patience=3,
        hidden_dim=16, batch_size=8, replay_capacity=500,
        target_sync=20, agent_seed=20260813,
    )
    report = run_reproducibility_check(config, repeats=args.repeats)
    write_report(report, args.output_dir)
    print(json.dumps({"mismatch_count": report["mismatch_count"], "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
