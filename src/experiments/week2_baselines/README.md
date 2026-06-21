# Week 2 Baselines: EVRP-TW Recreation and Comparison

This directory contains the Week 2 baseline recreation required by the project
hub lab: POMO-style construction, GA, and OR-based methods compared under
added electric-vehicle and time-window constraints.

## Methods

1. **POMO-style multi-start masked greedy**
   - Recreates the POMO inference idea of many parallel starts and selecting
     the best rollout.
   - Adds EVRP-TW feasibility masks for capacity and time windows, then inserts
     charging stations when battery would be insufficient.

2. **GA permutation + EV/TW repair**
   - Recreates a VRPTW-style genetic algorithm around customer permutations.
   - Uses split, repair, and penalty evaluation to enforce capacity,
     time-window, depot-return, and battery constraints.

3. **OR-Tools CVRPTW + charging repair**
   - Recreates the OR component of a hybrid OR/local-search baseline.
   - Solves customer sequencing with OR-Tools capacity and time dimensions,
     then inserts charging stations and validates electric feasibility.

## Run

```bash
python run_week2_baselines.py --scales 50 100 200 --seed 20260621
```

Outputs are written to `results/`:

- `week2_results.json`: full routes and validation details;
- `week2_results.csv`: compact machine-readable comparison table;
- `week2_results.md`: Markdown table for reports.

All methods use the same synthetic EVRP-TW instance generator and the same
post-run feasibility checker.  Objective values are total Euclidean route
distance and should only be compared when the solution is feasible under the
added E/TW constraints.
