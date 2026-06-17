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
