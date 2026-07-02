# Week 2 Research Progress: Baseline Recreation and Method Comparison

**Reporting date:** 21 June 2026

**Project:** Deep Reinforcement Learning for the Electric Vehicle Routing
Problem with Time Windows (EVRP-TW)

## 1. Week 2 lab requirements

The Week 2 lab requires baseline recreation and comparison across POMO, GA,
and OR-style methodologies.  Each method must be tested on different problem
scales, and the record must include instance scale, objective value,
feasibility under added electric-vehicle and time-window constraints, runtime,
and convergence details.

The implementation for this week is in
`src/experiments/week2/`.  Each compared algorithm is stored as a separate
Python file, with one deterministic EVRP-TW instance generator and one shared
feasibility checker for all methods.

## 2. Recreated methods

### POMO-style multi-start masked greedy

The original POMO implementation is CVRP-oriented.  For this week, I recreated
the relevant inference idea rather than the full neural training pipeline:
multiple parallel-style starts are decoded with feasibility-aware ordering,
then the best rollout is selected.  EVRP-TW constraints are added by route
splitting, time-window checks, capacity checks, and charging-station insertion.

### GA permutation + EV/TW repair

The GA baseline represents each solution as a customer permutation.  Crossover
and mutation generate new permutations, while a deterministic split-and-repair
procedure converts each chromosome into EVRP-TW routes.  Infeasible solutions
receive penalties, and the final output is validated by the shared checker.

### OR-Tools CVRPTW + charging repair

The OR baseline uses OR-Tools routing dimensions for customer sequencing with
capacity and time windows.  Since repeated charging-station visits are not
directly modelled in the simple CVRPTW formulation, charging stations are
inserted after OR-Tools produces the route sequence, then the full EVRP-TW
solution is checked.

## 3. Experimental setup

All experiments use deterministic synthetic instances with customer coordinates,
demands, time windows, charging stations, vehicle capacity, battery capacity,
and a fixed random seed.  The tested scales are 50, 100, and 200 customers.

Run command:

```bash
python src/experiments/week2/compare_week2_baselines.py --scales 50 100 200 --seed 20260621 --or-time-limit 8
```

Outputs:

- `src/experiments/week2/results/week2_results.json`
- `src/experiments/week2/results/week2_results.csv`
- `src/experiments/week2/results/week2_results.md`

## 4. Results

| Method | Customers | Objective distance | Feasible under E/TW | Runtime (s) | Vehicles | Convergence / notes |
|---|---:|---:|---|---:|---:|---|
| POMO-style multi-start masked greedy | 50 | 669.88 | Yes | 0.012 | 4 | 24 parallel-style starts; best feasible rollout selected |
| GA permutation + EV/TW repair | 50 | 1670.61 | Yes | 0.307 | 4 | population=48, generations_run=56, best_feasible=True |
| OR-Tools CVRPTW + charging repair | 50 | 536.84 | Yes | 8.010 | 4 | OR-Tools GLS time_limit=8s; charging stations inserted post hoc |
| POMO-style multi-start masked greedy | 100 | 1159.84 | Yes | 0.055 | 7 | 24 parallel-style starts; best feasible rollout selected |
| GA permutation + EV/TW repair | 100 | 4942.38 | Yes | 1.167 | 7 | population=48, generations_run=80, best_feasible=True |
| OR-Tools CVRPTW + charging repair | 100 | 1012.07 | Yes | 8.002 | 7 | OR-Tools GLS time_limit=8s; charging stations inserted post hoc |
| POMO-style multi-start masked greedy | 200 | 2090.49 | Yes | 0.270 | 14 | 24 parallel-style starts; best feasible rollout selected |
| GA permutation + EV/TW repair | 200 | 9602.82 | Yes | 2.670 | 14 | population=48, generations_run=68, best_feasible=True |
| OR-Tools CVRPTW + charging repair | 200 | 1661.91 | Yes | 8.006 | 14 | OR-Tools GLS time_limit=8s; charging stations inserted post hoc |

## 5. Method comparison

OR-Tools produced the best objective values on all three scales, but it used a
fixed 8-second search budget per instance.  This makes it a strong reference
baseline for route quality, especially when the model can express the main
capacity and time-window structure.

The POMO-style multi-start baseline was much faster.  It produced feasible
solutions in less than one second even at 200 customers, but the objective was
higher than OR-Tools because the constructive rollout does not perform local
search after route construction.  This result supports the idea that a learned
attention decoder could be useful as a fast initial-solution generator.

The GA baseline found feasible solutions at all scales, but its objective
values were much worse than both OR-Tools and POMO-style construction.  The
main reason is that the permutation search is broad, while the repair operator
is simple and does not include strong local search moves such as relocate,
2-opt, station relocation, or route exchange.

## 6. Challenges when adding E and TW constraints

The main difficulty is that feasibility is no longer determined by customer
order alone.  A route can be spatially short but infeasible because arrival
time exceeds a customer's due time, battery is insufficient before the next
customer or depot, or a charging stop changes the downstream schedule.

Charging stations also make the action space different from standard CVRP and
VRPTW.  Customers should be served once, but stations may be revisited.  This
is easy to handle in a custom constructive decoder, but harder to express in a
compact OR-Tools CVRPTW model without expanding the graph or adding station
copies.

For GA, the largest challenge is repair quality.  A customer permutation can be
converted into a route set, but a weak repair operator may hide the value of
genetic search.  Better local improvement is needed before GA can be treated
as a competitive baseline.

## 7. Insights for the target EVRP-TW model

The target deep RL model should separate three concerns clearly:

- customer selection policy;
- hard feasibility masking for capacity, time, and battery;
- charging insertion or charging decision logic.

The Week 2 results suggest that a fast learned decoder should not be evaluated
only by raw objective.  It should also be tested as an initial-solution
generator for OR/local-search repair.  A practical research direction is
therefore a hybrid approach: attention/RL constructs a feasible or nearly
feasible route plan, then OR-Tools, ALNS, or local search improves route
quality and charging placement.
