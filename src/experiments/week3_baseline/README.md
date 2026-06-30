# Week 3 Baseline: Feasibility-First Greedy EVRP-TW

This directory contains the Week 3 baseline reproduction required by the
project hub roadmap: reproduce one baseline and report objective value,
feasibility, and runtime logs.

The baseline is a deterministic feasibility-first greedy construction method:

1. choose the feasible unserved customer with the earliest due-time priority;
2. respect capacity, time-window, battery, charging-station, and depot-return
   constraints during construction;
3. return to the depot or visit a charging station when no customer can be
   served next;
4. validate every final route and record constraint-level violations.

The implementation is pure Python and does not use online data.  All instances
are generated locally from fixed random seeds.

## Run

```bash
python3 src/experiments/week3_baseline/run_week3_baseline.py \
  --scales 10 25 50 \
  --instances-per-scale 32 \
  --seed 20260630
```

Outputs are written to `results/`:

- `week3_results.json`: full metadata, per-instance routes, diagnostics, and
  aggregate results;
- `week3_results.csv`: compact aggregate table;
- `week3_results.md`: Markdown table and diagnostic cases for reports.

## Metrics

The result files report:

- objective distance;
- feasibility rate;
- runtime;
- time-window violations;
- capacity violations;
- energy violations;
- coverage and depot-return violations;
- charge count and charging time;
- hardware, random seed, and solver parameters.
