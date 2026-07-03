# Week 3: Controlled Method Evaluation for EVRP-TW

This directory contains the Week 3 controlled experiment.  The purpose is to
evaluate a method properly, not only to show that code runs.

The Python files in this folder are project-written experiment wrappers and
greedy selection rules for the controlled comparison.  They are not official
algorithm source files.  Official upstream source files used as references are
kept in `../official_sources/`.

## Research Question

Does a due-time-priority greedy policy perform better than a nearest-customer
greedy baseline on small, medium, and large synthetic EVRP-TW instances?

## Methods

- `due_time_priority.py`: tested method.  Chooses the feasible unserved customer
  with the earliest due-time priority.
- `nearest_customer.py`: baseline.  Chooses the feasible unserved customer with
  the shortest current travel distance.

`compare_week3_baselines.py` runs the controlled A-vs-B comparison.

Both methods use the same instance set, coordinates, objective definition,
feasibility checker, vehicle constraints, battery constraints, charging rules,
and stopping condition.

## Run

```bash
python3 src/experiments/week3/compare_week3_baselines.py \
  --scales 20 50 100 \
  --instances-per-scale 12 \
  --seed 20260630
```

Outputs are written to `results/`:

- `run_log.txt`: local command, environment, and summary;
- `week3_results.json`: full metadata, per-instance routes, diagnostics, and
  aggregate results;
- `week3_results.csv`: aggregate method-by-scale table;
- `week3_comparison.csv`: A-vs-B comparison table;
- `week3_results.md`: cleaned summary table and diagnostic cases.

## Focused Failure-Case Procedure

After the standard A-vs-B run, inspect deliberately difficult cases for about
2 hours:

- tight time windows: identify which customer window causes infeasibility;
- too few vehicles or too little capacity: estimate the minimum fleet size or
  capacity needed to recover feasibility;
- uneven customer distribution: check whether the longer routes are spatially
  reasonable.

For each failed case, record the instance, violated constraint, route step
where the issue first appears, and a possible repair strategy.

## Metrics

The result files report objective distance, feasibility rate, runtime,
time-window violations, capacity violations, energy violations, coverage
violations, charge count, hardware, random seed, and solver parameters.
