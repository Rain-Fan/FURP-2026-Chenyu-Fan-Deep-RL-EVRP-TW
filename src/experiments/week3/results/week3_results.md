# Week 3 Controlled Method Evaluation Results

Run started: `2026-07-03 12:38:07 CST`

Research question: Does due-time-priority greedy perform better than nearest-customer greedy on small, medium, and large synthetic EVRP-TW instances?

A = due-time-priority greedy. B = nearest-customer baseline.

## Summary Table

| Method | Role | Customers | Instances | Feasible | Feasibility rate | Mean objective | Mean feasible objective | Std objective | Mean runtime (s) | Mean vehicles | Mean charges | TW viol. | Capacity viol. | Energy viol. | Coverage viol. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A_due_time_priority | tested_method | 20 | 12 | 3 | 0.250 | 767.700 | 777.501 | 19.563 | 0.000250 | 4.000 | 2.667 | 0 | 0 | 0 | 9 |
| B_nearest_customer | baseline | 20 | 12 | 12 | 1.000 | 449.799 | 449.799 | 61.118 | 0.000243 | 2.667 | 1.250 | 0 | 0 | 0 | 0 |
| A_due_time_priority | tested_method | 50 | 12 | 6 | 0.500 | 1907.936 | 1819.997 | 106.148 | 0.001293 | 9.750 | 6.917 | 0 | 0 | 0 | 6 |
| B_nearest_customer | baseline | 50 | 12 | 12 | 1.000 | 758.561 | 758.561 | 77.587 | 0.001344 | 4.250 | 2.333 | 0 | 0 | 0 | 0 |
| A_due_time_priority | tested_method | 100 | 12 | 11 | 0.917 | 3779.576 | 3759.097 | 196.922 | 0.006136 | 18.667 | 15.417 | 0 | 0 | 0 | 1 |
| B_nearest_customer | baseline | 100 | 12 | 12 | 1.000 | 1116.221 | 1116.221 | 64.491 | 0.006811 | 6.583 | 2.083 | 0 | 0 | 0 | 0 |

## A vs B Comparison

| Customers | Feasibility delta | Feasible-objective delta | Runtime delta (s) | Coverage-violation delta |
|---:|---:|---:|---:|---:|
| 20 | -0.750 | 327.701 | 0.000008 | 9 |
| 50 | -0.500 | 1061.437 | -0.000050 | 6 |
| 100 | -0.083 | 2642.877 | -0.000676 | 1 |

## Diagnostic Cases

### A_due_time_priority on synthetic_evrptw_n100_seed20360634

- Scale: 100
- Seed: 20360634
- Objective distance: 4004.842
- Feasible: False
- Vehicles used: 20
- Charge count: 15
- Diagnosis: infeasible route; inspect listed constraint violations
- Violations: ['unserved customers: [89]', 'missing customers: [89]']
- First route: `[0, 85, 22, 96, 82, 93, 45, 104, 0]`

### A_due_time_priority on synthetic_evrptw_n50_seed20310636

- Scale: 50
- Seed: 20310636
- Objective distance: 2052.955
- Feasible: False
- Vehicles used: 10
- Charge count: 8
- Diagnosis: infeasible route; inspect listed constraint violations
- Violations: ['unserved customers: [41, 49]', 'missing customers: [41, 49]']
- First route: `[0, 20, 17, 7, 13, 54, 0]`

### A_due_time_priority on synthetic_evrptw_n50_seed20310633

- Scale: 50
- Seed: 20310633
- Objective distance: 2006.704
- Feasible: False
- Vehicles used: 10
- Charge count: 8
- Diagnosis: infeasible route; inspect listed constraint violations
- Violations: ['unserved customers: [7]', 'missing customers: [7]']
- First route: `[0, 12, 22, 32, 23, 4, 8, 34, 41, 55, 0]`

