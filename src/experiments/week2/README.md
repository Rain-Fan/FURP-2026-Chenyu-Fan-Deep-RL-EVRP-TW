# Week 2: EVRP-TW Baseline Comparison

This folder is intended for the Week 2 EVRP-TW baseline comparison scripts.
If scripts are not yet present, this README documents the expected layout and
how to prepare the environment.

Expected files (when implemented):

- `compare_week2_baselines.py` — runner that evaluates methods across instance
  scales and writes `results/week2_results.json`.
- `results/week2_results.json` — aggregated results consumed by
  `src/results/generate_research_visualizations.py`.

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
python compare_week2_baselines.py --scales 50 100 200 --seed 20260621 --or-time-limit 8
```

## Notes

- `src/results/generate_research_visualizations.py` expects `results/week2_results.json` to exist; ensure the runner writes that file with the expected schema.
