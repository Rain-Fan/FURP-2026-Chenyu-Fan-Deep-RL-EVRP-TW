# Week 7 Results: Double-DQN Operator Selection

Run started: `2026-08-13 18:22:10 CST`

Can a seed-separated Double DQN improve the Week 6 UCB1 operator selector on held-out EVRP-TW instances?

Training and evaluation seed overlap: **0**.

## Held-out aggregate results

| Profile | n | Method | Feasible | Mean objective | Runtime (s) |
|---|---:|---|---:|---:|---:|
| baseline | 20 | D_composite_inter_route | 6/6 | 411.080 | 0.004891 |
| baseline | 20 | E_fixed_portfolio | 6/6 | 387.740 | 0.010149 |
| baseline | 20 | E_adaptive_portfolio | 6/6 | 385.435 | 0.014235 |
| baseline | 20 | F_dqn_portfolio | 6/6 | 383.334 | 0.014093 |
| baseline | 50 | D_composite_inter_route | 6/6 | 663.486 | 0.105446 |
| baseline | 50 | E_fixed_portfolio | 6/6 | 639.872 | 0.201493 |
| baseline | 50 | E_adaptive_portfolio | 6/6 | 635.018 | 0.190328 |
| baseline | 50 | F_dqn_portfolio | 6/6 | 639.444 | 0.203980 |
| baseline | 100 | D_composite_inter_route | 6/6 | 1012.983 | 0.988933 |
| baseline | 100 | E_fixed_portfolio | 6/6 | 956.543 | 1.860601 |
| baseline | 100 | E_adaptive_portfolio | 6/6 | 946.415 | 1.308586 |
| baseline | 100 | F_dqn_portfolio | 6/6 | 980.947 | 1.165734 |
| tight_tw | 20 | D_composite_inter_route | 6/6 | 429.989 | 0.006587 |
| tight_tw | 20 | E_fixed_portfolio | 6/6 | 402.439 | 0.012356 |
| tight_tw | 20 | E_adaptive_portfolio | 6/6 | 400.009 | 0.015538 |
| tight_tw | 20 | F_dqn_portfolio | 6/6 | 399.180 | 0.015822 |
| tight_tw | 50 | D_composite_inter_route | 6/6 | 722.108 | 0.128690 |
| tight_tw | 50 | E_fixed_portfolio | 6/6 | 667.674 | 0.229799 |
| tight_tw | 50 | E_adaptive_portfolio | 6/6 | 669.651 | 0.193003 |
| tight_tw | 50 | F_dqn_portfolio | 6/6 | 662.886 | 0.225458 |
| tight_tw | 100 | D_composite_inter_route | 6/6 | 1017.905 | 1.108190 |
| tight_tw | 100 | E_fixed_portfolio | 6/6 | 967.338 | 1.805809 |
| tight_tw | 100 | E_adaptive_portfolio | 6/6 | 967.205 | 1.205706 |
| tight_tw | 100 | F_dqn_portfolio | 6/6 | 965.685 | 1.297644 |
| small_battery | 20 | D_composite_inter_route | 5/6 | 442.673 | 0.005023 |
| small_battery | 20 | E_fixed_portfolio | 5/6 | 435.503 | 0.009806 |
| small_battery | 20 | E_adaptive_portfolio | 5/6 | 435.503 | 0.011239 |
| small_battery | 20 | F_dqn_portfolio | 5/6 | 435.503 | 0.013902 |
| small_battery | 50 | D_composite_inter_route | 6/6 | 732.680 | 0.100516 |
| small_battery | 50 | E_fixed_portfolio | 6/6 | 708.009 | 0.199720 |
| small_battery | 50 | E_adaptive_portfolio | 6/6 | 705.530 | 0.166401 |
| small_battery | 50 | F_dqn_portfolio | 6/6 | 708.534 | 0.199263 |
| small_battery | 100 | D_composite_inter_route | 6/6 | 1052.850 | 1.011409 |
| small_battery | 100 | E_fixed_portfolio | 6/6 | 1017.379 | 2.097707 |
| small_battery | 100 | E_adaptive_portfolio | 6/6 | 1028.200 | 1.266325 |
| small_battery | 100 | F_dqn_portfolio | 6/6 | 1018.437 | 1.316716 |

## F-DQN comparisons

Negative objective percentage means DQN is shorter.

| Profile | n | Reference | Feasibility delta | Objective delta (%) | Runtime delta (s) | W/T/L |
|---|---:|---|---:|---:|---:|---:|
| baseline | 20 | D_composite_inter_route | +0.000 | -6.75 | +0.009202 | 4/2/0 |
| baseline | 20 | E_fixed_portfolio | +0.000 | -1.14 | +0.003943 | 2/4/0 |
| baseline | 20 | E_adaptive_portfolio | +0.000 | -0.55 | -0.000142 | 2/3/1 |
| baseline | 50 | D_composite_inter_route | +0.000 | -3.62 | +0.098533 | 5/0/1 |
| baseline | 50 | E_fixed_portfolio | +0.000 | -0.07 | +0.002487 | 4/0/2 |
| baseline | 50 | E_adaptive_portfolio | +0.000 | 0.70 | +0.013652 | 1/3/2 |
| baseline | 100 | D_composite_inter_route | +0.000 | -3.16 | +0.176802 | 5/0/1 |
| baseline | 100 | E_fixed_portfolio | +0.000 | 2.55 | -0.694866 | 3/0/3 |
| baseline | 100 | E_adaptive_portfolio | +0.000 | 3.65 | -0.142851 | 0/0/6 |
| tight_tw | 20 | D_composite_inter_route | +0.000 | -7.16 | +0.009234 | 5/1/0 |
| tight_tw | 20 | E_fixed_portfolio | +0.000 | -0.81 | +0.003466 | 2/4/0 |
| tight_tw | 20 | E_adaptive_portfolio | +0.000 | -0.21 | +0.000283 | 2/3/1 |
| tight_tw | 50 | D_composite_inter_route | +0.000 | -8.20 | +0.096768 | 5/0/1 |
| tight_tw | 50 | E_fixed_portfolio | +0.000 | -0.72 | -0.004341 | 4/1/1 |
| tight_tw | 50 | E_adaptive_portfolio | +0.000 | -1.01 | +0.032454 | 2/4/0 |
| tight_tw | 100 | D_composite_inter_route | +0.000 | -5.13 | +0.189454 | 5/0/1 |
| tight_tw | 100 | E_fixed_portfolio | +0.000 | -0.17 | -0.508165 | 4/0/2 |
| tight_tw | 100 | E_adaptive_portfolio | +0.000 | -0.16 | +0.091938 | 3/0/3 |
| small_battery | 20 | D_composite_inter_route | +0.000 | -1.62 | +0.008878 | 1/4/0 |
| small_battery | 20 | E_fixed_portfolio | +0.000 | 0.00 | +0.004096 | 0/5/0 |
| small_battery | 20 | E_adaptive_portfolio | +0.000 | 0.00 | +0.002662 | 0/5/0 |
| small_battery | 50 | D_composite_inter_route | +0.000 | -3.30 | +0.098747 | 5/1/0 |
| small_battery | 50 | E_fixed_portfolio | +0.000 | 0.07 | -0.000457 | 3/2/1 |
| small_battery | 50 | E_adaptive_portfolio | +0.000 | 0.43 | +0.032862 | 1/4/1 |
| small_battery | 100 | D_composite_inter_route | +0.000 | -3.27 | +0.305307 | 4/0/2 |
| small_battery | 100 | E_fixed_portfolio | +0.000 | 0.10 | -0.780991 | 3/0/3 |
| small_battery | 100 | E_adaptive_portfolio | +0.000 | -0.95 | +0.050391 | 4/1/1 |

## Failure and limitation cases

- `infeasible_or_validation` profile=small_battery, n=20, seed=20300014: gap_vs_UCB1=None, runtime=0.005386s, violations=['unserved customers: [8, 18]']
- `infeasible_or_validation` profile=small_battery, n=20, seed=20300014: gap_vs_UCB1=None, runtime=0.000636s, violations=['unserved customers: [8, 18]']
- `infeasible_or_validation` profile=small_battery, n=20, seed=20300014: gap_vs_UCB1=None, runtime=0.000623s, violations=['unserved customers: [8, 18]']
- `infeasible_or_validation` profile=small_battery, n=20, seed=20300014: gap_vs_UCB1=None, runtime=0.000610s, violations=['infeasible construction or warm start']
- `dqn_vs_ucb1` profile=baseline, n=100, seed=20380016: gap_vs_UCB1=85.36226421502045, runtime=1.154441s, violations=[]
- `dqn_vs_ucb1` profile=baseline, n=100, seed=20380015: gap_vs_UCB1=44.991913566798985, runtime=1.118106s, violations=[]

## Interpretation rule

This prototype is judged against fixed and UCB1 references on held-out seeds. It is not claimed to be state of the art, and losses are retained in the tables.
