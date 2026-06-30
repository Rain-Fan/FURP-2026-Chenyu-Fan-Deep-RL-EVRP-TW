# Week 3 Controlled Method Evaluation: EVRP-TW Greedy Policies

**Reporting date:** 2026-06-30

**Project:** Deep Reinforcement Learning for the Electric Vehicle Routing
Problem with Time Windows (EVRP-TW)

## 1. Goal

The Week 3 task is no longer only to make a method run.  The goal is to
evaluate a method properly: define a fair comparison, run controlled
experiments, explain the metrics, and write a short but convincing report.

This report evaluates whether a due-time-priority greedy policy performs
better than a nearest-customer greedy baseline on small, medium, and large
synthetic EVRP-TW instances.

## 2. Four Questions Before the Experiment

**Tested method:** `A_due_time_priority`

This method chooses the feasible unserved customer with the earliest due time.
It is designed to respect time windows earlier in the route-construction
process.

**Baseline:** `B_nearest_customer`

This baseline chooses the feasible unserved customer with the shortest travel
distance from the current node.  It is a simple distance-first construction
baseline.

**Main difference:**

Both methods use the same feasibility checks and repair rules.  The only
intended decision difference is the customer-selection priority:

- Method A prioritizes time-window urgency.
- Baseline B prioritizes immediate travel distance.

**Research question:**

Does due-time-priority greedy improve feasibility or objective value compared
with nearest-customer greedy when EVRP-TW constraints are active?

## 3. Fairness Controls

To make the comparison fair, both methods use:

- the same generated instance set and random seeds;
- the same coordinate data and distance matrix;
- the same objective definition: total route distance;
- the same vehicle capacity, battery capacity, energy rate, charging time, and
  maximum-vehicle rule;
- the same feasibility checker;
- the same stopping condition.

The tested scales are:

- small: 20 customers;
- medium: 50 customers;
- large: 100 customers.

Each scale contains 12 generated instances.  The methods are deterministic, so
the experiment uses repeated instances rather than repeated stochastic trials.

## 4. Local Run

The data below was generated locally by running the repository code.  No online
result table or copied benchmark output was used.

Command:

```bash
python3 src/experiments/week3_baseline/run_week3_baseline.py --scales 20 50 100 --instances-per-scale 12 --seed 20260630
```

Output files:

- `src/experiments/week3_baseline/results/run_log.txt`
- `src/experiments/week3_baseline/results/week3_results.json`
- `src/experiments/week3_baseline/results/week3_results.csv`
- `src/experiments/week3_baseline/results/week3_comparison.csv`
- `src/experiments/week3_baseline/results/week3_results.md`

## 5. Metrics

| Metric | Meaning |
|---|---|
| Objective distance | Total route distance. Lower is better only when comparing feasible solutions. |
| Feasibility rate | Fraction of instances where all customers are served without constraint violations. |
| Runtime | Local wall-clock solve time per instance. |
| Time-window violations | Number of late arrivals after waiting is applied. |
| Capacity violations | Number of routes exceeding vehicle capacity. |
| Energy violations | Number of battery failures before reaching the next node. |
| Coverage violations | Missing, duplicated, or unexpected customer visits. |
| Charge count | Number of charging-station visits. |

## 6. Experimental Setup

| Item | Value |
|---|---:|
| Base seed | 20260630 |
| Instance sizes | 20, 50, 100 customers |
| Instances per size | 12 |
| Vehicle capacity | 55 |
| Battery capacity | 185.0 |
| Energy rate | 1.0 |
| Speed | 1.0 |
| Charging time per station visit | 18.0 |
| Charging station rule | `max(5, ceil(customers / 14))` |
| Max vehicle rule | `max(4, ceil(customers / 5))` |

## 7. Summary Results

| Method | Role | Customers | Instances | Feasible | Feasibility rate | Mean objective | Mean feasible objective | Std objective | Mean runtime (s) | Mean vehicles | Mean charges | TW viol. | Capacity viol. | Energy viol. | Coverage viol. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A_due_time_priority | tested_method | 20 | 12 | 3 | 0.250 | 767.700 | 777.501 | 19.563 | 0.000220 | 4.000 | 2.667 | 0 | 0 | 0 | 9 |
| B_nearest_customer | baseline | 20 | 12 | 12 | 1.000 | 449.799 | 449.799 | 61.118 | 0.000218 | 2.667 | 1.250 | 0 | 0 | 0 | 0 |
| A_due_time_priority | tested_method | 50 | 12 | 6 | 0.500 | 1907.936 | 1819.997 | 106.148 | 0.001266 | 9.750 | 6.917 | 0 | 0 | 0 | 6 |
| B_nearest_customer | baseline | 50 | 12 | 12 | 1.000 | 758.561 | 758.561 | 77.587 | 0.001305 | 4.250 | 2.333 | 0 | 0 | 0 | 0 |
| A_due_time_priority | tested_method | 100 | 12 | 11 | 0.917 | 3779.576 | 3759.097 | 196.922 | 0.006335 | 18.667 | 15.417 | 0 | 0 | 0 | 1 |
| B_nearest_customer | baseline | 100 | 12 | 12 | 1.000 | 1116.221 | 1116.221 | 64.491 | 0.007054 | 6.583 | 2.083 | 0 | 0 | 0 | 0 |

## 8. A vs B Comparison

| Customers | Feasibility delta | Feasible-objective delta | Runtime delta (s) | Coverage-violation delta |
|---:|---:|---:|---:|---:|
| 20 | -0.750 | 327.701 | 0.000002 | 9 |
| 50 | -0.500 | 1061.437 | -0.000039 | 6 |
| 100 | -0.083 | 2642.877 | -0.000719 | 1 |

Negative feasibility delta means Method A was less feasible than Baseline B.
Positive feasible-objective delta means Method A had a longer route distance
among feasible solutions.

## 9. Discussion

The due-time-priority method did not outperform the nearest-customer baseline
on this controlled instance set.  Baseline B was feasible on all tested
instances, while Method A failed on 9 small instances, 6 medium instances, and
1 large instance.  The main failure mode was coverage: Method A often used all
available vehicles before all customers were served.

The reason is that a due-time-only priority can produce spatially inefficient
routes.  It serves urgent customers early, but it may jump across the plane,
consume more battery, require more charging, and open more vehicle routes.
This makes later customers harder to insert.  The nearest-customer baseline is
simpler, but in this generated Euclidean setting it preserves route compactness
and therefore uses fewer vehicles and charges.

Runtime differences were very small.  Method A was slightly faster at 50 and
100 customers, but the route quality and feasibility loss were much more
important than the runtime difference.

## 10. Failure Cases

### Case 1

- Method: `A_due_time_priority`
- Instance: `synthetic_evrptw_n100_seed20360634`
- Objective distance: 4004.842
- Feasible: false
- Vehicles used: 20
- Charge count: 15
- Failure reason: customer 89 remained unserved after all vehicles were used.

### Case 2

- Method: `A_due_time_priority`
- Instance: `synthetic_evrptw_n50_seed20310636`
- Objective distance: 2052.955
- Feasible: false
- Vehicles used: 10
- Charge count: 8
- Failure reason: customers 41 and 49 remained unserved.

### Case 3

- Method: `A_due_time_priority`
- Instance: `synthetic_evrptw_n50_seed20310633`
- Objective distance: 2006.704
- Feasible: false
- Vehicles used: 10
- Charge count: 8
- Failure reason: customer 7 remained unserved.

Full route sequences and violation lists are stored in
`src/experiments/week3_baseline/results/week3_results.json`.

## 11. Conclusion

For this Week 3 controlled experiment, the nearest-customer baseline is better
than the due-time-priority method under the current instance generator and
constraints.  It has higher feasibility, lower objective distance, fewer
vehicles, and fewer charging visits.

The next improvement should combine both ideas rather than using due time
alone: a weighted score using distance, due-time slack, remaining battery,
route load, and depot-return reserve should be tested against the same
baseline under the same controlled setup.
