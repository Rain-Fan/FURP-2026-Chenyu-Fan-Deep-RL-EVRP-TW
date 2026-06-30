# Week 3 Baseline Reproduction: Feasibility-First Greedy EVRP-TW

**Reporting date:** 2026-06-30

**Project:** Deep Reinforcement Learning for the Electric Vehicle Routing
Problem with Time Windows (EVRP-TW)

## 1. Requirement

The Project Hub Week 3 roadmap asks students to reproduce one baseline and
record objective value, feasibility, and runtime logs.  The benchmark guidance
also requires reporting feasibility together with objective value, runtime,
hardware, random seeds, solver parameters, and constraint-level diagnostics.

This report is not a weekly progress log.  It is the standalone Week 3
baseline-reproduction evidence package.

## 2. Baseline

The reproduced baseline is a deterministic feasibility-first greedy
construction method for EVRP-TW.  At each decision step, the solver selects the
feasible unserved customer with the earliest due-time priority.  If no customer
can be served next, it returns to the depot or visits a reachable charging
station.

The baseline checks the following constraints:

- customer service exactly once;
- vehicle capacity;
- customer time windows;
- battery consumption and charging-station visits;
- depot return;
- maximum vehicle count.

## 3. Local Run

The experiment was run locally on generated synthetic EVRP-TW instances.  No
online result data or copied benchmark output was used.

Command:

```bash
python3 src/experiments/week3_baseline/run_week3_baseline.py --scales 10 25 50 --instances-per-scale 32 --seed 20260630
```

Output files:

- `src/experiments/week3_baseline/results/run_log.txt`
- `src/experiments/week3_baseline/results/week3_results.json`
- `src/experiments/week3_baseline/results/week3_results.csv`
- `src/experiments/week3_baseline/results/week3_results.md`

## 4. Parameters

| Item | Value |
|---|---:|
| Base seed | 20260630 |
| Instance sizes | 10, 25, 50 customers |
| Instances per size | 32 |
| Vehicle capacity | 45 |
| Battery capacity | 155.0 |
| Energy rate | 1.0 |
| Speed | 1.0 |
| Charging time per station visit | 18.0 |
| Charging station rule | `max(4, ceil(customers / 12))` |
| Max vehicle rule | `max(3, ceil(customers / 6))` |

## 5. Results

| Customers | Instances | Feasible | Feasibility rate | Mean objective | Mean feasible objective | Mean runtime (s) | Mean vehicles | Mean charges | Time-window violations | Capacity violations | Energy violations | Coverage violations |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 32 | 21 | 0.656 | 450.552 | 441.557 | 0.000064 | 3.000 | 1.406 | 0 | 0 | 0 | 11 |
| 25 | 32 | 1 | 0.031 | 833.218 | 780.085 | 0.000296 | 5.000 | 3.469 | 0 | 0 | 0 | 31 |
| 50 | 32 | 1 | 0.031 | 1536.332 | 1545.652 | 0.001183 | 9.000 | 7.219 | 0 | 0 | 0 | 31 |

## 6. Diagnostic Cases

The baseline remained fast, but feasibility dropped sharply as the instance
size increased.  The main failure mode was coverage: the greedy construction
used all available vehicles before serving every customer.

### Case 1

- Instance: `synthetic_evrptw_n50_seed20310635`
- Objective distance: 1611.423
- Feasible: false
- Vehicles used: 9
- Charge count: 9
- Diagnosis: unserved customers remained after all vehicles were used.

### Case 2

- Instance: `synthetic_evrptw_n50_seed20310657`
- Objective distance: 1607.657
- Feasible: false
- Vehicles used: 9
- Charge count: 8
- Diagnosis: unserved customers remained after all vehicles were used.

### Case 3

- Instance: `synthetic_evrptw_n50_seed20310644`
- Objective distance: 1585.864
- Feasible: false
- Vehicles used: 9
- Charge count: 9
- Diagnosis: unserved customers remained after all vehicles were used.

Full route sequences and violation lists are stored in
`src/experiments/week3_baseline/results/week3_results.json`.

## 7. Interpretation

The baseline is useful as a transparent first reference because it is fast and
auditable.  However, it is not strong enough for medium-size EVRP-TW instances:
it prioritizes immediate feasible customer choices and does not repair earlier
route decisions.  The next experiment should compare this baseline with a
stronger method that includes route splitting, local search, or OR-style
repair.
