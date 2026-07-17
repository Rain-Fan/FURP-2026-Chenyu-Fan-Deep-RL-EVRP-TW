# Week 5 local reproducibility evidence

Generate the evidence from the repository root with:

```bash
python3 src/experiments/week5/run_reproducibility_check.py
```

The wrapper runs the Week 4 comparison twice using the fixed configuration:

```text
--scales 20 50 100 --instances-per-scale 12 --seed 20260706 \
--profiles baseline tight_tw small_battery
```

The generated output is local-only evidence: the two complete Week 4 output
sets are stored in `results/run_1/` and `results/run_2/`, and their console
logs are stored as `results/run_1.log` and `results/run_2.log`. The machine-
readable comparison is `results/week5_reproducibility.json`; the corresponding
human-readable report is `results/week5_reproducibility.md`.

The comparison requires all deterministic aggregate cells to match. It
deliberately excludes measured runtime columns, since runtime varies with
machine load and is therefore not reproducibility evidence.
