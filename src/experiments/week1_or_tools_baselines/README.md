# Google OR-Tools Routing Baselines

This directory contains reproducible TSP, VRP, CVRP, and VRPTW baselines
adapted from the official Google OR-Tools routing guides.

## Run

```bash
python -m pip install -r requirements.txt
python run_baselines.py
```

The script writes:

- `results/baseline_results.json`: machine-readable solver output;
- `results/route_tables.md`: route-level results;
- `results/baseline_routes.png`: route visualisations.

The experiments use the official 17-node demonstration instances and the
`PATH_CHEAPEST_ARC` first-solution strategy. The VRP also applies a distance
dimension with a global span coefficient of 100 to penalise the longest route.

## Sources

- [Routing overview](https://developers.google.com/optimization/routing)
- [TSP](https://developers.google.com/optimization/routing/tsp)
- [VRP](https://developers.google.com/optimization/routing/vrp)
- [CVRP](https://developers.google.com/optimization/routing/cvrp)
- [VRPTW](https://developers.google.com/optimization/routing/vrptw)
- [OR-Tools source repository](https://github.com/google/or-tools)
