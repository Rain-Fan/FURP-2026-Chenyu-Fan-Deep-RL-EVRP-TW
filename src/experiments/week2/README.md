# Week 2: EVRP-TW Baseline Recreation and Comparison

This folder keeps Week 2 experiments in the requested week-based layout.
Each algorithm studied or compared in Week 2 has its own Python file:

- `pomo_style.py`
- `genetic_algorithm.py`
- `or_tools_cvrptw.py`

`compare_week2_baselines.py` runs all three algorithms on the same generated
EVRP-TW instances and writes the comparison artifacts to `results/`.

## Run

```bash
python compare_week2_baselines.py --scales 50 100 200 --seed 20260621
```

Outputs:

- `results/week2_results.json`
- `results/week2_results.csv`
- `results/week2_results.md`

All methods use the same synthetic EVRP-TW instance generator and the same
post-run feasibility checker in `evrp_tw_common.py`.
