# Week 3 Baseline Results

Run started: `2026-06-30 15:06:53 CST`

Method: deterministic feasibility-first greedy construction baseline.

| Customers | Instances | Feasible | Feasibility rate | Mean objective | Mean feasible objective | Mean runtime (s) | Mean vehicles | Mean charges | TW viol. | Capacity viol. | Energy viol. | Coverage viol. |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 32 | 21 | 0.656 | 450.552 | 441.557 | 0.000064 | 3.000 | 1.406 | 0 | 0 | 0 | 11 |
| 25 | 32 | 1 | 0.031 | 833.218 | 780.085 | 0.000296 | 5.000 | 3.469 | 0 | 0 | 0 | 31 |
| 50 | 32 | 1 | 0.031 | 1536.332 | 1545.652 | 0.001183 | 9.000 | 7.219 | 0 | 0 | 0 | 31 |

## Diagnostic cases

### synthetic_evrptw_n50_seed20310635

- Scale: 50
- Seed: 20310635
- Objective distance: 1611.423
- Feasible: False
- Vehicles used: 9
- Charge count: 9
- Diagnosis: infeasible route; inspect listed constraint violations
- Violations: ['unserved customers: [3, 6, 10, 13, 26, 28, 33, 36, 42]', 'missing customers: [3, 6, 10, 13, 26, 28, 33, 36, 42]']
- First route: `[0, 19, 27, 21, 52, 0]`

### synthetic_evrptw_n50_seed20310657

- Scale: 50
- Seed: 20310657
- Objective distance: 1607.657
- Feasible: False
- Vehicles used: 9
- Charge count: 8
- Diagnosis: infeasible route; inspect listed constraint violations
- Violations: ['unserved customers: [2, 3, 5, 13, 22, 23, 30, 39]', 'missing customers: [2, 3, 5, 13, 22, 23, 30, 39]']
- First route: `[0, 4, 34, 28, 1, 43, 54, 0]`

### synthetic_evrptw_n50_seed20310644

- Scale: 50
- Seed: 20310644
- Objective distance: 1585.864
- Feasible: False
- Vehicles used: 9
- Charge count: 9
- Diagnosis: infeasible route; inspect listed constraint violations
- Violations: ['unserved customers: [1, 8, 9, 11, 22, 33, 40, 48]', 'missing customers: [1, 8, 9, 11, 22, 33, 40, 48]']
- First route: `[0, 15, 23, 36, 29, 25, 4, 55, 0]`

