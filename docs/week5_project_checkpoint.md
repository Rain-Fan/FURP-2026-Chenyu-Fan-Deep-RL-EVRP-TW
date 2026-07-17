# Week 5 Project Checkpoint

## Current Project Status

The project now has local reproducibility evidence for the Week 4 controlled
EVRP-TW comparison. The fixed configuration uses scales 20, 50, and 100; 12
instances per scale; seed `20260706`; and the `baseline`, `tight_tw`, and
`small_battery` profiles. Two runs completed successfully and their
deterministic aggregate cells matched.

## Evidence of Progress

| Local evidence | Result |
|---|---|
| Reproducibility wrapper | Both runs returned code 0. |
| Deterministic comparison | Match: `true`; no differences reported. |
| `C_composite_score` in `baseline` | Feasibility 1.0 at 20, 50, and 100 customers. |
| `C_composite_score` in `tight_tw` | Feasibility 1.0 at 20, 50, and 100 customers. |
| `C_composite_score` in `small_battery` | Feasibility 0.9167 at 20 customers and 1.0 at 50 and 100 customers. |

The generated [human-readable summary](../src/experiments/week5/results/week5_reproducibility.md)
and [machine-readable summary](../src/experiments/week5/results/week5_reproducibility.json)
are local-only provenance. The full first-run aggregate table is
[`run_1/week4_results.csv`](../src/experiments/week5/results/run_1/week4_results.csv).

## Problems and Limitations

Deterministic matching shows that the compared aggregate result fields were
stable for this local fixed configuration. It does not mean runtime is stable:
measured runtime is deliberately excluded because system load can vary. This
heuristic evaluation is not a public-benchmark result or a paper reproduction.

## Next Step

1. Harden the EVRP-TW feasibility checker for customer service, capacity, time
   windows, battery use, charging, depot return, and customer coverage.
2. Add a public EVRP-TW benchmark loader for a separate benchmark evaluation.
