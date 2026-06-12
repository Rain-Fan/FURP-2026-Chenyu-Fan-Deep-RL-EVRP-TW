# Experiment Plan

## Methods

- feasibility-first greedy baseline;
- attention policy trained with REINFORCE;
- attention policy and value head trained with PPO.

## Instance Sizes

Start with 5, 10, and 20 customers. Use the same station count, fleet
parameters, and test seeds for every compared method.

## Metrics

- feasibility rate;
- mean cost over all instances;
- mean cost over feasible instances;
- total distance;
- vehicles used;
- runtime and hardware.

## Protocol

1. Fix separate training, validation, and test seeds.
2. Train at least three independent model seeds.
3. Select checkpoints using validation feasibility first, then feasible cost.
4. Report mean and standard deviation over model seeds.
5. Compare objective values only for feasible solutions.
6. Save the exact YAML configuration and Git commit with each result.

## Ablations

- remove the energy-reserve mask;
- vary battery capacity and charging-station count;
- compare REINFORCE and PPO;
- vary embedding size and decoder depth;
- compare sampling and greedy decoding.

## Failure Analysis

For each infeasible route, record the first dead-end step, current node,
remaining capacity, battery, time, vehicles used, and number of unserved
customers.
