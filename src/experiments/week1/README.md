# Week 1: Classical OR-Tools Routing Baselines

This folder keeps Week 1 experiments in the requested week-based layout.
Each algorithm studied in Week 1 has its own Python file:

- `tsp.py`
- `vrp.py`
- `cvrp.py`
- `vrptw.py`

`compare_or_tools_baselines.py` runs all four algorithms and writes the
comparison artifacts to `results/`.

## Run

```bash
python -m pip install -r requirements.txt
python compare_or_tools_baselines.py
```

Outputs:

- `results/baseline_results.json`
- `results/route_tables.md`
- `results/baseline_routes.png`
