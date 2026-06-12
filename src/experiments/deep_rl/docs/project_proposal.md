# Project Proposal

## Objective

Develop and evaluate attention-based deep reinforcement-learning policies for
constructing feasible routes in the Electric Vehicle Routing Problem with Time
Windows.

## Research Questions

1. Can REINFORCE or PPO learn to construct feasible EVRP-TW routes?
2. How does the learned policy compare with a feasibility-first greedy solver?
3. Which constraints most often cause failure: capacity, time, energy, or fleet
   size?
4. How do charging stations and battery capacity affect distance and
   feasibility?

## Initial Scope

- homogeneous electric vehicles;
- one depot;
- fixed customer demand and service duration;
- deterministic travel time and linear energy consumption;
- full charging at station visits;
- synthetic Euclidean instances.

## Deliverables

- shared EVRP-TW environment and feasibility checker;
- greedy baseline;
- REINFORCE and PPO implementations;
- reproducible configurations and checkpoints;
- feasibility, cost, and runtime evaluation;
- route and training visualisations.

## Extension Path

Future work should add Schneider/Solomon benchmark loaders, OR-Tools or PyVRP
comparisons, partial charging, nonlinear energy models, local-search repair,
and POMO-style multi-start decoding.
