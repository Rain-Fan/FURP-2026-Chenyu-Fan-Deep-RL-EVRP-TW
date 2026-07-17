# Weekly Progress Log

> Update this file **every week**. Add a new entry at the top for each week.
> This is the first thing we check during review. Keep it honest and specific — it also feeds your attendance record (Rule 1).

**How to use:** copy the *Week template* block below for each new week. Newest week goes at the top.

---

## Week template — copy me

### Week N — YYYY-MM-DD

**Attended this week's meeting:** Yes / No (if No, did you email leave? Yes / No)

**Progress this week**
- _What did you actually do / finish?_

**Challenges & blockers**
- _What got in the way? What are you stuck on?_

**Next steps**
- _What will you do next week?_

**Hours spent (optional):** _e.g. 6h_

**Links (optional):** _commits, notebooks, docs, datasets..._

---
<!-- =================  YOUR ENTRIES BELOW  ================= -->


### Week 5 — 2026-07-13

**Attended this week's meeting:** Yes

**Progress this week**
- Treated Week 5 as the consolidation week described in the lab, following Track
  B (consolidate/verify) and Track C (one focused extension) since Weeks 1-4
  were already complete.
- Track C: implemented Method D = the Week 4 composite-score + 2-opt method plus
  feasibility-aware inter-route local search (or-opt relocation and customer
  swap), which is exactly the next step the Week 4 report recommended.
- Reused the Week 3 instance generator and the Week 4 construction / 2-opt /
  feasibility code unchanged, so Method D differs from Method C only by the new
  inter-route step (controlled comparison).
- Ran the controlled A/B/C/D comparison over 3 scales x 3 stress profiles x 12
  instances = 324 runs, all locally.
- Result: Method D closes the Week 4 medium-scale gap. Method C was worse than
  the nearest-customer baseline at n=50 (+1.6%) and n=100 (+2.7%); Method D is
  now shorter than the baseline on every scale and profile by about 9-16%, and
  beats Method C by about 6-16%, while keeping the same feasibility.
- Track B: wrote a reproducibility check that solves each instance 3 times and
  confirms identical routes and objective. All 135 checks pass, so the results
  are deterministic with a fixed seed.
- Added four matplotlib figures (objective, gap-vs-baseline, local-search gain,
  representative routes), two cross-week SVGs, and the required project
  checkpoint note.

**Challenges & blockers**
- Two small-battery n=20 instances stay infeasible for both C and D because the
  failure happens during greedy construction; inter-route moves only reorder an
  already feasible solution, so they cannot repair coverage.
- Inter-route search is O(n^2) per route pair, so Method D at n=100 takes about
  0.85 s per instance versus 0.03 s for Method C. Fine at these scales but needs
  a neighbourhood restriction before large benchmark instances.

**Next steps**
- Add a construction-stage / station-insertion repair so the two infeasible
  small-battery instances can be recovered, then re-run for 108/108 feasibility.
- Reconstruct the Schneider EVRP-TW benchmark format and run Method D on a few
  standard instances to compare against published baselines.

**Hours spent (optional):** 28 hours

**Links (optional):**
- Week 5 project checkpoint note: `docs/week5_checkpoint.md`
- Week 5 experiment code: `src/experiments/week5/compare_week5_methods.py`
- Week 5 inter-route operators: `src/experiments/week5/inter_route_moves.py`
- Week 5 reproducibility check: `src/experiments/week5/reproducibility_check.py`
- Week 5 experiment README: `src/experiments/week5/README.md`
- Week 5 summary table: `src/experiments/week5/results/week5_results.md`
- Week 5 D-vs-references table: `src/experiments/week5/results/week5_comparison.csv`
- Week 5 reproducibility report: `src/experiments/week5/results/reproducibility_report.md`
- Week 5 figures: `src/experiments/week5/results/week5_*.png`


### Week 4 — 2026-07-06

**Attended this week's meeting:** Yes

**Progress this week**
- Completed a focused literature-reading round for the EVRP-TW deep reinforcement learning project.
- Read and organized notes for four key papers: Attention Model, DRL for EVRPTW, POMO, and Schneider's classical EVRP-TW formulation.
- Compared learning-based routing methods with traditional EVRP-TW metaheuristics.
- Identified reusable ideas for the project, including attention-based encoder-decoder modeling, rollout/shared baselines, multi-mask feasibility handling, station dummy-copy modeling, and EVRP-TW benchmark construction.
- Recorded reproducibility issues, assumptions, experiment metrics, open questions, and next action items for each paper.
- Implemented the method improvement recommended at the end of Week 3: a new
  tested method `C_composite_score` (composite-score greedy) followed by a
  feasibility-aware 2-opt local search.
- Ran a new controlled experiment comparing Method C against the Week 3
  due-time method (A) and the nearest-customer baseline (B) on the same
  instance generator, across scales 20/50/100 and three parameter-sensitivity
  profiles (baseline, tight time windows, small battery): 324 total runs.
- Method C raised overall feasibility from Method A's 41.7% (45/108) to 99.1%
  (107/108) and cut feasible route distance by up to ~2700 units versus A,
  while staying competitive with baseline B (winning at n=20 and n=100, and
  trailing slightly at n=50).
- Added four matplotlib visualizations (feasibility, objective, 2-opt gain, and
  representative route geometry) and a full Week 4 report with setup, results,
  discussion, and failure analysis.

**Challenges & blockers**
- The DRL EVRPTW paper is directly relevant but does not appear to provide easily reusable public code.
- POMO is powerful for TSP/CVRP, but its multi-start symmetry does not transfer directly to EVRP-TW because time windows and battery state break many route symmetries.
- Schneider's EVRP-TW model assumes full recharging at stations, while the project may need a more flexible partial-charging model.
- Method C beats the nearest-customer baseline at small and large scales but is
  slightly worse at 50 customers, so the improvement is real but not universal.

**Next steps**
- Make the composite-score weights scale-aware and add inter-route local-search
  moves (or-opt, swap) to close the medium-scale gap against baseline B.
- Download or reconstruct the Schneider EVRP-TW benchmark format.
- Implement an EVRP-TW feasibility checker covering customer service, capacity, time windows, battery use, charging, depot return, and customer coverage.
- Decide whether the project model will use full charging, discrete partial charging, or continuous partial charging.
- Use the paper notes to choose the first DRL architecture and training baseline to implement.

**Hours spent (optional):** 30 hours

**Links (optional):**
- Attention Model reading note: `docs/reading_notes/week4/01_Attention_Model_Kool2018.md`
- DRL EVRPTW reading note: `docs/reading_notes/week4/02_DRL_EVRPTW_Lin2021.md`
- POMO reading note: `docs/reading_notes/week4/03_POMO_Kwon2020.md`
- Schneider EVRP-TW reading note: `docs/reading_notes/week4/04_EVRPTW_Schneider2014.md`
- Week 4 method-improvement report: `docs/week4_method_improvement.md`
- Week 4 experiment code: `src/experiments/week4/compare_week4_methods.py`
- Week 4 experiment README: `src/experiments/week4/README.md`
- Week 4 summary table: `src/experiments/week4/results/week4_results.md`
- Week 4 A/B/C comparison table: `src/experiments/week4/results/week4_comparison.csv`
- Week 4 figures: `src/experiments/week4/results/week4_*.png`

### Week 3 — 2026-06-30

**Attended this week's meeting:** Yes

**Progress this week**
- Converted the Week 3 work from simply recreating a runnable method into a
  controlled method-evaluation experiment.
- Defined the tested method as `A_due_time_priority`, which selects the
  feasible unserved customer with the earliest due-time priority.
- Defined the comparison baseline as `B_nearest_customer`, which selects the
  feasible unserved customer with the shortest current travel distance.
- Kept the comparison fair by using the same generated instance set, random
  seeds, coordinate data, distance matrix, objective definition, EVRP-TW
  feasibility checker, vehicle constraints, charging rules, and stopping
  condition for both methods.
- Ran local controlled experiments on small, medium, and large EVRP-TW
  instances: 20, 50, and 100 customers, with 12 generated instances per scale.
- Recorded objective distance, feasibility rate, runtime, vehicle count,
  charging count, time-window violations, capacity violations, energy
  violations, coverage violations, random seed, hardware, and solver
  parameters.
- Generated a cleaned summary table, an A-vs-B comparison table, full JSON
  route records, CSV result tables, a local run log, and a short experimental
  report with setup, results, discussion, failure cases, and conclusion.

**Challenges & blockers**
- The tested due-time-priority method did not outperform the nearest-customer
  baseline on this controlled instance set.
- Method A had lower feasibility than Baseline B: 0.250 vs 1.000 on 20-customer
  instances, 0.500 vs 1.000 on 50-customer instances, and 0.917 vs 1.000 on
  100-customer instances.
- Method A also had much longer feasible objective distance than Baseline B:
  +327.701 at 20 customers, +1061.437 at 50 customers, and +2642.877 at 100
  customers.
- The main failure mode was coverage: Method A sometimes used all available
  vehicles before serving every customer, even though time-window, capacity,
  and energy violations were zero.
- A due-time-only priority can create spatially inefficient routes, causing
  more vehicle use and more charging-station visits.

**Next steps**
- Design a stronger scoring rule that combines distance, due-time slack,
  remaining battery, route load, and depot-return reserve instead of using due
  time alone.
- Re-run the same controlled comparison against `B_nearest_customer` using the
  same instance set and metrics.
- Add local-search or route-repair steps to reduce coverage failures and
  unnecessary charging visits.
- Preserve the current Week 3 result files as the baseline evidence for later
  ablation and improvement comparisons.

**Hours spent (optional):** 30 hours

**Links (optional):**
- Week 3 meeting notes: `docs/meeting_notes/2026-07-01.md`
- Week 3 controlled evaluation report: `docs/week3_baseline_reproduction.md`
- Week 3 experiment code: `src/experiments/week3/compare_week3_baselines.py`
- Week 3 experiment README: `src/experiments/week3/README.md`
- Week 3 local run log: `src/experiments/week3/results/run_log.txt`
- Week 3 summary table: `src/experiments/week3/results/week3_results.md`
- Week 3 aggregate results: `src/experiments/week3/results/week3_results.csv`
- Week 3 A-vs-B comparison table: `src/experiments/week3/results/week3_comparison.csv`
- Week 3 full route and diagnostic records: `src/experiments/week3/results/week3_results.json`

### Week 2 — 2026-06-24

**Attended this week's meeting:** Yes

**Progress this week**
- Attended the second weekly meeting and participated in the group repository
  review.
- Checked each group member's GitHub repository and reviewed whether the
  project files, reports, and experiment records were organized clearly.
- Discussed GitHub repository-format issues, including folder structure, file
  naming, README clarity, weekly-report placement, and links between reports
  and supporting files.
- Gave and received suggestions on repository content, including making
  progress records specific, recording experiment commands and outputs, and
  keeping evidence easy to inspect.
- Clarified that the next stage should combine paper reading with independent
  experiments so that different methods can be compared fairly.

**Challenges & blockers**
- Some repositories still need clearer structure so weekly progress can be
  inspected quickly.
- Some reports need more concrete links to code, experiment records, command
  outputs, or paper notes.
- A fair method comparison requires consistent experiment settings, metrics,
  and reproducible records rather than only reading conclusions from papers.

**Next steps**
- Revise the GitHub repository format according to the meeting feedback,
  especially README structure, weekly-report links, and experiment records.
- Read papers covering different EVRP-TW or routing-solver methods.
- Choose representative methods and run self-contained experiments.
- Compare different methods using consistent metrics such as feasibility,
  objective value, runtime, scalability, and implementation difficulty.

**Hours spent (optional):** 30 hours

**Links (optional):**
- Week 2 meeting notes: `docs/meeting_notes/2026-06-24.md`

### Week 1 — 2026-06-12

**Attended this week's meeting:** Yes

**Progress this week**
- Developed a structured understanding of TSP, VRP, CVRP, VRPTW, and their
  relationship to the target EVRP-TW formulation.
- Configured and validated the research environment, including Python,
  Google OR-Tools, Matplotlib, Git, and the project repository structure.
- Reproduced the official Google OR-Tools TSP, VRP, CVRP, and VRPTW
  demonstration baselines on the 17-node instances.
- Generated reproducible route tables, machine-readable solver results, and
  route visualisations for all four baseline problems.
- Established the principal evaluation rule for later experiments: objective
  values must be compared only among feasible solutions, with feasibility,
  route cost, fleet use, and runtime reported separately.
- Organized the baseline artifacts and selected route visualisations for
  later EVRP-TW method comparison.

**Challenges & blockers**
- The cited paper and final public benchmark datasets remain to be confirmed.
- OR-Tools demonstration instances establish functional correctness but are
  not sufficient for claims regarding scalability or comparative performance.

**Next steps**
- Confirm the paper to reproduce and the required innovation.
- Formalise a common EVRP-TW evaluation protocol with fixed instances and
  random seeds.
- Add public EVRP-TW benchmark loaders and stronger optimisation baselines.
- Compare later methods using feasibility rate, feasible route cost, fleet
  use, runtime, and constraint-violation diagnostics.

**Hours spent (optional):** 30 hours

**Links (optional):**
- Repository: https://github.com/Rain-Fan/FURP-2026-Chenyu-Fan-Deep-RL-EVRP-TW
- Week 1 baseline report: `docs/week1_or_tools_baselines.md`
- Reproducible OR-Tools baselines: `src/experiments/week1/`
- Route visualisation: `src/experiments/week1/results/baseline_routes.png`
