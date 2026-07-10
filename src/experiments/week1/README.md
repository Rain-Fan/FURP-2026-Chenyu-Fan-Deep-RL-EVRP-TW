# Week 1: OR-Tools Routing Baselines

Week 1 reproduces small OR-Tools-style routing examples for TSP, VRP, CVRP,
and VRPTW.  The scripts follow the same basic structure as the OR-Tools
documentation examples: create data, create the routing model, register
callbacks, set dimensions or constraints, solve, and print or export the
solution.

## Files

- `tsp.py`: travelling-salesman baseline.
- `vrp.py`: multi-vehicle routing baseline.
- `cvrp.py`: capacity-constrained VRP baseline.
- `vrptw.py`: VRP with time-window baseline.
- `routing_data.py`: shared 17-node data used by the four baselines.
- `or_tools_common.py`: shared OR-Tools helper functions.
- `compare_or_tools_baselines.py`: local runner that writes result artifacts.

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

# upgrade pip and install dependencies (recommended: use top-level requirements)
python -m pip install --upgrade pip
# Option A (recommended): install top-level requirements for the whole repo
python -m pip install -r ../../../requirements.txt
# Option B: install experiment-specific requirements (works inside this folder)
python -m pip install -r requirements.txt
```

Notes:
- OR-Tools binary releases may have platform-specific constraints. If
  installation fails, consult OR-Tools installation docs for your OS.

## Run

```bash
python -m pip install -r requirements.txt
python compare_or_tools_baselines.py
```

## Outputs

- `results/baseline_results.json`
- `results/route_tables.md`
- `results/baseline_routes.png`
