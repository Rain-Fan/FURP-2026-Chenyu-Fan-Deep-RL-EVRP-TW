# Week 4 Method-Improvement Results

Run started: `2026-07-17 15:49:39 CST`

Research question: does a composite-score greedy with feasibility-aware 2-opt (Method C) recover the feasibility and route quality lost by the Week 3 due-time-only method (A), and how does it compare with the nearest-customer baseline (B) across scales and stress profiles?

C = composite-score greedy + 2-opt (tested). A = week3 due-time greedy. B = nearest-customer baseline.

## Summary Table (by profile x scale x method)

| Profile | Method | Customers | Instances | Feasible | Feas. rate | Mean feas. objective | Mean runtime (s) | Mean vehicles | Mean charges | Mean 2-opt moves | Mean 2-opt gain | Coverage viol. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | C_composite_score | 20 | 12 | 12 | 1.000 | 437.019 | 0.000997 | 2.750 | 1.333 | 2.417 | 15.726 | 0 |
| baseline | A_due_time_priority | 20 | 12 | 3 | 0.250 | 753.539 | 0.000248 | 4.000 | 2.583 | 0.000 | 0.000 | 9 |
| baseline | B_nearest_customer | 20 | 12 | 12 | 1.000 | 449.479 | 0.000250 | 2.750 | 1.250 | 0.000 | 0.000 | 0 |
| baseline | C_composite_score | 50 | 12 | 12 | 1.000 | 759.225 | 0.006649 | 4.250 | 3.000 | 8.917 | 36.530 | 0 |
| baseline | A_due_time_priority | 50 | 12 | 7 | 0.583 | 1929.138 | 0.001345 | 9.917 | 7.333 | 0.000 | 0.000 | 5 |
| baseline | B_nearest_customer | 50 | 12 | 12 | 1.000 | 724.769 | 0.001387 | 4.167 | 2.167 | 0.000 | 0.000 | 0 |
| baseline | C_composite_score | 100 | 12 | 12 | 1.000 | 1115.384 | 0.029558 | 6.667 | 3.333 | 25.417 | 87.347 | 0 |
| baseline | A_due_time_priority | 100 | 12 | 12 | 1.000 | 3833.416 | 0.006608 | 18.917 | 15.833 | 0.000 | 0.000 | 0 |
| baseline | B_nearest_customer | 100 | 12 | 12 | 1.000 | 1132.484 | 0.007252 | 6.833 | 2.000 | 0.000 | 0.000 | 0 |
| tight_tw | C_composite_score | 20 | 12 | 12 | 1.000 | 436.872 | 0.000994 | 2.833 | 1.250 | 3.083 | 22.982 | 0 |
| tight_tw | A_due_time_priority | 20 | 12 | 4 | 0.333 | 767.741 | 0.000247 | 4.000 | 2.750 | 0.000 | 0.000 | 8 |
| tight_tw | B_nearest_customer | 20 | 12 | 12 | 1.000 | 449.479 | 0.000240 | 2.750 | 1.250 | 0.000 | 0.000 | 0 |
| tight_tw | C_composite_score | 50 | 12 | 12 | 1.000 | 768.460 | 0.007193 | 4.583 | 2.667 | 11.667 | 44.345 | 0 |
| tight_tw | A_due_time_priority | 50 | 12 | 8 | 0.667 | 1912.130 | 0.001361 | 10.000 | 7.167 | 0.000 | 0.000 | 4 |
| tight_tw | B_nearest_customer | 50 | 12 | 12 | 1.000 | 723.998 | 0.001370 | 4.167 | 2.167 | 0.000 | 0.000 | 0 |
| tight_tw | C_composite_score | 100 | 12 | 12 | 1.000 | 1211.183 | 0.029546 | 7.167 | 4.167 | 29.333 | 101.582 | 0 |
| tight_tw | A_due_time_priority | 100 | 12 | 11 | 0.917 | 3853.121 | 0.006769 | 19.250 | 15.667 | 0.000 | 0.000 | 1 |
| tight_tw | B_nearest_customer | 100 | 12 | 12 | 1.000 | 1123.096 | 0.007441 | 6.833 | 1.750 | 0.000 | 0.000 | 0 |
| small_battery | C_composite_score | 20 | 12 | 11 | 0.917 | 464.919 | 0.000619 | 3.417 | 1.833 | 1.833 | 8.683 | 1 |
| small_battery | A_due_time_priority | 20 | 12 | 0 | 0.000 | NA | 0.000229 | 4.000 | 3.083 | 0.000 | 0.000 | 12 |
| small_battery | B_nearest_customer | 20 | 12 | 12 | 1.000 | 471.682 | 0.000243 | 3.583 | 1.583 | 0.000 | 0.000 | 0 |
| small_battery | C_composite_score | 50 | 12 | 12 | 1.000 | 834.312 | 0.004295 | 6.083 | 3.667 | 7.250 | 25.458 | 0 |
| small_battery | A_due_time_priority | 50 | 12 | 0 | 0.000 | NA | 0.001289 | 10.000 | 8.917 | 0.000 | 0.000 | 12 |
| small_battery | B_nearest_customer | 50 | 12 | 12 | 1.000 | 843.980 | 0.001371 | 5.750 | 4.083 | 0.000 | 0.000 | 0 |
| small_battery | C_composite_score | 100 | 12 | 12 | 1.000 | 1225.524 | 0.022293 | 8.583 | 6.250 | 21.750 | 63.781 | 0 |
| small_battery | A_due_time_priority | 100 | 12 | 0 | 0.000 | NA | 0.006307 | 20.000 | 17.750 | 0.000 | 0.000 | 12 |
| small_battery | B_nearest_customer | 100 | 12 | 12 | 1.000 | 1168.792 | 0.006782 | 8.083 | 5.417 | 0.000 | 0.000 | 0 |

## Method C vs References

Positive feasibility delta = C is more often feasible. Negative objective delta = C finds shorter feasible routes.

| Profile | Customers | Reference | Feasibility delta | Feasible-objective delta | Runtime delta (s) | Coverage-viol. delta |
|---|---:|---|---:|---:|---:|---:|
| baseline | 20 | A_due_time_priority | 0.750 | -316.520 | 0.000750 | -9 |
| baseline | 20 | B_nearest_customer | 0.000 | -12.460 | 0.000748 | 0 |
| baseline | 50 | A_due_time_priority | 0.417 | -1169.912 | 0.005304 | -5 |
| baseline | 50 | B_nearest_customer | 0.000 | 34.457 | 0.005262 | 0 |
| baseline | 100 | A_due_time_priority | 0.000 | -2718.032 | 0.022950 | 0 |
| baseline | 100 | B_nearest_customer | 0.000 | -17.100 | 0.022307 | 0 |
| small_battery | 20 | A_due_time_priority | 0.917 | NA | 0.000390 | -11 |
| small_battery | 20 | B_nearest_customer | -0.083 | -6.763 | 0.000376 | 1 |
| small_battery | 50 | A_due_time_priority | 1.000 | NA | 0.003007 | -12 |
| small_battery | 50 | B_nearest_customer | 0.000 | -9.667 | 0.002924 | 0 |
| small_battery | 100 | A_due_time_priority | 1.000 | NA | 0.015986 | -12 |
| small_battery | 100 | B_nearest_customer | 0.000 | 56.732 | 0.015511 | 0 |
| tight_tw | 20 | A_due_time_priority | 0.667 | -330.869 | 0.000747 | -8 |
| tight_tw | 20 | B_nearest_customer | 0.000 | -12.607 | 0.000754 | 0 |
| tight_tw | 50 | A_due_time_priority | 0.333 | -1143.669 | 0.005832 | -4 |
| tight_tw | 50 | B_nearest_customer | 0.000 | 44.462 | 0.005823 | 0 |
| tight_tw | 100 | A_due_time_priority | 0.083 | -2641.938 | 0.022776 | -1 |
| tight_tw | 100 | B_nearest_customer | 0.000 | 88.087 | 0.022104 | 0 |

## Diagnostic Cases

### A_due_time_priority on synthetic_evrptw_n100_seed20360714_tight_tw (tight_tw)

- Scale: 100
- Objective distance: 4054.870
- Feasible: False
- Vehicles used: 20
- 2-opt moves: 0
- Diagnosis: infeasible route; inspect listed constraint violations
- Violations: ['unserved customers: [88]', 'missing customers: [88]']

### A_due_time_priority on synthetic_evrptw_n100_seed20360717_small_battery (small_battery)

- Scale: 100
- Objective distance: 3266.965
- Feasible: False
- Vehicles used: 20
- 2-opt moves: 0
- Diagnosis: infeasible route; inspect listed constraint violations
- Violations: ['unserved customers: [5, 14, 19, 66, 86, 89]', 'missing customers: [5, 14, 19, 66, 86, 89]']

### A_due_time_priority on synthetic_evrptw_n100_seed20360707_small_battery (small_battery)

- Scale: 100
- Objective distance: 3257.846
- Feasible: False
- Vehicles used: 20
- 2-opt moves: 0
- Diagnosis: infeasible route; inspect listed constraint violations
- Violations: ['unserved customers: [5, 9, 20, 28, 53, 66, 67, 78, 79]', 'missing customers: [5, 9, 20, 28, 53, 66, 67, 78, 79]']

### A_due_time_priority on synthetic_evrptw_n100_seed20360716_small_battery (small_battery)

- Scale: 100
- Objective distance: 3246.882
- Feasible: False
- Vehicles used: 20
- 2-opt moves: 0
- Diagnosis: infeasible route; inspect listed constraint violations
- Violations: ['unserved customers: [7, 20, 23, 31, 89, 94, 99]', 'missing customers: [7, 20, 23, 31, 89, 94, 99]']
