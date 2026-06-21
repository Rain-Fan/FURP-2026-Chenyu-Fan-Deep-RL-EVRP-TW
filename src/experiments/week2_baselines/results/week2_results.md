# Week 2 EVRP-TW Baseline Results

| Method | Customers | Objective distance | Feasible under E/TW | Runtime (s) | Vehicles | Convergence / notes |
|---|---:|---:|---|---:|---:|---|
| POMO-style multi-start masked greedy | 50 | 669.88 | Yes | 0.012 | 4 | 24 parallel-style starts; best feasible rollout selected |
| GA permutation + EV/TW repair | 50 | 1670.61 | Yes | 0.336 | 4 | population=48, generations_run=56, best_feasible=True |
| OR-Tools CVRPTW + charging repair | 50 | 536.84 | Yes | 8.006 | 4 | OR-Tools GLS time_limit=8s; charging stations inserted post hoc |
| POMO-style multi-start masked greedy | 100 | 1159.84 | Yes | 0.058 | 7 | 24 parallel-style starts; best feasible rollout selected |
| GA permutation + EV/TW repair | 100 | 4942.38 | Yes | 1.236 | 7 | population=48, generations_run=80, best_feasible=True |
| OR-Tools CVRPTW + charging repair | 100 | 1012.07 | Yes | 8.002 | 7 | OR-Tools GLS time_limit=8s; charging stations inserted post hoc |
| POMO-style multi-start masked greedy | 200 | 2090.49 | Yes | 0.272 | 14 | 24 parallel-style starts; best feasible rollout selected |
| GA permutation + EV/TW repair | 200 | 9602.82 | Yes | 2.705 | 14 | population=48, generations_run=68, best_feasible=True |
| OR-Tools CVRPTW + charging repair | 200 | 1660.49 | Yes | 8.006 | 14 | OR-Tools GLS time_limit=8s; charging stations inserted post hoc |

All objective values are total Euclidean route distance and are only
directly comparable when `Feasible under E/TW` is `Yes`.  E/TW
feasibility is checked after each method has inserted or repaired
capacity, time-window, depot-return, and battery/charging constraints.
