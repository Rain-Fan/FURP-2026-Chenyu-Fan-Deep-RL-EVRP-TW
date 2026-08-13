# Week 6 Integrated Heuristic and Adaptive Operator Selection Design

**Date:** 2026-08-13

**Project:** Deep RL for EVRP-TW

**Primary lab track:** Track B — combine existing methods

**Supporting lab track:** Track C — lightweight adaptive operator selection

## 1. Goal and Research Question

Week 6 will turn the separate construction and local-search methods from Weeks
3–5 into one inspectable workflow. The primary research question is:

> Does a portfolio that combines nearest-customer and composite-score
> construction with feasibility-aware local search produce better feasible
> EVRP-TW solutions than the Week 5 fixed Method D, and can a lightweight
> adaptive operator selector improve the quality/runtime trade-off over a fixed
> operator order?

The implementation must satisfy the Week 6 lab requirements: a clear method
pipeline, a concrete batch experiment, at least three scales or settings,
summary statistics rather than selected best cases, inspectable evidence, and
an explicit explanation of how learning could help.

## 2. Scope

The Week 6 work will:

- reuse the nearest-customer and composite-score constructors;
- reuse the independent EVRP-TW feasibility checker;
- reuse feasibility-aware 2-opt, relocate, and swap operators;
- add a portfolio workflow that constructs and improves multiple candidates;
- add a deterministic UCB1 operator-selection prototype;
- record learning-ready action traces;
- document a complete MDP formulation for a future RL policy;
- run controlled experiments and generate tables, logs, and figures;
- update repository-level weekly and reproduction documentation.

The Week 6 work will not claim that UCB1 is a complete RL solution. It is a
transparent adaptive baseline and data-generation step for a future
state-dependent policy. It will not add an unvalidated neural network or claim
novelty unsupported by ablation evidence.

## 3. Compared Methods

The experiment will compare four methods on identical instances:

1. **B — nearest-customer baseline.** The Week 3 nearest-customer constructor
   without Week 6 portfolio logic.
2. **D — Week 5 fixed hybrid.** Composite-score construction, 2-opt, then fixed
   relocate/swap inter-route search.
3. **E-fixed — fixed portfolio.** Build nearest and composite candidates,
   validate both, apply the same fixed local-search schedule to each feasible
   candidate, and retain the shortest feasible result.
4. **E-adaptive — adaptive portfolio.** Build the same two candidates, apply a
   2-opt warm start, then use UCB1 to choose among 2-opt, relocate, and swap;
   retain the shortest feasible result.

This comparison separates the value of the construction portfolio from the
value of adaptive action selection.

## 4. Method Architecture

```text
EVRP-TW instance
  |-- nearest-customer construction
  `-- composite-score construction
          |
          v
independent feasibility validation
          |
          v
2-opt warm start on each feasible candidate
          |
          +-- E-fixed: fixed relocate -> swap rounds
          `-- E-adaptive: UCB1 chooses 2-opt / relocate / swap
          |
          v
independent validation of every accepted state
          |
          v
shortest feasible candidate
          |
          v
evaluation table + action trace + figures
```

Each candidate remains isolated. An infeasible construction is recorded and is
not passed to improvement operators that cannot repair coverage failures. Every
accepted operator output is independently validated before it becomes the next
state. If every candidate is infeasible, the workflow returns the best
diagnostic record without presenting an objective as a valid solution.

## 5. Adaptive Operator Selection

### 5.1 Actions

The action set is:

- `two_opt`: one bounded feasibility-aware intra-route improvement pass;
- `relocate`: one inter-route relocation sweep;
- `swap`: one inter-route customer-swap sweep.

The existing operators will be wrapped, not rewritten. Each action produces a
new candidate solution, accepted move count, distance change, feasibility
status, and elapsed time.

### 5.2 UCB1 policy

Every action is tried once when the budget permits. Later choices maximize:

```text
mean normalized reward + exploration_weight * sqrt(log(total selections) / action selections)
```

Tie-breaking uses the declared action order so fixed inputs and seeds remain
reproducible. The policy is reset for each constructed candidate so results do
not depend on experiment ordering.

### 5.3 Reward and stopping

The primary reward is relative distance reduction:

```text
(distance_before - distance_after) / max(distance_before, epsilon)
```

An infeasible transition receives a fixed negative reward and is rejected. The
trace records runtime separately so the scientific report can show the
quality/runtime trade-off without hiding it inside a hand-tuned scalar. Search
stops when the action budget is exhausted or a configured number of consecutive
actions produces no accepted improvement.

### 5.4 Trace schema

Each action record contains:

- profile, scale, instance seed, construction source, and step;
- state features before the action;
- selected action and UCB score;
- objective before and after;
- normalized reward and accepted move count;
- feasibility before and after;
- action runtime and cumulative runtime;
- termination reason where applicable.

The trace will be exported as JSON and CSV for later RL/DL experiments.

## 6. Complete MDP Formulation

The future RL formulation will be documented separately with:

- **State:** instance scale; route count; current distance; feasibility and
  violation counts; time-window tightness; battery tightness; recent progress;
  iteration fraction; and per-operator usage and reward statistics.
- **Action:** apply 2-opt, relocate, swap, or stop.
- **Transition:** run the selected deterministic operator, validate the result,
  and update solution and operator statistics.
- **Reward:** feasible normalized objective improvement, an infeasibility
  penalty, and an optional small measured-time cost assessed in ablation.
- **Episode:** one improvement process beginning from a feasible constructed
  solution for one instance.
- **Terminal condition:** explicit stop action, action budget, consecutive
  no-improvement limit, or no valid candidate.

The UCB1 prototype is an action-value baseline without full state conditioning.
The recorded traces establish whether action effectiveness varies enough by
state and profile to justify a learned policy.

## 7. Experiment Design

### 7.1 Instance matrix

- Scales: 20, 50, and 100 customers.
- Profiles: `baseline`, `tight_tw`, and `small_battery`.
- Replicates: at least 12 generated instances per scale/profile cell.
- Randomness: fixed, recorded base seed and deterministic derived seeds.
- Total core cells: 108 instances per method, 432 method-instance runs for four
  methods.

### 7.2 Metrics

The experiment records:

- feasibility rate and violation count;
- mean, median, best, and standard deviation of feasible objective;
- mean and maximum runtime;
- vehicles used;
- improvement over the initial construction;
- improvement against B and D;
- action selections, accepted moves, reward, and operator runtime;
- variability and determinism under fixed seeds.

An improvement claim requires feasibility no worse than the reference and a
lower mean feasible objective in the relevant comparison cell. Runtime cost is
reported alongside quality. No claim will be based on one selected instance.

### 7.3 Expected failure cases

- A construction may strand customers under the small-battery profile.
- Portfolio search may improve robustness without reducing mean objective in
  every cell.
- UCB1 may spend extra runtime exploring operators and may not beat the fixed
  order on deterministic small instances.
- Inter-route neighborhoods may become expensive at 100 customers.

These outcomes will be recorded as results rather than removed from the report.

## 8. Outputs

### 8.1 Code and tests

`src/experiments/week6/` will contain reusable portfolio and selection modules,
a controlled experiment runner, a visualization script, tests, and a README
with exact reproduction commands.

### 8.2 Evidence files

`src/experiments/week6/results/` will contain full JSON results,
aggregate/comparison CSV tables, a Markdown report, an environment run log,
JSON/CSV adaptive traces, a reproducibility report, and figures.

### 8.3 Documentation

- `docs/week6_integration.md`: required integration note with current stage,
  method design, plan, actual results, limitations, and next step.
- `docs/week6_mdp_design.md`: complete MDP and learning-usefulness assessment.
- Updates to `docs/00_weekly.md`, the top-level README, `src/README.md`, local
  run instructions, and the result visualization index.

### 8.4 Visualizations

The implementation will generate at least:

1. a combined-workflow diagram;
2. objective and feasibility comparison panels;
3. an objective-versus-runtime trade-off plot;
4. an operator selection/reward heatmap;
5. adaptive-search convergence curves;
6. representative routes or an improvement-distribution plot when meaningful.

## 9. Verification Strategy

Automated tests will cover:

- UCB1 exploration, score calculation, and deterministic tie-breaking;
- normalized reward and infeasible-transition handling;
- no-improvement and budget stopping conditions;
- feasibility preservation after every accepted operator action;
- portfolio selection of the shortest feasible candidate;
- stable result and trace schemas;
- fixed-seed reproducibility on a small test matrix.

Completion requires fresh execution of the tests, the full Week 6 experiment,
the reproducibility check, the visualization generator, output-schema checks,
Markdown/link checks, and `git diff --check`. Generated claims in the report
must be recalculated from the committed result files.

## 10. Repository and Delivery Constraints

Only Week 6 files and directly related repository indexes will be staged.
Existing unrelated untracked files will remain untouched. All result claims
will come from locally executed code. After verification, the implementation
will be committed and pushed to the repository's `main` branch as requested.
