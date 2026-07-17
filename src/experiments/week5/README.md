# Week 5: Consolidation — Inter-Route Local Search

Week 5 is the consolidation week.  Weeks 1–4 built a controlled EVRP-TW
comparison pipeline and, in Week 4, a composite-score greedy with intra-route
2-opt (Method C).  The Week 4 report found that Method C still trailed the
nearest-customer baseline (Method B) on the medium 50-customer scale and named
inter-route local search (or-opt relocation + swap) as the next step.

This week follows two of the Week 5 lab tracks:

- **Track C (one focused extension):** add **Method D** = Method C + inter-route
  local search (relocate + swap).  Method D is the only new method; C and B are
  carried over unchanged from Weeks 3–4 so the comparison stays controlled.
- **Track B (consolidate / verify):** rerun the same instance set across scales
  and stress profiles, and verify with a companion script that the algorithmic
  outputs are deterministic across repeated runs.

## Research question

> Does adding inter-route local search (or-opt relocation and swap) on top of
> the Week 4 composite-score + 2-opt method close the medium-scale distance gap
> against the nearest-customer baseline, without losing feasibility?

## Files

- `inter_route_moves.py` — the two feasibility-aware inter-route operators:
  - `relocate_pass` (or-opt-1): move one customer to the best feasible position
    in another route;
  - `swap_pass`: exchange one customer between two routes;
  - `inter_route_optimize`: alternate relocate and swap sweeps until neither
    improves the solution.
  A move is accepted only when the injected checker confirms every affected
  route stays feasible and the combined distance strictly decreases.
- `compare_week5_methods.py` — runner. Reuses the Week 3 instance generator and
  the Week 4 construction / 2-opt / feasibility code, imports Methods C and B
  unchanged, and adds Method D.
- `reproducibility_check.py` — Track B verification. Solves each instance
  several times and confirms the routes and objective are identical every time.
- `visualize_week5.py` — matplotlib figures (objective, gap-vs-baseline, local
  search gain, representative routes).

## Controlled-comparison design

All three methods share, on every instance:

- the same Week 3 instance generator, coordinates, and random seeds;
- the same objective definition (total route distance);
- the same EVRP-TW feasibility checker;
- the same vehicle, battery, charging, and stopping rules.

Method D differs from Method C only by the added inter-route local-search step,
so the experiment isolates that one change.

## Parameter-sensitivity profiles

Same three profiles as Week 4, so the two weeks are directly comparable:

| Profile | Change vs Week 3 parameters | Purpose |
|---|---|---|
| `baseline` | none | reproduce the Week 3/4 setting |
| `tight_tw` | time windows shrunk to 60% width | stress time-window feasibility |
| `small_battery` | battery capacity reduced to 75% | stress energy feasibility |

## Run

```bash
# Controlled A/B/C/D comparison across scales and stress profiles (324 runs)
python3 compare_week5_methods.py --scales 20 50 100 --instances-per-scale 12 --seed 20260713

# Reproducibility / determinism check (135 checks, 3 repeats each)
python3 reproducibility_check.py --scales 20 50 100 --instances-per-scale 5 --repeats 3

# Figures from the committed results
python3 visualize_week5.py
```

## Outputs

- `results/week5_results.json` — metadata, aggregate rows, comparisons, full
  per-instance route records, and the largest D-over-C improvements.
- `results/week5_results.csv` — aggregate table (profile × scale × method).
- `results/week5_comparison.csv` — Method D vs each reference, per profile/scale.
- `results/week5_results.md` — human-readable summary and comparison tables.
- `results/run_log.txt` — command, environment, and aggregate lines.
- `results/reproducibility_report.md` / `.json` — determinism check result.
- `results/week5_objective_by_profile.png`
- `results/week5_gap_vs_baseline.png`
- `results/week5_ls_gain.png`
- `results/week5_representative_routes.png`

## Headline findings (from the committed local run)

- **The Week 4 medium-scale gap is closed.** Method C was worse than baseline B
  at n=50 (+1.6%) and n=100 (+2.7%); Method D is now shorter than B on every
  scale and profile, by roughly 9–16%.
- **Method D beats Method C everywhere** by about 6–16% on mean feasible
  distance, confirming the inter-route moves add value on top of 2-opt.
- **Feasibility is preserved.** D matches C's feasibility on all profiles; both
  lose the same two `small_battery` n=20 instances to a construction-stage
  failure that local search cannot repair (documented honestly).
- **Reproducibility verified.** All 135 determinism checks pass: every method
  produces identical routes and objective across repeated runs with a fixed
  seed.
- **Cost:** inter-route search is O(n²) per route pair, so Method D is slower
  than C (about 0.85 s per 100-customer instance vs 0.03 s), but still fast at
  these scales.

See `../../../docs/week5_checkpoint.md` for the project checkpoint note with the
required status / evidence / limitations / next-step sections.
