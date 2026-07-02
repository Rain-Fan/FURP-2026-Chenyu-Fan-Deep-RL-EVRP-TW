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
- Route visualisation: `src/results/route_visualization.png`
