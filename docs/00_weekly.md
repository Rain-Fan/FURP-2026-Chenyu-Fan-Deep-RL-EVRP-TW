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
- Weekly log detail: `src/experiments/deep_rl/docs/weekly_logs/week2.md`

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
