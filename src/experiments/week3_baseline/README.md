# Week 3: Controlled Method Evaluation for EVRP-TW

This directory contains the Week 3 controlled experiment.  The purpose is to
evaluate a method properly, not only to show that code runs.

## Research Question

Does a due-time-priority greedy policy perform better than a nearest-customer
greedy baseline on small, medium, and large synthetic EVRP-TW instances?

## Methods

- `A_due_time_priority`: tested method.  Chooses the feasible unserved customer
  with the earliest due-time priority.
- `B_nearest_customer`: baseline.  Chooses the feasible unserved customer with
  the shortest current travel distance.

Both methods use the same instance set, coordinates, objective definition,
feasibility checker, vehicle constraints, battery constraints, charging rules,
and stopping condition.

## Run

```bash
python3 src/experiments/week3_baseline/run_week3_baseline.py \
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

## Metrics

The result files report objective distance, feasibility rate, runtime,
time-window violations, capacity violations, energy violations, coverage
violations, charge count, hardware, random seed, and solver parameters.
