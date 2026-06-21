# Week 2

## Baseline recreation and comparison

This week focused on the project-hub Week 2 requirement: recreate baseline
methods and compare results across different EVRP-TW problem scales.

Completed work:

- implemented POMO-style multi-start masked greedy construction;
- implemented a GA baseline over customer permutations with EV/TW repair;
- implemented an OR-Tools CVRPTW baseline with charging-station insertion;
- added a shared feasibility checker for capacity, time windows, depot return,
  battery consumption, and charging stations;
- ran 50, 100, and 200 customer experiments;
- recorded objective values, feasibility status, runtime, vehicle count, and
  convergence notes;
- wrote the comparison/reflection report in
  `docs/week2_baseline_comparison.md`.

Main result:

OR-Tools achieved the best route distance under the fixed search budget, the
POMO-style constructive baseline was much faster and still feasible, and GA
required repair to stay feasible but produced weaker objective values.  This
supports using learned decoders as fast initial-solution generators followed
by OR/local-search improvement.
