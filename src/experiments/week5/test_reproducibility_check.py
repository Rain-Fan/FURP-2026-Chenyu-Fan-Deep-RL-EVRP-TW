"""Regression coverage for the Week 5 reproducibility workflow."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
