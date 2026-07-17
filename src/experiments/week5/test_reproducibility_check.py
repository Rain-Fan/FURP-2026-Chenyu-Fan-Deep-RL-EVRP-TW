"""Regression coverage for the Week 5 reproducibility workflow."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import csv
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_reproducibility_check
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


class ReproducibilityFailureTests(unittest.TestCase):
    def test_nonzero_week4_run_writes_failure_summary_and_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            results_dir = Path(directory) / "results"
            failed_run = subprocess.CompletedProcess(args=["week4"], returncode=7, stdout="", stderr="failed")
            successful_run = subprocess.CompletedProcess(args=["week4"], returncode=0, stdout="", stderr="")
            with (
                mock.patch.object(run_reproducibility_check, "parse_args", return_value=mock.Mock(results_dir=results_dir)),
                mock.patch.object(run_reproducibility_check, "run_week4", side_effect=[failed_run, successful_run]),
            ):
                self.assertEqual(run_reproducibility_check.main(), 1)

            summary = (results_dir / "week5_reproducibility.json").read_text(encoding="utf-8")
            self.assertIn('"deterministic_reproducible": false', summary)
            self.assertIn("Week 4 run 1 exited with 7", summary)

    def test_missing_aggregate_csv_writes_failure_summary_and_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            results_dir = Path(directory) / "results"
            successful_run = subprocess.CompletedProcess(args=["week4"], returncode=0, stdout="", stderr="")
            with (
                mock.patch.object(run_reproducibility_check, "parse_args", return_value=mock.Mock(results_dir=results_dir)),
                mock.patch.object(run_reproducibility_check, "run_week4", side_effect=[successful_run, successful_run]),
            ):
                self.assertEqual(run_reproducibility_check.main(), 1)

            summary = (results_dir / "week5_reproducibility.json").read_text(encoding="utf-8")
            self.assertIn('"deterministic_reproducible": false', summary)
            self.assertIn("missing expected aggregate CSV", summary)

    def test_deterministic_csv_difference_writes_failure_summary_and_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            results_dir = Path(directory) / "results"
            successful_run = subprocess.CompletedProcess(args=["week4"], returncode=0, stdout="", stderr="")

            def write_differing_results(run_dir: Path, _log_path: Path) -> subprocess.CompletedProcess[str]:
                run_dir.mkdir(parents=True, exist_ok=True)
                feasibility_rate = "1.0" if run_dir.name == "run_1" else "0.5"
                write_csv(run_dir / "week4_results.csv", feasibility_rate=feasibility_rate, runtime="0.1")
                return successful_run

            with (
                mock.patch.object(run_reproducibility_check, "parse_args", return_value=mock.Mock(results_dir=results_dir)),
                mock.patch.object(run_reproducibility_check, "run_week4", side_effect=write_differing_results),
            ):
                self.assertEqual(run_reproducibility_check.main(), 1)

            summary = (results_dir / "week5_reproducibility.json").read_text(encoding="utf-8")
            markdown_summary = (results_dir / "week5_reproducibility.md").read_text(encoding="utf-8")
            diagnostic = "unequal deterministic cell for ('baseline', 'C_composite_score', '20'), feasibility_rate"
            self.assertIn('"deterministic_reproducible": false', summary)
            self.assertIn(diagnostic, summary)
            self.assertIn("Status: **FAIL**", markdown_summary)
            self.assertIn(diagnostic, markdown_summary)


class ReproducibilityIntegrationTests(unittest.TestCase):
    def test_main_creates_summary_after_two_successful_runs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parent / "run_reproducibility_check.py"), "--output-dir", directory],
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            summary_path = Path(directory) / "week5_reproducibility.json"
            self.assertTrue(summary_path.is_file())
            self.assertIn('"deterministic_match": true', summary_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
