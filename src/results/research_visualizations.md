# Research Visualization Index

Generated from the existing Week 2, Week 3, Week 4, and Week 5 experiment result files.

## Figures

- [week2_baseline_comparison.svg](week2_baseline_comparison.svg)
- [week3_performance_summary.svg](week3_performance_summary.svg)
- [week3_diagnostic_summary.svg](week3_diagnostic_summary.svg)
- [week3_representative_routes.svg](week3_representative_routes.svg)
- [week4_performance_summary.svg](week4_performance_summary.svg)
- [week4_profile_sensitivity.svg](week4_profile_sensitivity.svg)
- [week4_representative_routes.svg](week4_representative_routes.svg)
- [week5_performance_summary.svg](week5_performance_summary.svg)
- [week5_representative_routes.svg](week5_representative_routes.svg)

## Week 3 headline deltas

| Customers | Feasibility delta A-B | Feasible objective delta A-B | Coverage violation delta A-B |
|---:|---:|---:|---:|
| 20 | -0.750 | 327.701 | 9 |
| 50 | -0.500 | 1061.437 | 6 |
| 100 | -0.083 | 2642.877 | 1 |

A is `A_due_time_priority`; B is `B_nearest_customer`. Negative feasibility
delta means A solved fewer instances. Positive objective delta means A used
longer feasible routes.

## Week 4 headline deltas (Method C vs references, baseline profile)

| Customers | Reference | Feasibility delta C-ref | Feasible objective delta C-ref |
|---:|---|---:|---:|
| 20 | A: due-time | 0.750 | -316.520 |
| 20 | B: nearest | 0.000 | -12.460 |
| 50 | A: due-time | 0.417 | -1169.912 |
| 50 | B: nearest | 0.000 | 34.457 |
| 100 | A: due-time | 0.000 | -2718.032 |
| 100 | B: nearest | 0.000 | -17.100 |

C is `C_composite_score` (composite-score greedy + feasibility-aware 2-opt).
Positive feasibility delta means C solved more instances than the reference.
Negative objective delta means C found shorter feasible routes.

## Week 5 headline deltas (Method D vs references, baseline profile)

| Customers | Reference | Feasibility delta D-ref | Objective delta D-ref (%) |
|---:|---|---:|---:|
| 20 | C: composite+2opt | 0.000 | -10.23 |
| 20 | B: nearest | 0.000 | -12.93 |
| 50 | C: composite+2opt | 0.000 | -11.30 |
| 50 | B: nearest | 0.000 | -9.89 |
| 100 | C: composite+2opt | 0.000 | -14.17 |
| 100 | B: nearest | 0.000 | -11.83 |

D is `D_composite_inter_route` (Method C plus inter-route or-opt + swap).
Negative objective percent means D found shorter feasible routes; at n=50 and
n=100 D is now below the baseline, closing the Week 4 medium-scale gap.
