# Week 3: Controlled Greedy-Policy Comparison

Week 3 compares two greedy customer-selection policies under the same EVRP-TW
instance generator, feasibility checker, and metrics.  The code keeps method
selection separate from the experiment runner so the comparison is easy to
inspect.

## Files

- `due_time_priority.py`: selects the feasible customer with the earliest due
  time.
- `nearest_customer.py`: selects the feasible customer with the shortest
  current travel distance.
- `compare_week3_baselines.py`: local runner that generates instances, runs
  both policies, validates routes, and writes result artifacts.

## Run

```bash
python3 compare_week3_baselines.py --scales 20 50 100 --instances-per-scale 12 --seed 20260630
```

## Outputs

- `results/run_log.txt`
- `results/week3_results.json`
- `results/week3_results.csv`
- `results/week3_comparison.csv`
- `results/week3_results.md`

## Failure-Case Review

After the standard run, inspect difficult cases for about 2 hours:

- tight time windows: identify which customer window causes infeasibility;
- too few vehicles or too little capacity: estimate the minimum fleet size or
  capacity needed to recover feasibility;
- uneven customer distribution: check whether the longer routes are spatially
  reasonable.

For each failed case, record the instance, violated constraint, route step
where the issue first appears, and a possible repair strategy.
