# `/src` - EVRP-TW Research Experiments

> **Reproducible baseline experiments for vehicle routing and EVRP-TW**

## Directory Structure

```text
/src
  README.md
  data/                  Shared dataset notes or links
  experiments/week1_or_tools_baselines/
  experiments/week2_baselines/
  experiments/week3_baseline/
  results/               Selected figures and compact result summaries
```

The experiment packages contain:

```text
week1_or_tools_baselines/  OR-Tools TSP, VRP, CVRP, and VRPTW baselines
week2_baselines/           EVRP-TW method comparison artifacts
week3_baseline/            Feasibility-first greedy EVRP-TW baseline run
```

## Getting Started

```bash
cd src/experiments/week1_or_tools_baselines
python -m pip install -r requirements.txt
python run_baselines.py
```

Week 3 baseline results can be regenerated with:

```bash
python3 src/experiments/week3_baseline/run_week3_baseline.py --scales 10 25 50 --instances-per-scale 32 --seed 20260630
```

## Notes

- Generated checkpoints, logs, and large datasets are excluded from Git.
- Objective values should only be compared for feasible solutions.
- Exact seeds and YAML configurations should be retained with every result.

---

_Project by Chenyu Fan · UNNC FURP 2026_
