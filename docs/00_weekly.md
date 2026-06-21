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

### Week 2 — 2026-06-21

**Attended this week's meeting:** Yes

**Progress this week**
- Read and followed the Week 2 project-hub task on baseline recreation and
  method comparison.
- Implemented a new reproducible Week 2 baseline suite covering POMO-style
  multi-start construction, GA permutation search with EV/TW repair, and an
  OR-Tools CVRPTW baseline with charging-station repair.
- Added electric-vehicle and time-window feasibility checking shared across
  all methods, including capacity, depot return, battery, charging station,
  and customer service-window validation.
- Ran experiments on 50, 100, and 200 customer instances and recorded
  objective distance, feasibility status, runtime, vehicle count, and
  convergence notes for every method.
- Wrote the Week 2 comparison/reflection document explaining objective and
  runtime differences, challenges in adding E/TW constraints, and implications
  for the target EVRP-TW model.

**Challenges & blockers**
- The original POMO repository is CVRP-specific, so a full faithful neural
  POMO training reproduction would require a larger EVRP-TW state/action
  redesign.  This week therefore recreates the multi-start masked rollout
  inference idea with explicit EV/TW constraints.
- Charging stations are repeatable nodes, which makes them harder to express
  in a simple OR-Tools CVRPTW model.  The current OR baseline handles customer
  sequencing in OR-Tools and inserts charging stations as a repair step.
- GA feasibility depends strongly on repair quality; stronger local search is
  needed before GA can be considered a competitive quality baseline.

**Next steps**
- Add stronger local search moves such as 2-opt, relocate, exchange, station
  relocation, and route-level repair.
- Use the Week 2 baselines as reference methods for the existing Deep RL
  EVRP-TW environment.
- Extend the neural policy evaluation so learned decoding can be compared both
  directly and as an initial solution for OR/local-search repair.

**Hours spent (optional):** Not recorded

**Links (optional):**
- Week 2 comparison report: `docs/week2_baseline_comparison.md`
- Week 2 baseline code: `src/experiments/week2_baselines/`
- Week 2 results table: `src/experiments/week2_baselines/results/week2_results.md`
- Week 2 machine-readable results:
  `src/experiments/week2_baselines/results/week2_results.json`

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
- Maintained the existing Deep RL EVRP-TW implementation, including the
  feasibility-first greedy baseline, REINFORCE, PPO, visualisation tools, and
  automated tests.

**Challenges & blockers**
- The cited paper and final public benchmark datasets remain to be confirmed.
- OR-Tools demonstration instances establish functional correctness but are
  not sufficient for claims regarding scalability or comparative performance.

**Next steps**
- Confirm the paper to reproduce and the required innovation.
- Formalise a common EVRP-TW evaluation protocol with fixed instances and
  random seeds.
- Add public EVRP-TW benchmark loaders and stronger optimisation baselines.
- Compare greedy, REINFORCE, and PPO using feasibility rate, feasible route
  cost, fleet use, runtime, and training stability.

**Hours spent (optional):** 30 hours

**Links (optional):**
- Repository: https://github.com/Rain-Fan/FURP-2026-Chenyu-Fan-Deep-RL-EVRP-TW
- Week 1 baseline report: `docs/week1_or_tools_baselines.md`
- Reproducible OR-Tools baselines: `src/experiments/or_tools_baselines/`
- Implementation: `src/experiments/deep_rl/`
- Route visualisation: `src/results/route_visualization.png`
- Smoke configuration: `src/experiments/deep_rl/experiments/configs/smoke.yaml`
