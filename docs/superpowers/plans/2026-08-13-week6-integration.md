# Week 6 Integrated Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and evaluate a Week 6 EVRP-TW portfolio solver with fixed and UCB1-adaptive local-search schedules, complete MDP documentation, learning-ready traces, and generated visual evidence.

**Architecture:** Reuse Week 3–5 instance, construction, feasibility, 2-opt, relocate, and swap code through thin Week 6 adapters. Keep UCB1 and trace logic pure, portfolio orchestration separate, experiment serialization reproducible, and documentation derived from committed results.

**Tech Stack:** Python 3.14, standard-library `unittest`, dataclasses, JSON/CSV, matplotlib 3.10, existing deterministic EVRP-TW modules.

## Global Constraints

- Track B is primary; Track C is a lightweight adaptive baseline, not complete RL.
- Compare B, D, E-fixed, and E-adaptive on identical instances.
- Full matrix: scales 20/50/100, profiles baseline/tight_tw/small_battery, 12 instances per cell.
- Independently validate every reported final solution and every accepted adaptive state.
- Fixed inputs must reproduce routes, objectives, action sequences, and termination.
- Generate all tables, logs, claims, traces, and figures from actual executions.
- Do not stage or modify unrelated untracked workspace files.

## File Map

- `adaptive_selector.py`: generic UCB1, reward, trace records, stopping loop.
- `portfolio_solver.py`: existing-method adapters, validation, B/D/E-fixed/E-adaptive solving.
- `compare_week6_methods.py`: controlled matrix, aggregation, serialization.
- `reproducibility_check.py`: repeated fixed-seed signature checks.
- `visualize_week6.py`: six Week 6 figures.
- `tests/`: pure unit tests, integration tests, schema and deterministic smoke tests.
- `results/`: actual JSON/CSV/Markdown/log/trace/PNG evidence.
- `docs/week6_integration.md` and `docs/week6_mdp_design.md`: Lab 6 notes.

---

### Task 1: Pure Adaptive Selection Core

**Files:**
- Create: `src/experiments/week6/adaptive_selector.py`
- Test: `src/experiments/week6/tests/test_adaptive_selector.py`

**Interfaces:**
- `normalized_reward(before: float, after: float, feasible: bool) -> float`
- `UCB1Policy(actions: tuple[str, ...], exploration_weight: float)` with `select`, `update`, `scores`
- `adaptive_search(initial, actions, objective, validate, max_steps=12, patience=4, context=None) -> SearchResult`
- Dataclasses: `ActionOutcome`, `TraceRecord`, `SearchResult`

- [ ] **Step 1: Write failing reward and policy tests**

    def test_relative_reward(self):
        self.assertAlmostEqual(normalized_reward(100.0, 90.0, True), 0.1)

    def test_infeasible_reward(self):
        self.assertEqual(normalized_reward(100.0, 80.0, False), -1.0)

    def test_exploration_order(self):
        p = UCB1Policy(("two_opt", "relocate", "swap"), 0.7)
        self.assertEqual([p.select(), p.select(), p.select()],
                         ["two_opt", "relocate", "swap"])

- [ ] **Step 2: Run RED test**

Run `python3 -m unittest src/experiments/week6/tests/test_adaptive_selector.py -v`; expect missing-module failure.

- [ ] **Step 3: Implement dataclasses, normalized reward, and UCB1**

Untried actions are selected in declaration order. Tried actions use `mean_reward + exploration_weight * sqrt(log(total_pulls) / pulls)`. Equal scores use declaration order. Selection reserves a pull so repeated selection before update still explores.

- [ ] **Step 4: Add failing search-loop tests**

    def test_rejects_infeasible_candidate(self):
        actions = {"bad": lambda x: ActionOutcome(x - 5, 1, False, 0.01)}
        r = adaptive_search(100.0, actions, float, lambda x: x >= 100,
                            max_steps=3, patience=1)
        self.assertEqual(r.solution, 100.0)
        self.assertEqual(r.termination_reason, "patience")
        self.assertFalse(r.trace[0].accepted)

    def test_stops_at_budget(self):
        actions = {"step": lambda x: ActionOutcome(x - 1, 1, True, 0.01)}
        r = adaptive_search(10.0, actions, float, lambda x: True,
                            max_steps=3, patience=4)
        self.assertEqual(len(r.trace), 3)
        self.assertEqual(r.termination_reason, "budget")

- [ ] **Step 5: Implement adaptive loop**

Record action, UCB score, objective before/after, reward, acceptance, moves, action and cumulative runtime, context, and termination. Accept only feasible strict improvements; update UCB with all observed rewards.

- [ ] **Step 6: Run GREEN test and commit**

Run the focused unittest, then commit the two files as `feat: add deterministic adaptive operator selector`.

---

### Task 2: Portfolio Solver and Independent Validation

**Files:**
- Create: `src/experiments/week6/portfolio_solver.py`
- Test: `src/experiments/week6/tests/test_portfolio_solver.py`

**Interfaces:**
- Consume Week 4 `greedy_solve`, `apply_two_opt`, `check_single_route`, `apply_profile`.
- Consume Week 5 `relocate_pass`, `swap_pass`, and Method D solver.
- Export `B_METHOD`, `D_METHOD`, `E_FIXED_METHOD`, `E_ADAPTIVE_METHOD`, ordered `METHODS`.
- Export `validate_routes(instance, routes) -> ValidationResult`.
- Export `solve_method(instance, method, adaptive_steps=12, patience=4) -> SolveResult`.

- [ ] **Step 1: Write failing validation tests**

On one generated 20-customer instance, assert a nearest solution validates; removing one customer reports `unserved customers`; duplicating one reports duplicates; and best-candidate selection ignores an infeasible shorter solution.

- [ ] **Step 2: Run RED portfolio test**

Run `python3 -m unittest src/experiments/week6/tests/test_portfolio_solver.py -v`; expect missing module.

- [ ] **Step 3: Implement independent validation**

Check depot anchors, each route with `check_single_route`, exact customer coverage, duplicates, fleet limit, and full distance. Never trust construction flags.

- [ ] **Step 4: Implement safe operator adapters**

Copy routes before action. Wrap one bounded 2-opt application, one relocate sweep, and one swap sweep. Measure runtime and validate the full candidate. Rejected candidates cannot mutate current state.

- [ ] **Step 5: Implement compatibility methods B and D**

B must match Week 5 nearest construction. D must call Week 5's existing solver. Test equal route tuples and objectives on a fixed instance.

- [ ] **Step 6: Implement E-fixed and E-adaptive**

Construct nearest and composite candidates, discard infeasible candidates, apply 2-opt warm start, then fixed inter-route optimization or `adaptive_search`. Return the shortest feasible final candidate plus diagnostics for both sources.

- [ ] **Step 7: Add feasibility and repeatability tests**

For all methods on baseline and small-battery 20-customer cases, validate feasible outputs; solve twice and compare routes, objective, source, action sequence, and termination.

- [ ] **Step 8: Run GREEN tests and commit**

Run focused tests and commit as `feat: combine week 6 construction and search methods`.

---

### Task 3: Controlled Experiment Runner and Schema

**Files:**
- Create: `src/experiments/week6/compare_week6_methods.py`
- Test: `src/experiments/week6/tests/test_compare_week6_methods.py`

**Interfaces:**
- `run_experiment(scales, profiles, instances_per_scale, base_seed, adaptive_steps, patience) -> ExperimentBundle`
- `aggregate_results`, `compare_results`, and `write_outputs`
- Outputs: `week6_results.json`, `week6_aggregate.csv`, `week6_comparison.csv`, `adaptive_trace.json`, `adaptive_trace.csv`, `week6_results.md`, `run_log.txt`

- [ ] **Step 1: Write failing aggregation and schema tests**

Use hand-built rows to assert feasibility rate, mean, median, standard deviation, best objective, runtime, and action counts. A temporary 1×1×1 smoke run must create all outputs and JSON keys `metadata`, `aggregate`, `comparisons`, `instances`, `diagnostics`, `adaptive_trace`.

- [ ] **Step 2: Run RED runner tests**

Run `python3 -m unittest src/experiments/week6/tests/test_compare_week6_methods.py -v`; expect missing module.

- [ ] **Step 3: Implement controlled loop and records**

Use existing scale-derived seeds. Run four methods on each identical profiled instance. Preserve routes, violations, source diagnostics, trace, runtime, and environment metadata.

- [ ] **Step 4: Implement aggregates and comparisons**

Aggregate by profile/scale/method. Compare E variants against B and D using feasibility delta, objective delta/percent, runtime delta, and wins/ties/losses on jointly feasible instances.

- [ ] **Step 5: Implement serializers**

Write stable-column CSV, pretty JSON, Markdown tables with diagnostics, and an exact-command environment log. Never output an infeasible objective as comparable.

- [ ] **Step 6: Run all tests and commit**

Run unittest discovery and commit as `feat: add week 6 controlled experiment runner`.

---

### Task 4: Reproducibility Checker

**Files:**
- Create: `src/experiments/week6/reproducibility_check.py`
- Test: `src/experiments/week6/tests/test_reproducibility_check.py`

**Interfaces:**
- `solution_signature(result) -> tuple` includes routes, rounded objective, source, action sequence, termination.
- CLI writes `reproducibility_report.json` and `.md`, exiting nonzero on mismatch.

- [ ] **Step 1: Write RED tests**

Equal results yield equal signatures; changing one action yields mismatch. Two repeats for four methods on one small instance must pass.

- [ ] **Step 2: Implement repeated checks**

Defaults: three scales, three profiles, three instances per cell, three repeats. Record exact mismatch signatures and pass counts.

- [ ] **Step 3: Run tests and commit**

Run focused tests and commit as `test: verify week 6 reproducibility`.

---

### Task 5: Visualization Generator

**Files:**
- Create: `src/experiments/week6/visualize_week6.py`
- Test: `src/experiments/week6/tests/test_visualize_week6.py`

**Interfaces:**
- Consume `results/week6_results.json` and recorded route/trace data.
- Produce six PNGs with stable `week6_` filenames.

- [ ] **Step 1: Write RED figure smoke test**

With a temporary minimal results JSON, call plot functions and assert each output has a PNG signature and exceeds 5 KB.

- [ ] **Step 2: Implement six figures**

Create `week6_workflow.png`, `week6_objective_feasibility.png`,
`week6_quality_runtime.png`, `week6_operator_heatmap.png`,
`week6_convergence.png`, and `week6_improvement_distribution.png`. Use
accessible colors, units, legends, and honest captions.

- [ ] **Step 3: Run tests and commit**

Run focused tests and commit as `feat: visualize week 6 integration results`.

---

### Task 6: Full Experiment and Evidence

**Files:**
- Generate: `src/experiments/week6/results/*`

- [ ] **Step 1: Run all tests**

Run `python3 -m unittest discover -s src/experiments/week6/tests -v`; require zero failures.

- [ ] **Step 2: Run full 432-run comparison**

    python3 src/experiments/week6/compare_week6_methods.py \
      --scales 20 50 100 \
      --profiles baseline tight_tw small_battery \
      --instances-per-scale 12 --seed 20260813 \
      --adaptive-steps 12 --patience 4

Require 108 rows per method and no uncaught error. Do not manually edit numbers.

- [ ] **Step 3: Run reproducibility matrix**

    python3 src/experiments/week6/reproducibility_check.py \
      --scales 20 50 100 --instances-per-scale 3 --repeats 3 \
      --profiles baseline tight_tw small_battery --seed 20260813

Require all route/objective/action signatures to match.

- [ ] **Step 4: Generate figures and audit schema**

Run the visualizer. Verify 432 instance rows, 36 aggregate rows, all methods per cell, nonnegative runtime, objectives only for feasible rows, declared trace actions only, and six decodable PNGs.

- [ ] **Step 5: Commit actual evidence**

Commit only `src/experiments/week6/results` as `results: add week 6 portfolio experiment evidence`.

---

### Task 7: Week 6 Research Documentation

**Files:**
- Create: `src/experiments/week6/README.md`
- Create: `docs/week6_integration.md`
- Create: `docs/week6_mdp_design.md`
- Modify: `docs/00_weekly.md`

- [ ] **Step 1: Calculate headline values from JSON**

Print feasibility, objective/runtime deltas, wins/ties/losses, action counts/rewards, and trace count through a read-only script. Use only these values in prose.

- [ ] **Step 2: Write Lab 6 integration note**

Include current stage, chosen tracks, pipeline, experiment plan and actual matrix, results, failure cases, limitations, learning usefulness, next step, figures, and exact reproduction commands.

- [ ] **Step 3: Write complete MDP note**

Define state feature names/ranges, actions, transition, reward, episode, terminal conditions, environment API mapping, data source, metrics, fixed/UCB baselines, data split, and go/no-go criteria for full RL.

- [ ] **Step 4: Write README and weekly entry**

Document code, outputs, commands, findings, and honest non-improvements. Add Week 6 as newest weekly entry; use `Not recorded` for attendance because no attendance fact was supplied.

- [ ] **Step 5: Verify and commit docs**

Check links, JSON-derived numbers, placeholder scan, and `git diff --check`; commit as `docs: publish week 6 integration and MDP design`.

---

### Task 8: Repository Integration and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `src/README.md`
- Modify: `src/results/LOCAL_RUNS.md`
- Modify: `src/results/research_visualizations.md`

- [ ] **Step 1: Add Week 6 navigation**

Update project status, tree, commands, local-run output list, and visualization index without rewriting unrelated history.

- [ ] **Step 2: Run complete verification**

    python3 -m unittest discover -s src/experiments/week6/tests -v
    python3 src/experiments/week6/reproducibility_check.py --scales 20 50 100 --instances-per-scale 3 --repeats 3 --profiles baseline tight_tw small_battery --seed 20260813
    python3 src/experiments/week6/visualize_week6.py
    git diff --check

Also validate links, JSON schema/counts, six PNGs, and exact scope.

- [ ] **Step 3: Inspect and commit indexes**

Review full diff/status and commit four index files as `docs: integrate week 6 research artifacts`.

- [ ] **Step 4: Final smoke, fetch, and push**

Run one small solve, fetch origin, verify fast-forward compatibility, push to `origin/main`, fetch again, and require `HEAD == origin/main`.
