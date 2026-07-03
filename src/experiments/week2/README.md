# Week 2: EVRP-TW Baseline Comparison

Week 2 compares three local EVRP-TW baselines on the same deterministic
synthetic instances.  The code is organized in a documentation-style layout:
shared data/model helpers, one file per method, and one comparison runner.

## Files

- `evrp_tw_common.py`: instance generation, repair helpers, and feasibility
  checks.
- `pomo_style.py`: POMO-inspired multi-start constructive baseline.
- `genetic_algorithm.py`: permutation GA with EV/time-window repair.
- `or_tools_cvrptw.py`: OR-Tools CVRPTW sequencing with charging repair.
- `compare_week2_baselines.py`: local runner that writes result artifacts.

## Run

```bash
python compare_week2_baselines.py --scales 50 100 200 --seed 20260621 --or-time-limit 8
```

## Outputs

- `results/week2_results.json`
- `results/week2_results.csv`
- `results/week2_results.md`
