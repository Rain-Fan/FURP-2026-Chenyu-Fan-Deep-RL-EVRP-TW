# Week 4 Method Improvement: Composite-Score Greedy with 2-opt

**Project:** Deep RL for Electric Vehicle Routing with Time Windows (EVRP-TW)
**Student:** Chenyu Fan · **Supervisor:** Tianxiang Cui
**Week 4 deliverable:** extend the Week 3 baseline with a meaningful method
improvement, evaluate it under new experimental settings, and report the
results with evidence.

---

## 1. Motivation

Week 3 ran a controlled comparison between two greedy customer-selection
policies on synthetic EVRP-TW instances:

- **Method A** (`A_due_time_priority`) — pick the feasible customer with the
  earliest due time.
- **Baseline B** (`B_nearest_customer`) — pick the feasible customer that is
  closest to the current position.

The Week 3 result was clear and negative for Method A: it had lower feasibility
(0.250 / 0.500 / 0.917 at 20 / 50 / 100 customers versus 1.000 for B) and much
longer feasible routes (+327.7 / +1061.4 / +2642.9). Its main failure mode was
**coverage**: a due-time-only rule chases deadlines across the map, so vehicles
run out before every customer is served.

Week 3's own "next steps" recommended:

1. a scoring rule that combines distance, due-time slack, and reserve, instead
   of using due time alone; and
2. a local-search / route-repair step to cut unnecessary distance and charging.

Week 4 implements both and tests whether they close the gap.

---

## 2. Proposed method (Method C)

**`C_composite_score` = composite-score greedy construction + feasibility-aware
2-opt.**

### 2.1 Composite scoring rule

At each construction step the shared Week 3 feasibility checker returns the
list of feasible customers. Method C ranks them by a weighted sum of three
normalized terms (lower is better):

```
score = 1.00 * norm_distance      # keep routes compact (fixes Week 3 failure)
      + 0.35 * norm_urgency        # prefer earlier due times
      + 0.25 * norm_slack          # prefer tight remaining time-window slack
```

Each term is normalized over the current candidate set so the weights behave
consistently regardless of instance scale. Distance dominates — that is the
lever that directly attacks Week 3's coverage/length failure — while urgency
and slack break ties toward customers that would otherwise become infeasible
later. The weights are fixed before the experiment and are **not** tuned per
instance.

### 2.2 Feasibility-aware 2-opt

After a route is constructed, 2-opt repeatedly reverses a segment of the
visiting order and keeps the change only when an independent single-route
checker confirms the route is **still feasible** (load, time windows, battery)
**and strictly shorter**. Segment endpoints are restricted to customer
positions so depot anchors and inserted charging stations keep their roles.
Only Method C uses this step, so its contribution is directly attributable.

---

## 3. Experimental setup

- **Instances:** the exact Week 3 generator (`generate_instance`), so
  coordinates, demands, stations, and seeds are identical.
- **Scales:** 20, 50, 100 customers.
- **Instances per scale:** 12 (seeds derived as `base_seed + scale*1000 + offset`).
- **Base seed:** 20260706.
- **Methods:** C (tested), A (Week 3 reference), B (baseline) — all sharing one
  feasibility checker, objective, and stopping rule.
- **Parameter-sensitivity profiles** (new this week):

  | Profile | Change | Stresses |
  |---|---|---|
  | `baseline` | Week 3 parameters | — |
  | `tight_tw` | time windows shrunk to 60% width | time-window feasibility |
  | `small_battery` | battery capacity at 75% | energy feasibility |

- **Total runs:** 3 profiles × 3 scales × 12 instances × 3 methods = **324**.
- **Environment:** recorded in `results/run_log.txt` (Python version, platform).
- **Metrics:** feasibility rate, mean feasible objective (distance), runtime,
  vehicles used, charging visits, 2-opt moves, 2-opt distance gain, and
  per-type constraint violations.

Everything is produced by running `compare_week4_methods.py` locally; no number
is hand-entered.

---

## 4. Results

### 4.1 Feasibility (overall, across all 108 instances per method)

| Method | Feasible instances | Feasibility rate |
|---|---:|---:|
| C: composite + 2-opt | 107 / 108 | 0.991 |
| A: due-time (Week 3) | 45 / 108 | 0.417 |
| B: nearest (baseline) | 108 / 108 | 1.000 |

Method C recovers almost all of the feasibility that Method A lost, and matches
Baseline B except on a single stressed instance.

### 4.2 Mean feasible objective (route distance), `baseline` profile

| Scale | C (tested) | A (Week 3) | B (baseline) |
|---:|---:|---:|---:|
| 20 | 437.0 | 753.5 | 449.5 |
| 50 | 759.2 | 1929.1 | 724.8 |
| 100 | 1115.4 | 3833.4 | 1132.5 |

### 4.3 Method C vs references (selected deltas)

Negative objective delta = C finds shorter feasible routes; positive
feasibility delta = C is feasible more often.

| Profile | Scale | Reference | Feasibility Δ | Feasible-objective Δ |
|---|---:|---|---:|---:|
| baseline | 20 | A | +0.750 | −316.5 |
| baseline | 50 | A | +0.417 | −1169.9 |
| baseline | 100 | A | 0.000 | −2718.0 |
| baseline | 20 | B | 0.000 | −12.5 |
| baseline | 50 | B | 0.000 | +34.5 |
| baseline | 100 | B | 0.000 | −17.1 |
| small_battery | 50 | B | 0.000 | −9.7 |
| small_battery | 100 | B | 0.000 | +56.7 |
| tight_tw | 100 | B | 0.000 | +88.1 |

### 4.4 2-opt contribution (Method C, mean distance removed per instance)

| Profile | n=20 | n=50 | n=100 |
|---|---:|---:|---:|
| baseline | 15.7 | 36.5 | 87.3 |
| tight_tw | 23.0 | 44.3 | 101.6 |
| small_battery | 8.7 | 25.5 | 63.8 |

The gain grows with scale, which is expected: longer routes have more
improving reversals available.

### 4.5 Figures

- `src/experiments/week4/results/week4_feasibility_by_profile.png` — feasibility
  rate per method across scales and profiles.
- `src/experiments/week4/results/week4_objective_by_profile.png` — mean feasible
  objective per method.
- `src/experiments/week4/results/week4_two_opt_gain.png` — distance recovered by
  2-opt.
- `src/experiments/week4/results/week4_representative_routes.png` — route
  geometry for A, B, and C on the same 50-customer instance; Method A is visibly
  tangled and vehicle-heavy, while Method C is the most compact.

---

## 5. Discussion

**The composite score fixes the Week 3 failure mode.** Method A collapsed
because a due-time-only rule ignores geography, so it scatters vehicles and runs
out before covering everyone. Giving distance the dominant weight restores
compact routes; the urgency and slack terms then act as tie-breakers that avoid
stranding time-critical customers. The effect is large: at 50 customers
(`baseline`) feasibility rises from 0.583 (A) to 1.000 (C) and mean feasible
distance falls by about 1170 units.

**Against a strong baseline the win is real but modest.** Baseline B is already
very good — nearest-neighbour construction is naturally distance-compact. Method
C beats B at n=20 and n=100 but is slightly worse at n=50 (+34.5). This is an
honest trade-off, not a universal improvement: the composite score sometimes
diverts to an urgent-but-farther customer where pure nearest-neighbour would
not, and 2-opt cannot always recover that on medium routes. Under stress
profiles the picture is the same — C stays feasible and close to B, winning on
some cells (small_battery n=50: −9.7) and losing on others (tight_tw n=100:
+88.1).

**2-opt earns its place.** The measured gains (up to ~100 units) confirm the
local search removes genuine distance rather than being cosmetic, and because it
only accepts feasible reversals it never breaks a valid route.

**Runtime cost is acceptable.** Method C is slower than the pure greedies
(the 2-opt passes and the composite normalization add work), but even at 100
customers a single instance solves in well under 0.03 s, so the extra quality is
essentially free at these scales.

---

## 6. Failure-case analysis

- **Method A, small-battery profile:** feasible on 0/36 instances. Reducing the
  battery to 75% removes the slack that A relied on; because it already wastes
  distance, it can no longer reach the depot/stations before covering every
  customer. Diagnostic cases in `week4_results.md` list the specific unserved
  customers (e.g. `missing customers: [5, 14, 19, 66, 86, 89]`).
- **Method C, small-battery n=20:** one instance infeasible (coverage). With a
  tight battery and few customers, the composite rule occasionally commits a
  vehicle to an urgent far customer early, leaving a later customer unreachable
  on the remaining battery. This is the same class of failure as A but far
  rarer, and it disappears at larger scales where more stations are available.
- **Method C vs B at n=50:** feasible but longer. The composite rule's urgency
  term is the likely cause; a scale-aware weight or a stronger local-search
  neighbourhood (e.g. or-opt / inter-route moves) would probably close it.

---

## 7. Conclusion

Week 4 implemented the improvement recommended by the Week 3 report: a
composite-score greedy plus feasibility-aware 2-opt (Method C). Tested on 324
controlled runs across three scales and three stress profiles, Method C raised
feasibility from Method A's 41.7% to 99.1% and cut feasible route distance by
up to ~2700 units, while staying competitive with — and often beating — the
strong nearest-customer baseline. The one clear limitation is the medium-scale
(n=50) case where C trails B on distance, pointing to the next step: make the
score weights scale-aware and add inter-route local-search moves (or-opt, swap)
before comparing again on the same instance set. The Week 4 code, raw results,
and figures are committed so the comparison can be reproduced and extended.

---

## 8. Reproduce

```bash
cd src/experiments/week4
python3 compare_week4_methods.py --scales 20 50 100 --instances-per-scale 12 --seed 20260706
python3 visualize_week4.py
```

Outputs are written to `src/experiments/week4/results/`.
