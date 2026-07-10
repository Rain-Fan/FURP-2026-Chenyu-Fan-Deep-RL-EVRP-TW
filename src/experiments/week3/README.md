# Week 3: Controlled Greedy-Policy Comparison

This folder is intended for the Week 3 controlled greedy-policy experiments.
If scripts are not yet present, this README documents the expected layout and
how to prepare the environment.

Expected files (when implemented):

- `compare_week3_baselines.py` — runner that evaluates the controlled greedy
  policy vs baselines and writes `results/week3_results.json` with `aggregate`,
  `instances`, and `comparison` sections consumed by visualization scripts.
- `results/week3_results.json` — aggregated results used by `src/results`.

## Environment

- Recommended Python: 3.10 or 3.11

Create and activate a virtual environment, then install dependencies:

```bash
# create venv
python -m venv .venv
# activate (macOS / Linux)
source .venv/bin/activate
# activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# upgrade pip and install dependencies
python -m pip install --upgrade pip
# Option A (recommended): install top-level requirements for the whole repo
python -m pip install -r ../../../requirements.txt
# Option B: if a per-experiment requirements.txt is added later
python -m pip install -r requirements.txt
```

## Run (example)

```bash
# placeholder — replace with the actual runner once implemented
python compare_week3_baselines.py --scales 20 50 100 --instances-per-scale 12 --seed 20260630
```

## Notes

- `src/results/generate_research_visualizations.py` expects `results/week3_results.json` with the fields used in its generators (`aggregate`, `instances`, `comparison`). Make sure the runner writes the JSON in the expected format.
