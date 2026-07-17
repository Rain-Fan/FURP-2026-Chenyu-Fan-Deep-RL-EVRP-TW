# Week 5 Project Checkpoint

**Project:** Deep RL for Electric Vehicle Routing with Time Windows (EVRP-TW)
**Student:** Chenyu Fan · **Supervisor:** Tianxiang Cui
**Week 5 track:** Track B (consolidate and verify) + Track C (one focused
extension). Weeks 1–4 are already complete, so this week strengthens the
existing pipeline and adds the single extension the Week 4 report asked for.

---

## 1. Current Project Status

**Problem.** Electric Vehicle Routing Problem with Time Windows (EVRP-TW): route
a fleet of battery-limited vehicles from a depot to serve every customer inside
its time window, respecting vehicle capacity, battery consumption, and recharging
at stations, while minimising total route distance.

**What has been implemented and reproduced.**

- Week 1: OR-Tools routing baselines for TSP / VRP / CVRP / VRPTW.
- Week 2: an EVRP-TW baseline comparison (POMO-style greedy, GA repair,
  OR-Tools + charging repair) with a shared instance generator.
- Week 3: a controlled greedy-policy comparison — due-time priority (A) vs
  nearest-customer (B) — with a full EVRP-TW feasibility checker.
- Week 4: Method C, a composite-score greedy plus feasibility-aware intra-route
  2-opt, evaluated against A and B across three scales and three stress profiles.
- Week 5 (this week): Method D, which adds **inter-route local search** (or-opt
  relocation + customer swap) on top of Method C, plus a reproducibility check.

**What currently works.**

- The end-to-end pipeline runs locally and deterministically: generate instances
  → construct routes → local search → independently validate → aggregate → plot.
- Method D is feasible on 106 / 108 instances and produces the shortest feasible
  routes of any method built so far.
- All results, tables, logs, and figures are regenerated from committed scripts.

**What is not finished yet.**

- The project has not yet moved to the learned (deep-RL) policy that is the
  final research goal; the current methods are heuristic baselines.
- Two `small_battery` n=20 instances remain infeasible for both C and D because
  the failure happens during construction, which local search cannot repair.

---

## 2. Evidence of Progress

All numbers below are from the committed local run
(`src/experiments/week5/results/week5_results.json`, base seed 20260713,
12 instances per scale).

Representative instances (baseline profile, one seed per scale):

| Instance | Method | Feasible | Objective | Runtime (s) | Main Observation |
|---|---|---|---:|---:|---|
| n=20 seed 20280713 | B nearest | Yes | 448.5 | 0.0002 | compact baseline |
| n=20 seed 20280713 | C composite+2opt | Yes | 448.4 | 0.0010 | ties baseline here |
| n=20 seed 20280713 | D +inter-route | Yes | 401.2 | 0.0055 | 4 relocations shorten routes |
| n=100 seed 20360723 | C composite+2opt | Yes | 1307.1 | 0.030 | 2-opt only |
| n=100 seed 20360723 | D +inter-route | Yes | 1039.8 | 0.85 | 87 inter-route moves, −267 |

Aggregate comparison of Method D against the two references (mean over 12
feasible instances per cell):

| Profile | Customers | vs C (%) | vs B baseline (%) |
|---|---:|---:|---:|
| baseline | 20 | −10.23 | −12.93 |
| baseline | 50 | −11.30 | −9.89 |
| baseline | 100 | −14.17 | −11.83 |
| tight_tw | 50 | −12.67 | −10.56 |
| small_battery | 100 | −15.44 | −10.45 |

Negative percentages mean Method D is shorter. The key result: at n=50 the Week 4
Method C was **+1.6% worse** than baseline B; Method D is now **−9.89% better**,
so the gap the Week 4 report flagged is closed.

Supporting figures (in `src/experiments/week5/results/`):

- `week5_gap_vs_baseline.png` — C is above the baseline line at n=50/100; D is
  below it everywhere.
- `week5_objective_by_profile.png` — mean feasible objective per method.
- `week5_ls_gain.png` — local-search distance removed roughly triples from C to D.
- `week5_representative_routes.png` — D's routes have visibly fewer crossings.

Reproducibility evidence (`results/reproducibility_report.md`): all **135**
determinism checks pass — every method returns identical routes and objective
across 3 repeats with the same seed.

---

## 3. Problems and Limitations

- **Construction-stage infeasibility.** Two `small_battery` n=20 instances are
  infeasible for both C and D. The cause is the greedy construction stranding a
  customer with too little battery; inter-route moves only reorder an already
  feasible solution, so they cannot fix it. A construction-time repair or a
  station-insertion operator would be needed.
- **Runtime growth.** Inter-route search evaluates O(n²) candidate moves per
  route pair, so Method D at n=100 takes about 0.85 s per instance versus 0.03 s
  for Method C. This is fine for the current scales but will not scale to the
  large benchmark instances without a neighbourhood restriction (e.g. only
  consider geographically near routes).
- **Heuristic, not learned.** These are still construction + local-search
  heuristics. They are useful, reproducible baselines but are not the deep-RL
  method that is the project's final target.
- **Synthetic instances.** Instances come from the project generator, not the
  standard Schneider EVRP-TW benchmark, so the numbers are internally comparable
  but not yet comparable to published results.

---

## 4. Next Step

One or two concrete tasks for the following week:

1. **Add a construction-stage / station-insertion repair operator** so the two
   `small_battery` n=20 infeasible instances can be recovered, and re-run the
   Week 5 comparison to confirm 108/108 feasibility.
2. **Reconstruct the Schneider EVRP-TW benchmark format** and run Method D on a
   few standard instances so the heuristic can be compared against published
   baselines before starting the learned policy.

---

## Reproduce

```bash
cd src/experiments/week5
python3 compare_week5_methods.py --scales 20 50 100 --instances-per-scale 12 --seed 20260713
python3 reproducibility_check.py --scales 20 50 100 --instances-per-scale 5 --repeats 3
python3 visualize_week5.py
```

Outputs are written to `src/experiments/week5/results/`.
