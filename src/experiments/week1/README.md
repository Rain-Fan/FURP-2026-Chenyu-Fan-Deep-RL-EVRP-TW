# Week 1: Classical OR-Tools Routing Baselines

This folder keeps Week 1 experiments in the requested week-based layout.
The official OR-Tools algorithm source files are stored in
`../official_sources/or_tools/`:

- `tsp.py`
- `vrp.py`
- `vrp_capacity.py`
- `vrp_time_windows.py`

The Python files in this Week 1 folder are project wrappers used to extract
comparable JSON, route tables, and route visualisations from OR-Tools runs.
They should not be cited as official OR-Tools source code.

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
