# Week 2 EVRP-TW Baseline Results

| Method | Customers | Objective distance | Feasible under E/TW | Runtime (s) | Vehicles | Convergence / notes |
|---|---:|---:|---|---:|---:|---|
| POMO-style multi-start masked greedy | 50 | 669.88 | Yes | 0.013 | 4 | 24 parallel-style starts; best feasible rollout selected |
| GA permutation + EV/TW repair | 50 | 1670.61 | Yes | 0.306 | 4 | population=48, generations_run=56, best_feasible=True |
| OR-Tools CVRPTW + charging repair | 50 | 536.84 | Yes | 8.003 | 4 | OR-Tools GLS time_limit=8s; charging stations inserted post hoc |
| POMO-style multi-start masked greedy | 100 | 1159.84 | Yes | 0.062 | 7 | 24 parallel-style starts; best feasible rollout selected |
| GA permutation + EV/TW repair | 100 | 4942.38 | Yes | 1.269 | 7 | population=48, generations_run=80, best_feasible=True |
| OR-Tools CVRPTW + charging repair | 100 | 1012.07 | Yes | 8.004 | 7 | OR-Tools GLS time_limit=8s; charging stations inserted post hoc |
| POMO-style multi-start masked greedy | 200 | 2090.49 | Yes | 0.290 | 14 | 24 parallel-style starts; best feasible rollout selected |
| GA permutation + EV/TW repair | 200 | 9602.82 | Yes | 2.839 | 14 | population=48, generations_run=68, best_feasible=True |
| OR-Tools CVRPTW + charging repair | 200 | 1665.01 | Yes | 8.005 | 14 | OR-Tools GLS time_limit=8s; charging stations inserted post hoc |

All objective values are total Euclidean route distance and are only
directly comparable when `Feasible under E/TW` is `Yes`. E/TW
feasibility is checked after each method has inserted or repaired
capacity, time-window, depot-return, and battery/charging constraints.
