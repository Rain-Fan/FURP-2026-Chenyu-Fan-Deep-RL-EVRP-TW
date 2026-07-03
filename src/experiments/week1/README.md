# Week 1: Official OR-Tools Routing Samples

This folder is aligned with the Google OR-Tools routing examples.  The root
Python files are copied official source files from:

https://github.com/google/or-tools/tree/stable/ortools/constraint_solver/samples

## Official Files

| Local file | Official OR-Tools sample | Purpose |
|---|---|---|
| `tsp.py` | `tsp.py` | Travelling Salesman Problem sample. |
| `vrp.py` | `vrp.py` | Vehicle Routing Problem sample. |
| `vrp_capacity.py` | `vrp_capacity.py` | Capacity-constrained VRP sample. |
| `vrp_time_windows.py` | `vrp_time_windows.py` | VRP with time windows sample. |
| `LICENSE` | OR-Tools `LICENSE` | Apache License 2.0. |

## Project Adapters

`project_adapters/` contains project-written scripts that were used to produce
compact JSON tables and route visualisations for this research repository.
Those files are not official OR-Tools source code.

## Run Official Samples

```bash
python -m pip install -r requirements.txt
python tsp.py
python vrp.py
python vrp_capacity.py
python vrp_time_windows.py
```

## Existing Result Artifacts

The `results/` folder contains previously generated project artifacts:

- `baseline_results.json`
- `route_tables.md`
- `baseline_routes.png`
