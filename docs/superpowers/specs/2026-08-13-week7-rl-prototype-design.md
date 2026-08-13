# Week 7 Reinforcement-Learning Prototype Design

## Status and positioning

This is a self-directed Week 7 research extension of the completed Week 6
Track B + lightweight Track C work.  It turns the documented operator-selection
MDP into a trainable reinforcement-learning prototype.  It is not presented as
a state-of-the-art EVRP-TW solver.  Its purpose is to test, reproducibly, whether
a small state-dependent policy adds value beyond fixed search and UCB1 on the
same local environment.

The implementation must preserve the project's feasibility-first rule: an
infeasible route is never treated as better because its distance is shorter.
Negative and inconclusive results are valid and must be reported.

## Research question

Can a small Double DQN learn a state-dependent choice among 2-opt, relocate,
and swap that improves held-out feasible route quality or search cost relative
to the Week 6 UCB1 selector, while using the same construction portfolio,
operator implementations, validation logic, step budget, and test instances?

## Compared methods

The held-out experiment compares four methods:

1. `D_composite_inter_route`: the Week 5 fixed single-source reference.
2. `E_fixed_portfolio`: the Week 6 two-source fixed-schedule portfolio.
3. `E_adaptive_portfolio`: the Week 6 UCB1 two-source portfolio.
4. `F_dqn_portfolio`: the Week 7 two-source portfolio controlled by a trained
   Double DQN.

Each portfolio constructs nearest and composite candidates, validates them,
applies the same feasibility-aware warm start, searches each feasible candidate,
and retains the shortest independently validated final solution.  DQN is not
allowed extra construction sources, operators, search steps, or evaluation
instances.

## MDP

### State

The environment emits a finite 12-dimensional `float64` vector after every
decision:

1. customer count divided by 100;
2. vehicle count divided by the fleet limit;
3. current objective divided by the warm-start objective;
4. cumulative relative improvement from the warm start;
5. step index divided by the step budget;
6. consecutive non-improving steps divided by patience;
7. last normalized reward, clipped to `[-1, 1]`;
8. cumulative acceptance rate;
9-11. one-hot encoding of the last action (all zero before the first action);
12. construction-source flag (`0` nearest, `1` composite).

The scale, progress, quality, recent outcome, action history, and source are
therefore observable without exposing seed identity or future operator results.

### Action

The discrete action set is ordered and fixed:

```text
0 = two_opt
1 = relocate
2 = swap
```

Each action applies one bounded, deterministic feasibility-aware operator pass
from the existing Week 4/5 code.

### Transition

The selected operator produces a candidate route set.  The existing independent
Week 6 validator checks depot anchoring, fleet size, exact customer coverage,
duplicates, capacity, time windows, battery, charging, and depot return.  A
strictly shorter feasible candidate becomes the next solution; otherwise the
current solution is retained and the non-improvement counter increases.

### Reward

For a feasible candidate, reward is the normalized distance reduction
`(before - after) / warm_start_objective`.  A feasible non-improving action
receives a small step penalty of `-0.001`; an infeasible transition receives
`-1.0`.  The denominator is fixed within an episode so rewards are comparable
across steps.  Only strict feasible improvements are accepted.

### Episode and terminal condition

One episode searches one warm-start candidate for one instance and construction
source.  It stops at the shared action budget (12 in the full experiment) or
after four consecutive non-improving actions.  Infeasible constructions do not
start an episode and remain explicit failure cases.

## Learning algorithm

The policy is a dependency-light Double DQN implemented with NumPy:

- MLP: 12 inputs, one 32-unit ReLU hidden layer, three linear Q outputs;
- replay buffer with deterministic seeded sampling;
- epsilon-greedy exploration with linear decay;
- Huber loss and Adam optimization;
- discount factor `0.95`;
- separate target network, synchronized at a fixed update interval;
- Double-DQN target: online network selects the next action and target network
  evaluates it;
- gradient norm clipping;
- `.npz` checkpoint containing weights, normalization-independent metadata,
  action order, dimensions, and training seed.

The code must support a tiny smoke configuration for tests and a full CLI
configuration for committed research results.

## Data split and experiment matrix

Training and evaluation use the existing deterministic synthetic EVRP-TW
generator but disjoint seed namespaces.  The full run uses all three profiles
(`baseline`, `tight_tw`, `small_battery`) and scales 20, 50, and 100.

- Training: 8 seeds per profile-scale cell, two portfolio sources where
  construction is feasible.
- Evaluation: 6 different seeds per profile-scale cell, four methods.
- Total held-out method-instance evaluations: `3 × 3 × 6 × 4 = 216`.
- Search budget: 12 decisions; patience: 4.
- Training/evaluation overlap is checked programmatically and must be zero.

The result metadata records the exact commands, Python/platform information,
NumPy version, training hyperparameters, seed ranges, counts, and wall-clock
runtime.

## Outputs

`src/experiments/week7/results/` contains only locally generated artifacts:

- `week7_results.json`: metadata, training history, aggregate rows, comparisons,
  per-instance routes, action traces, diagnostics, and split audit;
- `week7_aggregate.csv`, `week7_comparison.csv`, `week7_instances.csv`, and
  `week7_training_history.csv`;
- `week7_results.md`: commands, setup, tables, honest interpretation, at least
  three failure/limitation cases, and conclusion;
- `dqn_checkpoint.npz` plus a JSON checkpoint manifest;
- `reproducibility_report.json` and `.md`;
- `run_log.txt`;
- generated PNGs for training, held-out quality/feasibility, runtime trade-off,
  action selection, policy-state behavior, and representative routes.

Selected Week 7 SVG summaries are also generated into `src/results/` from the
committed JSON, following the Week 2-6 pattern.

## Error handling and validity rules

- Invalid state shape, action index, hyperparameter, or empty replay sample
  raises `ValueError` with a specific message.
- NaN or infinite states, rewards, objectives, Q values, gradients, or model
  parameters fail immediately.
- Checkpoint loading validates state dimension, action order, hidden dimension,
  and array shapes.
- Training and evaluation seed overlap is a hard error.
- Aggregate objective statistics include feasible rows only; feasibility and
  runtime include every attempted instance.
- Generated tables and figures read result files rather than duplicating
  experimental values in source code.

## Testing and reproducibility

Standard-library `unittest` tests cover environment state/transition/termination,
replay behavior, neural forward/training/checkpoint round-trip, Double-DQN
targets, smoke training, seed isolation, result schema, visualization smoke
generation, and deterministic policy evaluation.  Tests use real small local
instances and real operators where integration behavior matters.

The reproducibility command trains twice under a small fixed configuration and
compares model parameter hashes, action sequences, feasibility, routes, and
objectives.  It also evaluates the committed full checkpoint twice on a fixed
matrix.  Runtime values are reported but excluded from equality signatures.

## Repository integration

The implementation updates:

- `README.md` and `src/README.md`;
- `docs/00_weekly.md` with a Week 7 self-directed entry whose attendance is
  recorded as `Not recorded`;
- `docs/week7_rl_extension.md` with the research narrative and evidence;
- `src/results/LOCAL_RUNS.md`, the cross-week generator, and visualization index;
- `src/experiments/week7/` with code, tests, README, checkpoint, and results.

No meeting note is created because no Week 7 meeting facts were supplied.

## Acceptance criteria

The work is complete only when:

1. all Week 6 and Week 7 tests pass locally;
2. the full training/evaluation command finishes and writes every declared
   artifact;
3. train/evaluation seed overlap is zero;
4. every reported final route has been independently validated;
5. visualizations render successfully and contain data from the generated JSON;
6. the reproducibility command reports zero deterministic mismatches;
7. documentation matches measured outputs, including negative results;
8. regenerating figures is idempotent; and
9. the exact committed tree is verified after merge before push.
