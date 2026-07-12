# Local Result Provenance

This folder keeps only result artifacts that can be regenerated from repository
commands.  The old generic PNG placeholders were removed because they did not
have a current reproducible generation path.

## Reproduced Locally

Run date: 2026-07-03 (Weeks 1-3), 2026-07-12 (Week 4)

Week 1:

```bash
cd src/experiments/week1
python3 compare_or_tools_baselines.py
```

Generated:

- `src/experiments/week1/results/baseline_results.json`
- `src/experiments/week1/results/route_tables.md`
- `src/experiments/week1/results/baseline_routes.png`

Week 2:

```bash
cd src/experiments/week2
python3 compare_week2_baselines.py --scales 50 100 200 --seed 20260621 --or-time-limit 8
```

Generated:

- `src/experiments/week2/results/week2_results.json`
- `src/experiments/week2/results/week2_results.csv`
- `src/experiments/week2/results/week2_results.md`

Week 3:

```bash
cd src/experiments/week3
python3 compare_week3_baselines.py --scales 20 50 100 --instances-per-scale 12 --seed 20260630
```

Generated:

- `src/experiments/week3/results/run_log.txt`
- `src/experiments/week3/results/week3_results.json`
- `src/experiments/week3/results/week3_results.csv`
- `src/experiments/week3/results/week3_comparison.csv`
- `src/experiments/week3/results/week3_results.md`

Week 4:

```bash
cd src/experiments/week4
python3 compare_week4_methods.py --scales 20 50 100 --instances-per-scale 12 --seed 20260706
python3 visualize_week4.py
```

Generated:

- `src/experiments/week4/results/run_log.txt`
- `src/experiments/week4/results/week4_results.json`
- `src/experiments/week4/results/week4_results.csv`
- `src/experiments/week4/results/week4_comparison.csv`
- `src/experiments/week4/results/week4_results.md`
- `src/experiments/week4/results/week4_feasibility_by_profile.png`
- `src/experiments/week4/results/week4_objective_by_profile.png`
- `src/experiments/week4/results/week4_two_opt_gain.png`
- `src/experiments/week4/results/week4_representative_routes.png`

Visualizations:

```bash
python3 src/results/generate_research_visualizations.py
```

Generated:

- `src/results/week2_baseline_comparison.svg`
- `src/results/week3_performance_summary.svg`
- `src/results/week3_diagnostic_summary.svg`
- `src/results/week3_representative_routes.svg`
- `src/results/week4_performance_summary.svg`
- `src/results/week4_profile_sensitivity.svg`
- `src/results/week4_representative_routes.svg`
- `src/results/research_visualizations.md`
