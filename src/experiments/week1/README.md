# Week 1: OR-Tools Routing Baselines

Week 1 reproduces small OR-Tools-style routing examples for TSP, VRP, CVRP,
and VRPTW.  The scripts follow the same basic structure as the OR-Tools
documentation examples: create data, create the routing model, register
callbacks, set dimensions or constraints, solve, and print or export the
solution.

## Files

- `tsp.py`: travelling-salesman baseline.
- `vrp.py`: multi-vehicle routing baseline.
- `cvrp.py`: capacity-constrained VRP baseline.
- `vrptw.py`: VRP with time-window baseline.
- `routing_data.py`: shared 17-node data used by the four baselines.
- `or_tools_common.py`: shared OR-Tools helper functions.
- `compare_or_tools_baselines.py`: local runner that writes result artifacts.

## Run

```bash
python -m pip install -r requirements.txt
python compare_or_tools_baselines.py
```

## Outputs

- `results/baseline_results.json`
- `results/route_tables.md`
- `results/baseline_routes.png`
