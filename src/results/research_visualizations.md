# Research Visualization Index

Generated from the existing Week 2 and Week 3 experiment result files.

## Figures

- [week2_baseline_comparison.svg](week2_baseline_comparison.svg)
- [week3_performance_summary.svg](week3_performance_summary.svg)
- [week3_diagnostic_summary.svg](week3_diagnostic_summary.svg)
- [week3_representative_routes.svg](week3_representative_routes.svg)

## Week 3 headline deltas

| Customers | Feasibility delta A-B | Feasible objective delta A-B | Coverage violation delta A-B |
|---:|---:|---:|---:|
| 20 | -0.750 | 327.701 | 9 |
| 50 | -0.500 | 1061.437 | 6 |
| 100 | -0.083 | 2642.877 | 1 |

A is `A_due_time_priority`; B is `B_nearest_customer`. Negative feasibility
delta means A solved fewer instances. Positive objective delta means A used
longer feasible routes.
