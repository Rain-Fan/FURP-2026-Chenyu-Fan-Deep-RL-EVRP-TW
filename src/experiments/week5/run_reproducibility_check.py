#!/usr/bin/env python3
"""Run the Week 4 experiment twice and check deterministic aggregate results."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
WEEK4_RUNNER = REPOSITORY_ROOT / "src" / "experiments" / "week4" / "compare_week4_methods.py"
DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "results"
KEY_COLUMNS = ("profile", "method", "scale")
NONDETERMINISTIC_COLUMNS = {"mean_runtime_sec", "runtime_std_sec"}
WEEK4_ARGUMENTS = (
    "--scales",
    "20",
    "50",
    "100",
    "--instances-per-scale",
    "12",
    "--seed",
    "20260706",
    "--profiles",
    "baseline",
    "tight_tw",
    "small_battery",
)


def read_aggregate_csv(path: Path) -> tuple[list[str], dict[tuple[str, str, str], dict[str, str]], list[str]]:
    """Read an aggregate table, returning headers, rows indexed by their stable key, and errors."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        errors: list[str] = []
        missing_key_columns = [column for column in KEY_COLUMNS if column not in columns]
        if missing_key_columns:
            return columns, {}, [f"{path}: missing key columns: {', '.join(missing_key_columns)}"]

        rows: dict[tuple[str, str, str], dict[str, str]] = {}
        for line_number, row in enumerate(reader, start=2):
            key = tuple(row[column] for column in KEY_COLUMNS)
            if key in rows:
                errors.append(f"{path}: duplicate row for key {key} at line {line_number}")
            rows[key] = row
    return columns, rows, errors


def compare_aggregate_csv(first: Path, second: Path) -> list[str]:
    """Return deterministic differences between aggregate tables keyed by profile/method/scale."""
    first_columns, first_rows, first_errors = read_aggregate_csv(first)
    second_columns, second_rows, second_errors = read_aggregate_csv(second)
    differences = [*first_errors, *second_errors]

    for column in sorted(set(first_columns) - set(second_columns)):
        differences.append(f"missing column in second CSV: {column}")
    for column in sorted(set(second_columns) - set(first_columns)):
        differences.append(f"unexpected column in second CSV: {column}")

    for key in sorted(set(first_rows) - set(second_rows)):
        differences.append(f"missing row in second CSV: {key}")
    for key in sorted(set(second_rows) - set(first_rows)):
        differences.append(f"unexpected row in second CSV: {key}")

    common_columns = (set(first_columns) & set(second_columns)) - set(KEY_COLUMNS) - NONDETERMINISTIC_COLUMNS
    for key in sorted(set(first_rows) & set(second_rows)):
        for column in sorted(common_columns):
            if first_rows[key][column] != second_rows[key][column]:
                differences.append(
                    f"unequal deterministic cell for {key}, {column}: "
                    f"{first_rows[key][column]!r} != {second_rows[key][column]!r}"
                )
    return differences


def run_week4(results_dir: Path, log_path: Path) -> subprocess.CompletedProcess[str]:
    """Run the fixed Week 4 configuration and retain its complete console log."""
    command = [sys.executable, str(WEEK4_RUNNER), *WEEK4_ARGUMENTS, "--results-dir", str(results_dir)]
    result = subprocess.run(command, cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=False)
    log_path.write_text(result.stdout + result.stderr, encoding="utf-8")
    return result


def write_summary(
    results_dir: Path,
    run_results: list[subprocess.CompletedProcess[str]],
    differences: list[str],
) -> None:
    """Write machine- and human-readable reproducibility evidence."""
    summary = {
        "deterministic_reproducible": not differences and all(result.returncode == 0 for result in run_results),
        "configuration": {"week4_arguments": list(WEEK4_ARGUMENTS)},
        "runs": [
            {"returncode": result.returncode, "results_dir": str(results_dir / f"run_{index}")}
            for index, result in enumerate(run_results, start=1)
        ],
        "differences": differences,
        "environment": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        },
    }
    (results_dir / "week5_reproducibility.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    status = "PASS" if summary["deterministic_reproducible"] else "FAIL"
    lines = [
        "# Week 5 Reproducibility Check",
        "",
        f"Status: **{status}**",
        "",
        "The aggregate CSV comparison excludes measured runtime columns because runtime varies with system load.",
        "",
        "## Fixed Week 4 Configuration",
        "",
        f"`{sys.executable} {WEEK4_RUNNER} {' '.join(WEEK4_ARGUMENTS)}`",
        "",
        "## Result",
        "",
    ]
    if differences:
        lines.extend(f"- {difference}" for difference in differences)
    else:
        lines.append("- All deterministic aggregate cells matched across both runs.")
    (results_dir / "week5_reproducibility.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    run_results = [
        run_week4(args.results_dir / f"run_{index}", args.results_dir / f"run_{index}.log")
        for index in (1, 2)
    ]
    differences: list[str] = []
    if any(result.returncode != 0 for result in run_results):
        differences.extend(
            f"Week 4 run {index} exited with {result.returncode}"
            for index, result in enumerate(run_results, start=1)
            if result.returncode != 0
        )
    else:
        first_csv = args.results_dir / "run_1" / "week4_results.csv"
        second_csv = args.results_dir / "run_2" / "week4_results.csv"
        missing_csvs = [path for path in (first_csv, second_csv) if not path.is_file()]
        differences.extend(f"missing expected aggregate CSV: {path}" for path in missing_csvs)
        if not missing_csvs:
            differences.extend(compare_aggregate_csv(first_csv, second_csv))

    write_summary(args.results_dir, run_results, differences)
    return 1 if differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
