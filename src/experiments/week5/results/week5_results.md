# Week 5 Consolidation Results: Inter-Route Local Search

Run started: `2026-07-17 17:57:38 CST`

Research question: does adding inter-route local search (or-opt relocation + swap) on top of the Week 4 composite-score + 2-opt method (Method C) close the medium-scale distance gap against the nearest-customer baseline (Method B), without losing feasibility?

D = composite + 2-opt + inter-route LS (tested). C = composite + 2-opt (Week 4). B = nearest-customer baseline.

## Summary Table (by profile x scale x method)

| Profile | Method | Customers | Instances | Feasible | Feas. rate | Mean feas. objective | Mean runtime (s) | Mean vehicles | Mean 2-opt | Mean inter-route | Mean LS gain |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | D_composite_inter_route | 20 | 12 | 12 | 1.000 | 407.318 | 0.005611 | 2.583 | 3.667 | 5.917 | 71.479 |
| baseline | C_composite_score | 20 | 12 | 12 | 1.000 | 453.744 | 0.000913 | 2.833 | 3.667 | 0.000 | 25.054 |
| baseline | B_nearest_customer | 20 | 12 | 12 | 1.000 | 467.816 | 0.000202 | 2.917 | 0.000 | 0.000 | 0.000 |
| baseline | D_composite_inter_route | 50 | 12 | 12 | 1.000 | 663.665 | 0.104582 | 4.333 | 10.417 | 22.417 | 133.725 |
| baseline | C_composite_score | 50 | 12 | 12 | 1.000 | 748.251 | 0.007302 | 4.333 | 10.417 | 0.000 | 49.139 |
| baseline | B_nearest_customer | 50 | 12 | 12 | 1.000 | 736.512 | 0.001256 | 4.333 | 0.000 | 0.000 | 0.000 |
| baseline | D_composite_inter_route | 100 | 12 | 12 | 1.000 | 987.154 | 0.831418 | 6.667 | 25.917 | 60.000 | 249.274 |
| baseline | C_composite_score | 100 | 12 | 12 | 1.000 | 1150.150 | 0.029434 | 6.833 | 25.917 | 0.000 | 86.278 |
| baseline | B_nearest_customer | 100 | 12 | 12 | 1.000 | 1119.591 | 0.006014 | 6.583 | 0.000 | 0.000 | 0.000 |
| tight_tw | D_composite_inter_route | 20 | 12 | 12 | 1.000 | 396.791 | 0.005873 | 2.667 | 5.000 | 8.250 | 93.043 |
| tight_tw | C_composite_score | 20 | 12 | 12 | 1.000 | 455.486 | 0.000972 | 3.000 | 5.000 | 0.000 | 34.348 |
| tight_tw | B_nearest_customer | 20 | 12 | 12 | 1.000 | 467.816 | 0.000211 | 2.917 | 0.000 | 0.000 | 0.000 |
| tight_tw | D_composite_inter_route | 50 | 12 | 12 | 1.000 | 658.793 | 0.108563 | 4.083 | 12.333 | 24.500 | 146.753 |
| tight_tw | C_composite_score | 50 | 12 | 12 | 1.000 | 754.359 | 0.006840 | 4.333 | 12.333 | 0.000 | 51.187 |
| tight_tw | B_nearest_customer | 50 | 12 | 12 | 1.000 | 736.541 | 0.001201 | 4.333 | 0.000 | 0.000 | 0.000 |
| tight_tw | D_composite_inter_route | 100 | 12 | 12 | 1.000 | 990.983 | 0.987321 | 6.750 | 27.250 | 74.667 | 275.000 |
| tight_tw | C_composite_score | 100 | 12 | 12 | 1.000 | 1176.093 | 0.026742 | 6.833 | 27.250 | 0.000 | 89.891 |
| tight_tw | B_nearest_customer | 100 | 12 | 12 | 1.000 | 1112.104 | 0.006104 | 6.583 | 0.000 | 0.000 | 0.000 |
| small_battery | D_composite_inter_route | 20 | 12 | 10 | 0.833 | 422.092 | 0.004988 | 3.417 | 2.167 | 5.417 | 46.574 |
| small_battery | C_composite_score | 20 | 12 | 10 | 0.833 | 452.070 | 0.000618 | 3.583 | 2.167 | 0.000 | 7.786 |
| small_battery | B_nearest_customer | 20 | 12 | 12 | 1.000 | 468.653 | 0.000206 | 3.583 | 0.000 | 0.000 | 0.000 |
| small_battery | D_composite_inter_route | 50 | 12 | 12 | 1.000 | 720.942 | 0.090635 | 5.583 | 7.917 | 27.583 | 130.306 |
| small_battery | C_composite_score | 50 | 12 | 12 | 1.000 | 822.243 | 0.004415 | 6.000 | 7.917 | 0.000 | 29.005 |
| small_battery | B_nearest_customer | 50 | 12 | 12 | 1.000 | 794.947 | 0.001188 | 5.583 | 0.000 | 0.000 | 0.000 |
| small_battery | D_composite_inter_route | 100 | 12 | 12 | 1.000 | 1050.839 | 0.821121 | 8.167 | 21.000 | 71.833 | 251.413 |
| small_battery | C_composite_score | 100 | 12 | 12 | 1.000 | 1242.767 | 0.021150 | 8.500 | 21.000 | 0.000 | 59.486 |
| small_battery | B_nearest_customer | 100 | 12 | 12 | 1.000 | 1173.518 | 0.005649 | 8.167 | 0.000 | 0.000 | 0.000 |

## Method D vs References

Negative objective delta / percent = D finds shorter feasible routes.

| Profile | Customers | Reference | Feasibility delta | Feasible-objective delta | Objective delta (%) | Runtime delta (s) |
|---|---:|---|---:|---:|---:|---:|
| baseline | 20 | C_composite_score | 0.000 | -46.426 | -10.23 | 0.004698 |
| baseline | 20 | B_nearest_customer | 0.000 | -60.499 | -12.93 | 0.005410 |
| baseline | 50 | C_composite_score | 0.000 | -84.586 | -11.30 | 0.097281 |
| baseline | 50 | B_nearest_customer | 0.000 | -72.847 | -9.89 | 0.103327 |
| baseline | 100 | C_composite_score | 0.000 | -162.996 | -14.17 | 0.801984 |
| baseline | 100 | B_nearest_customer | 0.000 | -132.437 | -11.83 | 0.825404 |
| small_battery | 20 | C_composite_score | 0.000 | -29.978 | -6.63 | 0.004370 |
| small_battery | 20 | B_nearest_customer | -0.167 | -46.561 | -9.94 | 0.004782 |
| small_battery | 50 | C_composite_score | 0.000 | -101.302 | -12.32 | 0.086221 |
| small_battery | 50 | B_nearest_customer | 0.000 | -74.005 | -9.31 | 0.089447 |
| small_battery | 100 | C_composite_score | 0.000 | -191.927 | -15.44 | 0.799971 |
| small_battery | 100 | B_nearest_customer | 0.000 | -122.679 | -10.45 | 0.815472 |
| tight_tw | 20 | C_composite_score | 0.000 | -58.694 | -12.89 | 0.004902 |
| tight_tw | 20 | B_nearest_customer | 0.000 | -71.025 | -15.18 | 0.005663 |
| tight_tw | 50 | C_composite_score | 0.000 | -95.566 | -12.67 | 0.101723 |
| tight_tw | 50 | B_nearest_customer | 0.000 | -77.748 | -10.56 | 0.107362 |
| tight_tw | 100 | C_composite_score | 0.000 | -185.109 | -15.74 | 0.960578 |
| tight_tw | 100 | B_nearest_customer | 0.000 | -121.120 | -10.89 | 0.981217 |

## Largest Method D improvements over Method C

These are the instances where inter-route moves removed the most distance relative to the Week 4 method.

| Profile | Customers | Seed | C distance | D distance | Reduction | Inter-route moves |
|---|---:|---:|---:|---:|---:|---:|
| small_battery | 100 | 20360717 | 1310.394 | 1016.015 | 294.379 | 92 |
| small_battery | 100 | 20360719 | 1357.354 | 1070.980 | 286.374 | 93 |
| baseline | 100 | 20360723 | 1307.098 | 1039.835 | 267.263 | 87 |
| tight_tw | 100 | 20360719 | 1311.257 | 1047.646 | 263.611 | 115 |
