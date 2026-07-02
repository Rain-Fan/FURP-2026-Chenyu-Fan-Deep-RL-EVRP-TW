# `/src` - EVRP-TW Research Experiments

> **Reproducible baseline experiments for vehicle routing and EVRP-TW**

## Directory Structure

```text
/src
  README.md
  data/                  Shared dataset notes or links
  experiments/week1/
  experiments/week2/
  experiments/week3/
  results/               Selected figures and compact result summaries
```

The experiment packages contain:

```text
week1/  OR-Tools TSP, VRP, CVRP, and VRPTW algorithm files plus comparison
week2/  POMO-style, GA, and OR-style algorithm files plus comparison
week3/  Due-time-priority and nearest-customer greedy files plus comparison
```

## Getting Started

```bash
cd src/experiments/week1
python -m pip install -r requirements.txt
python compare_or_tools_baselines.py
```

Week 3 baseline results can be regenerated with:

```bash
python3 src/experiments/week3/compare_week3_baselines.py --scales 20 50 100 --instances-per-scale 12 --seed 20260630
```

## Notes

- Generated checkpoints, logs, and large datasets are excluded from Git.
- Objective values should only be compared for feasible solutions.
- Exact seeds and YAML configurations should be retained with every result.

---

_Project by Chenyu Fan · UNNC FURP 2026_
