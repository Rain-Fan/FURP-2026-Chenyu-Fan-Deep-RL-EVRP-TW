# Week 7 Reinforcement-Learning Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, run, document, and publish a complete locally reproducible Double-DQN operator-selection prototype for the existing EVRP-TW portfolio.

**Architecture:** A focused Week 7 package reuses the Week 3 instance generator, Week 4 profile/warm-start logic, and Week 6 independent validator/operators. `rl_environment.py` owns the MDP, `dqn_agent.py` owns learning, `train_week7_rl.py` owns training/evaluation/export, and separate scripts own reproducibility and visualization.  Training and held-out evaluation seeds are disjoint and every route is independently validated.

**Tech Stack:** Python 3.14, NumPy (installed with Matplotlib 3.10.9), standard-library `unittest`, dataclasses, JSON/CSV/NPZ, and headless Matplotlib.

## Global Constraints

- Preserve the Week 6 action order exactly: `two_opt`, `relocate`, `swap`.
- Use a 12-value finite state and 12-step/4-patience full-run budget.
- Never aggregate objective values from infeasible rows.
- Full training uses 8 seeds per profile-scale cell; held-out evaluation uses 6 non-overlapping seeds per cell.
- Full evaluation compares D, E-fixed, E-adaptive/UCB1, and F-DQN on all three profiles and scales 20/50/100.
- All result prose and figures must read generated result files; no hand-entered experimental claims.
- Do not create a Week 7 meeting note because no meeting facts were supplied.

---

### Task 1: MDP environment

**Files:**
- Create: `src/experiments/week7/rl_environment.py`
- Create: `src/experiments/week7/tests/test_rl_environment.py`

**Interfaces:**
- Consumes: Week 4 `greedy_solve`, `apply_two_opt`; Week 6 `_operator_actions`, `raw_solution_distance`, `validate_routes`.
- Produces: `ACTIONS`, `Transition`, `EpisodeResult`, `build_warm_start(instance, source)`, and `OperatorSelectionEnv(instance, routes, source, max_steps, patience)` with `reset()`, `state`, and `step(action_index)`.

- [ ] **Step 1: Write failing environment tests**

```python
def test_state_is_finite_twelve_vector(self):
    env = self.make_env(scale=20)
    state = env.reset()
    self.assertEqual(state.shape, (12,))
    self.assertTrue(np.isfinite(state).all())

def test_invalid_action_is_rejected(self):
    with self.assertRaisesRegex(ValueError, "action index"):
        self.make_env().step(3)

def test_patience_terminates_non_improving_episode(self):
    env = OperatorSelectionEnv(..., max_steps=12, patience=1)
    transition = env.step(0)
    self.assertTrue(transition.done)
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `python3 -m unittest discover -s src/experiments/week7/tests -p 'test_rl_environment.py' -v`

Expected: import failure because `rl_environment.py` does not exist.

- [ ] **Step 3: Implement the environment**

Implement strict input checks, 12-value state encoding, normalized reward with
`-0.001` non-improvement and `-1.0` infeasibility penalties, strict feasible
acceptance, fixed action order, trace records, patience, and budget termination.

- [ ] **Step 4: Run the environment tests and Week 6 compatibility tests**

Run:

```bash
python3 -m unittest discover -s src/experiments/week7/tests -p 'test_rl_environment.py' -v
python3 -m unittest discover -s src/experiments/week6/tests -p 'test_*.py' -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/experiments/week7/rl_environment.py src/experiments/week7/tests/test_rl_environment.py
git commit -m "feat: add week 7 operator-selection MDP"
```

### Task 2: NumPy Double DQN

**Files:**
- Create: `src/experiments/week7/dqn_agent.py`
- Create: `src/experiments/week7/tests/test_dqn_agent.py`

**Interfaces:**
- Consumes: `(state, action, reward, next_state, done)` transitions from Task 1.
- Produces: `ReplayBuffer`, `QNetwork`, `DQNAgent.select_action`, `DQNAgent.observe`, `DQNAgent.train_step`, `DQNAgent.save`, and `DQNAgent.load`.

- [ ] **Step 1: Write failing learning tests**

```python
def test_training_reduces_huber_loss(self):
    agent = DQNAgent(state_dim=12, action_dim=3, seed=7)
    for _ in range(80):
        agent.observe(np.zeros(12), 1, 1.0, np.zeros(12), True)
    first = agent.train_step(batch_size=16)
    for _ in range(30):
        last = agent.train_step(batch_size=16)
    self.assertLess(last, first)

def test_checkpoint_round_trip_preserves_q_values(self):
    agent.save(path)
    loaded = DQNAgent.load(path)
    np.testing.assert_allclose(agent.q_values(state), loaded.q_values(state))
```

- [ ] **Step 2: Run and verify RED**

Run: `python3 -m unittest discover -s src/experiments/week7/tests -p 'test_dqn_agent.py' -v`

Expected: import failure because `dqn_agent.py` does not exist.

- [ ] **Step 3: Implement replay, network, Adam, and Double-DQN targets**

Use a 12→32 ReLU→3 MLP, Huber loss, deterministic replay sampling, Double-DQN
next-action selection, target synchronization, finite-value guards, gradient
clipping, and validated NPZ serialization.

- [ ] **Step 4: Run Task 2 and Task 1 tests**

Run: `python3 -m unittest discover -s src/experiments/week7/tests -p 'test_*.py' -v`

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/experiments/week7/dqn_agent.py src/experiments/week7/tests/test_dqn_agent.py
git commit -m "feat: implement numpy double dqn"
```

### Task 3: Training, held-out evaluation, and result exporters

**Files:**
- Create: `src/experiments/week7/train_week7_rl.py`
- Create: `src/experiments/week7/tests/test_train_week7_rl.py`

**Interfaces:**
- Consumes: Tasks 1-2 and Week 6 `solve_method` references.
- Produces: `TrainingConfig`, `train_agent`, `solve_dqn_portfolio`, `run_experiment`, `write_outputs`, and CLI arguments for scales/profiles/train/eval seeds/counts/search/hyperparameters.

- [ ] **Step 1: Write failing smoke and schema tests**

```python
def test_smoke_run_has_disjoint_splits_and_all_methods(self):
    bundle, agent = run_experiment(scales=[20], profiles=["baseline"],
        train_instances=1, eval_instances=1, train_seed=100, eval_seed=200,
        max_steps=3, patience=2, episodes=2)
    self.assertEqual(bundle.metadata["seed_overlap"], [])
    self.assertEqual({row.method for row in bundle.instances}, set(METHODS))

def test_overlapping_seed_namespaces_are_rejected(self):
    with self.assertRaisesRegex(ValueError, "overlap"):
        run_experiment(..., train_seed=100, eval_seed=100)
```

- [ ] **Step 2: Run and verify RED**

Run: `python3 -m unittest discover -s src/experiments/week7/tests -p 'test_train_week7_rl.py' -v`

Expected: import failure because the experiment runner does not exist.

- [ ] **Step 3: Implement training/evaluation**

Train online over shuffled deterministic instance/source episodes, update from
replay after a warm-up, decay epsilon linearly, and evaluate greedily. Reuse
Week 6 D/E-fixed/E-adaptive for references. Export metadata, training history,
aggregate/comparison/instance/action/diagnostic rows, model checkpoint, CSVs,
Markdown, JSON, manifest, and run log.

- [ ] **Step 4: Run tests and a smoke CLI**

Run:

```bash
python3 -m unittest discover -s src/experiments/week7/tests -p 'test_*.py' -v
python3 src/experiments/week7/train_week7_rl.py --scales 20 --profiles baseline --train-instances 1 --eval-instances 1 --epochs 1 --max-steps 3 --patience 2 --output-dir /tmp/week7-smoke
```

Expected: tests pass and every declared smoke artifact exists.

- [ ] **Step 5: Commit**

```bash
git add src/experiments/week7/train_week7_rl.py src/experiments/week7/tests/test_train_week7_rl.py
git commit -m "feat: add week 7 dqn training and evaluation"
```

### Task 4: Reproducibility and visualizations

**Files:**
- Create: `src/experiments/week7/reproducibility_check.py`
- Create: `src/experiments/week7/visualize_week7.py`
- Create: `src/experiments/week7/tests/test_reproducibility_check.py`
- Create: `src/experiments/week7/tests/test_visualize_week7.py`

**Interfaces:**
- Consumes: full Week 7 bundle/checkpoint from Task 3.
- Produces: `result_signature`, `run_reproducibility_check`, `FIGURE_NAMES`, and `generate_all(payload, output_dir)`.

- [ ] **Step 1: Write failing determinism and figure tests**

```python
def test_two_fixed_runs_have_identical_signatures(self):
    report = run_reproducibility_check(smoke_config)
    self.assertEqual(report["mismatch_count"], 0)

def test_all_figures_are_nonempty_pngs(self):
    generate_all(payload, output_dir)
    self.assertEqual({p.name for p in output_dir.iterdir()}, set(FIGURE_NAMES))
    self.assertTrue(all(p.stat().st_size > 5000 for p in output_dir.iterdir()))
```

- [ ] **Step 2: Run and verify RED**

Run: `python3 -m unittest discover -s src/experiments/week7/tests -p 'test_reproducibility_check.py' -v && python3 -m unittest discover -s src/experiments/week7/tests -p 'test_visualize_week7.py' -v`

Expected: import failures for both missing scripts.

- [ ] **Step 3: Implement reproducibility and six headless figures**

Generate training return/loss, held-out objective/feasibility, quality-runtime,
action frequencies, policy-state heatmap, and representative route figures.
Reproducibility signatures exclude runtime/timestamps but include model hashes,
routes, objectives, feasibility, and action sequences.

- [ ] **Step 4: Run all Week 7 tests**

Run: `python3 -m unittest discover -s src/experiments/week7/tests -p 'test_*.py' -v`

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/experiments/week7/reproducibility_check.py src/experiments/week7/visualize_week7.py src/experiments/week7/tests
git commit -m "test: add week 7 reproducibility and figures"
```

### Task 5: Full local experiment and measured artifacts

**Files:**
- Create: `src/experiments/week7/results/*`

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: the complete local evidence package defined by the design spec.

- [ ] **Step 1: Run the full training and held-out evaluation**

Run:

```bash
python3 src/experiments/week7/train_week7_rl.py \
  --scales 20 50 100 --profiles baseline tight_tw small_battery \
  --train-instances 8 --eval-instances 6 \
  --train-seed 20270013 --eval-seed 20280013 \
  --epochs 3 --max-steps 12 --patience 4 \
  --hidden-dim 32 --batch-size 32 --replay-capacity 5000 \
  --learning-rate 0.001 --gamma 0.95 --target-sync 100 \
  --agent-seed 20260813
```

Expected: 216 held-out method-instance rows, zero seed overlap, nonempty model,
trace, aggregate, comparison, diagnostic, Markdown, CSV, JSON, and log artifacts.

- [ ] **Step 2: Generate figures**

Run: `python3 src/experiments/week7/visualize_week7.py`

Expected: every `FIGURE_NAMES` PNG exists and exceeds 5 KB.

- [ ] **Step 3: Run reproducibility checks**

Run: `python3 src/experiments/week7/reproducibility_check.py`

Expected: zero deterministic mismatches.

- [ ] **Step 4: Cross-check measured claims**

Read `week7_results.json` and assert the documented run counts, split audit,
route feasibility, objective deltas, action counts, and checkpoint hash.  Write
no claim that cannot be derived from this readback.

- [ ] **Step 5: Commit generated evidence**

```bash
git add src/experiments/week7/results
git commit -m "results: add local week 7 dqn evidence"
```

### Task 6: Documentation and cross-week integration

**Files:**
- Create: `src/experiments/week7/README.md`
- Create: `docs/week7_rl_extension.md`
- Modify: `docs/00_weekly.md`
- Modify: `README.md`
- Modify: `src/README.md`
- Modify: `src/results/LOCAL_RUNS.md`
- Modify: `src/results/generate_research_visualizations.py`
- Modify: `src/results/research_visualizations.md`
- Modify: `src/results/test_generate_research_visualizations.py`
- Create: `src/results/week7_*.svg`

**Interfaces:**
- Consumes: measured Task 5 JSON and figures.
- Produces: reproducible instructions, honest research narrative, Week 7 weekly entry, and selected cross-week SVGs.

- [ ] **Step 1: Extend the cross-week test and verify RED**

Add expectations for Week 7 SVG names and literal values independently read
from the committed JSON. Run:

```bash
python3 -m unittest discover -s src/results -p 'test_*.py' -v
```

Expected: fail because Week 7 generation is missing.

- [ ] **Step 2: Implement Week 7 cross-week SVG generation**

Add dependency-free SVG summaries for held-out performance, training curve,
and representative routes; extend the generated Markdown headline table.

- [ ] **Step 3: Write documentation from measured files**

Document exact commands, dataset split, architecture, results, trade-offs,
failure cases, reproducibility, scope limits, and next experiment. Add the Week
7 entry at the top of `docs/00_weekly.md` with attendance `Not recorded` and do
not create a meeting note.

- [ ] **Step 4: Verify documentation links and generators**

Run:

```bash
python3 src/results/generate_research_visualizations.py
python3 -m unittest discover -s src/results -p 'test_*.py' -v
git diff --check
```

Expected: generators pass and a second generation causes no diff.

- [ ] **Step 5: Commit integration**

```bash
git add README.md docs/00_weekly.md docs/week7_rl_extension.md src/README.md src/experiments/week7/README.md src/results
git commit -m "docs: integrate week 7 rl extension"
```

### Task 7: Final verification and publication

**Files:** No new files.

**Interfaces:** Verifies and publishes Tasks 1-6.

- [ ] **Step 1: Run fresh complete verification**

```bash
python3 -m unittest discover -s src/experiments/week6/tests -p 'test_*.py' -v
python3 -m unittest discover -s src/experiments/week7/tests -p 'test_*.py' -v
python3 -m unittest discover -s src/results -p 'test_*.py' -v
python3 -m py_compile src/experiments/week7/*.py src/results/*.py
xmllint --noout src/results/week7_*.svg
git diff --check
```

- [ ] **Step 2: Render and inspect every Week 7 PNG/SVG**

Use local rendering to check titles, axes, legends, clipping, route panels, and
that values match JSON readback.

- [ ] **Step 3: Review repository scope**

Confirm only Week 7 and explicitly required cross-week files changed; confirm
no existing untracked user files are staged.

- [ ] **Step 4: Merge to `main`, rerun tests, and push**

Fast-forward the feature branch into up-to-date `main`, repeat the tests from
Step 1 on the merged tree, then `git push origin main` only if all pass.

- [ ] **Step 5: Confirm remote equality**

Run `git rev-parse HEAD` and `git rev-parse origin/main`; they must match.
