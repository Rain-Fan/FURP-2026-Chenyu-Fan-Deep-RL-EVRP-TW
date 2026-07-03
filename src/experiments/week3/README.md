# Week 3: Project EVRP-TW Controlled Experiment

No confirmed official source repository was found for the exact Week 3
EVRP-TW greedy comparison used in this project.  Therefore the project-written
files are retained under `project_adapters/` and are explicitly marked as
adapters, not official algorithm source code.

## Project Adapter Files

| Local file | Role |
|---|---|
| `project_adapters/compare_week3_baselines.py` | Controlled A-vs-B experiment runner. |
| `project_adapters/due_time_priority.py` | Project-written due-time-priority selector. |
| `project_adapters/nearest_customer.py` | Project-written nearest-customer selector. |

These files follow a clear experiment-runner format: method definition,
shared instance generation, shared feasibility checks, shared metrics, and
single-command output generation.  They should not be described as official
paper code.

## Run Project Adapter Experiment

```bash
python3 src/experiments/week3/project_adapters/compare_week3_baselines.py \
  --scales 20 50 100 \
  --instances-per-scale 12 \
  --seed 20260630
```

Outputs are written to `results/`:

- `run_log.txt`: local command, environment, and summary;
- `week3_results.json`: full metadata, per-instance routes, diagnostics, and
  aggregate results;
- `week3_results.csv`: aggregate method-by-scale table;
- `week3_comparison.csv`: A-vs-B comparison table;
- `week3_results.md`: cleaned summary table and diagnostic cases.

## Focused Failure-Case Procedure

After the standard A-vs-B run, inspect deliberately difficult cases for about
2 hours:

- tight time windows: identify which customer window causes infeasibility;
- too few vehicles or too little capacity: estimate the minimum fleet size or
  capacity needed to recover feasibility;
- uneven customer distribution: check whether the longer routes are spatially
  reasonable.

For each failed case, record the instance, violated constraint, route step
where the issue first appears, and a possible repair strategy.
