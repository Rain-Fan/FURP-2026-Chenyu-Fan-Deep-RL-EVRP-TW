# Week 2: EVRP-TW Baseline Recreation and Comparison

This folder keeps Week 2 experiments in the requested week-based layout.
Official upstream algorithm source files are not stored in this folder.  They
are stored under `../official_sources/`, including:

- Google OR-Tools routing samples in `../official_sources/or_tools/`;
- POMO CVRP source files from `yd-kwon/POMO` in
  `../official_sources/pomo_cvrp/`.

The files below are project-written experiment wrappers or simplified
recreations used for controlled local comparison.  They should not be cited as
official algorithm source code:

- `pomo_style.py`
- `genetic_algorithm.py`
- `or_tools_cvrptw.py`
- `evrp_tw_common.py`
- `compare_week2_baselines.py`

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
