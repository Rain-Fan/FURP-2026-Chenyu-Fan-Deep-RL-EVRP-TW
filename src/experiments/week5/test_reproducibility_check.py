"""Regression coverage for the Week 5 reproducibility workflow."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_reproducibility_check import compare_aggregate_csv


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
WEEK4_RUNNER = REPOSITORY_ROOT / "src" / "experiments" / "week4" / "compare_week4_methods.py"


def run_week4(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    """Run the Week 4 experiment from the repository root."""
    return subprocess.run(
        [sys.executable, str(WEEK4_RUNNER), *arguments],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def write_csv(path: Path, feasibility_rate: str, runtime: str) -> Path:
    """Write one aggregate row for result-table comparison tests."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["profile", "method", "scale", "feasibility_rate", "mean_runtime_sec"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "profile": "baseline",
                "method": "C_composite_score",
                "scale": "20",
                "feasibility_rate": feasibility_rate,
                "mean_runtime_sec": runtime,
            }
        )
    return path


class Week4ResultsDirectoryTests(unittest.TestCase):
    def test_week4_runner_writes_to_explicit_results_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "alternate-results"
            result = run_week4(
                [
                    "--scales",
                    "20",
                    "--instances-per-scale",
                    "1",
                    "--profiles",
                    "baseline",
                    "--results-dir",
                    str(destination),
                ]
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((destination / "week4_results.csv").is_file())


class AggregateComparisonTests(unittest.TestCase):
    def test_comparison_ignores_runtime_but_reports_changed_feasibility(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_path = Path(directory)
            first = write_csv(temporary_path / "first.csv", feasibility_rate="1.0", runtime="0.1")
            equal = write_csv(temporary_path / "equal.csv", feasibility_rate="1.0", runtime="9.9")
            changed = write_csv(temporary_path / "changed.csv", feasibility_rate="0.5", runtime="0.1")
            self.assertEqual(compare_aggregate_csv(first, equal), [])
            self.assertIn("feasibility_rate", "\n".join(compare_aggregate_csv(first, changed)))


if __name__ == "__main__":
    unittest.main()
