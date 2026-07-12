# Week 4: Method Improvement — Composite-Score Greedy with 2-opt

Week 4 extends the Week 3 controlled comparison by implementing the improvement
that the Week 3 report recommended.  Week 3 found that the due-time-priority
greedy (Method A) was worse than the nearest-customer baseline (Method B): it
caused coverage failures and produced long, vehicle-heavy routes.  Week 3's
"next steps" asked for a combined scoring rule and a local-search repair.

This week adds **Method C**, a composite-score greedy followed by a
feasibility-aware **2-opt** local search, and evaluates it against Methods A and
B on the same instances, across three scales and three stress profiles.

## Research question

> Does a composite-score greedy with feasibility-aware 2-opt local search
> recover the feasibility and route quality lost by the Week 3 due-time-only
> method, and how does it compare with the nearest-customer baseline across
> scales and under tighter time windows / smaller batteries?

## Files

- `composite_score.py` — Method C selector. Ranks feasible customers by a
  weighted score of normalized travel distance, due-time urgency, and
  time-window slack.
- `two_opt.py` — feasibility-aware 2-opt operator. A segment reversal is kept
  only when an injected checker confirms the route is still feasible and
  strictly shorter.
- `compare_week4_methods.py` — runner. Reuses the Week 3 instance generator and
  constraint model, imports Methods A and B unchanged, adds Method C, and runs
  the parameter-sensitivity profiles.
- `visualize_week4.py` — matplotlib figures (feasibility, objective, 2-opt gain,
  representative routes).

## Controlled-comparison design

All three methods share, on every instance:

- the same Week 3 instance generator, coordinates, and random seeds;
- the same objective definition (total route distance);
- the same EVRP-TW feasibility checker;
- the same vehicle, battery, charging, and stopping rules.

Only two things change for the tested method: the customer-ranking rule
(composite score) and the added 2-opt post-processing. This isolates the effect
of the improvement.

## Parameter-sensitivity profiles

| Profile | Change vs Week 3 | Purpose |
|---|---|---|
| `baseline` | none (Week 3 parameters) | reproduce the Week 3 setting |
| `tight_tw` | time windows shrunk to 60% width | stress time-window feasibility |
| `small_battery` | battery capacity reduced to 75% | stress energy feasibility |

## Run

```bash
python3 compare_week4_methods.py --scales 20 50 100 --instances-per-scale 12 --seed 20260706
python3 visualize_week4.py
```

## Outputs

- `results/week4_results.json` — metadata, aggregate rows, comparisons, full
  per-instance route records, diagnostic cases.
- `results/week4_results.csv` — aggregate table (profile × scale × method).
- `results/week4_comparison.csv` — Method C vs each reference, per profile/scale.
- `results/week4_results.md` — human-readable summary and comparison tables.
- `results/run_log.txt` — command, environment, and aggregate lines.
- `results/week4_feasibility_by_profile.png`
- `results/week4_objective_by_profile.png`
- `results/week4_two_opt_gain.png`
- `results/week4_representative_routes.png`

## Headline findings (from the committed local run)

- Method C is **feasible on 107 of 108 instances** (99.1%), versus Method A's
  frequent coverage failures (45/108 overall; 0% feasible under the
  small-battery profile). Baseline B is feasible on all 108.
- Against Baseline B, Method C is competitive on distance: it wins on the
  small and large scales and trails slightly on the 50-customer scale, while
  never increasing coverage violations except one small-battery case.
- The 2-opt step removes real distance — on average up to ~100 units per
  100-customer instance under tight time windows — confirming the local search
  is doing useful work rather than being decorative.

See `../../../docs/week4_method_improvement.md` for the full report with
discussion and failure analysis.
