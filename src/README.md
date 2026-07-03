# `/src` - EVRP-TW Research Experiments

> **Reproducible baseline experiments for vehicle routing and EVRP-TW**

## Directory Structure

```text
/src
  README.md
  data/                  Shared dataset notes or links
  experiments/official_sources/
  experiments/week1/
  experiments/week2/
  experiments/week3/
  results/               Selected figures and compact result summaries
```

The experiment packages contain:

```text
official_sources/  Upstream official algorithm source files and provenance
week1/             OR-Tools wrapper experiments and comparison artifacts
week2/             EVRP-TW comparison wrappers and generated result artifacts
week3/             Controlled greedy-policy experiment wrappers and results
```

Algorithm provenance rule:

- Official algorithm source files live in `experiments/official_sources/`.
- Week-specific scripts are project wrappers, adapters, synthetic data
  generators, comparison runners, or reports unless their README explicitly
  points to an official upstream file.
- Project-written wrappers must not be described as official algorithm source
  code.

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

Research visualizations can be regenerated from the existing result JSON files
with:

```bash
python3 src/results/generate_research_visualizations.py
```

Generated visual outputs:

- `results/week2_baseline_comparison.svg`
- `results/week3_performance_summary.svg`
- `results/week3_diagnostic_summary.svg`
- `results/week3_representative_routes.svg`
- `results/research_visualizations.md`

## Notes

- Generated checkpoints, logs, and large datasets are excluded from Git.
- Objective values should only be compared for feasible solutions.
- Exact seeds and YAML configurations should be retained with every result.

---

_Project by Chenyu Fan · UNNC FURP 2026_
