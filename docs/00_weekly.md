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

**Attended this week's meeting:** Not recorded

**Progress this week**
- Set up repository from the FURP template.
- Initialized `/src` directory structure: `data/`, `experiments/`, `results/`.
- Added the Deep RL for EVRP-TW implementation under `src/experiments/deep_rl/`.
- Implemented a batched PyTorch environment with capacity, time-window,
  battery, charging-station, and fleet constraints.
- Added a feasibility-first greedy baseline, REINFORCE, and PPO.
- Added experiment configurations, training and evaluation scripts,
  visualisation tools, notebooks, and automated tests.
- Added representative problem, route, and training figures to `src/results/`.
- Ran the automated test suite: 10 tests passed.
- Completed the two-iteration REINFORCE smoke training on Apple MPS.

**Challenges & blockers**
- The cited paper and final benchmark datasets still need to be confirmed.
- Short smoke runs validate execution but do not establish model performance.

**Next steps**
- Confirm the paper to reproduce and the required innovation.
- Run controlled experiments across fixed seeds and customer sizes.
- Compare feasibility, feasible route cost, runtime, and training stability.
- Add public EVRP-TW benchmark loaders and stronger optimisation baselines.

**Hours spent (optional):** Not recorded

**Links (optional):**
- Repository: https://github.com/Rain-Fan/FURP-2026-Chenyu-Fan-Deep-RL-EVRP-TW
- Implementation: `src/experiments/deep_rl/`
- Route visualisation: `src/results/route_visualization.png`
- Smoke configuration: `src/experiments/deep_rl/experiments/configs/smoke.yaml`
