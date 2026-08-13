# Week 6 MDP Design: State-Dependent EVRP-TW Operator Selection

## Purpose and Boundary

The current UCB1 prototype chooses among existing deterministic operators using
only their reward history in the current episode. A future RL policy would add
state context. The learning task is **operator selection for improving an
already feasible EVRP-TW solution**, not end-to-end customer routing. This
narrow boundary keeps the environment simulatable with the committed code and
provides strong fixed-rule baselines.

## MDP Definition

### State

At decision step `t`, use a fixed-length normalized feature vector:

| Feature | Definition / range |
|---|---|
| scale | customers / 100 |
| route ratio | routes used / maximum vehicles |
| distance ratio | current distance / initial feasible distance |
| progress | step / action budget |
| no-improvement ratio | consecutive failures / patience |
| TW tightness | mean customer window width / baseline width |
| battery tightness | battery capacity / baseline capacity |
| charge density | station visits / routes |
| recent reward | most recent normalized improvement |
| per-action pulls | three counts / action budget |
| per-action mean reward | three running means |
| per-action accepted rate | three accepted / selected ratios |

Feasibility and violation counts remain in the state API even though accepted
states should have zero violations. They allow a later repair action extension
without changing the interface.

### Actions

1. `two_opt`: bounded feasibility-aware intra-route improvement.
2. `relocate`: one inter-route or-opt-1 sweep.
3. `swap`: one inter-route customer-swap sweep.
4. `stop`: terminate when expected improvement is lower than search cost.

Every operator already exists and has a clear deterministic transition, so the
action meanings are concrete and comparable with fixed rules.

### Transition

The environment copies the current routes, executes one action, independently
checks route anchors, coverage, duplicates, fleet use, capacity, time windows,
battery and charging, and either accepts a strict feasible improvement or keeps
the prior state. It then updates action history and step counters.

### Reward

The primary reward is:

```text
r_t = (distance_before - distance_after) / distance_before
```

An infeasible proposal receives `-1` and is rejected. A later cost-aware
ablation may use `r_t - lambda * runtime_t / runtime_budget`, but the current
trace stores runtime separately to avoid choosing `lambda` after seeing test
results. The terminal reward is zero; quality improvement is already dense.

### Episode and Terminal Conditions

An episode begins from one feasible nearest or composite candidate after the
2-opt warm start. It ends on a `stop` action, 12-action budget, four consecutive
non-improving actions, or loss of any valid candidate. One problem instance can
produce two episodes, one per construction source.

## Environment Mapping

| MDP element | Current code |
|---|---|
| reset / initial state | `portfolio_solver._build_portfolio_candidate` |
| action execution | `portfolio_solver._operator_actions` |
| feasibility oracle | `portfolio_solver.validate_routes` |
| current UCB1 baseline | `adaptive_selector.UCB1Policy` |
| episode loop | `adaptive_selector.adaptive_search` |
| trace dataset | `results/adaptive_trace.json` and `.csv` |

The environment is deterministic for a fixed instance and action sequence.
Stochasticity for training must therefore come from sampling instances and
profiles, not hidden transition noise.

## Data and Evaluation Protocol

The Week 6 run supplies 2,364 transitions from 108 generated instances. Split
by **instance seed**, never by transition, to avoid leakage:

- 70% training seeds;
- 15% validation seeds for policy selection and early stopping;
- 15% held-out test seeds used once for final comparison.

Future Schneider instances must form a separate out-of-distribution test set.
Report feasibility rate, mean/median feasible distance, runtime, improvement
from the warm start, action count, and wins/ties/losses. Compare against:

- fixed `2-opt → relocate → swap`;
- best single operator;
- deterministic UCB1;
- an oracle that evaluates all three actions and chooses the best immediate
  feasible improvement (quality upper bound, not deployable baseline).

## Candidate Learning Models

A contextual bandit or small MLP policy is the first justified model because
the action set and state vector are small. A sequential Q-learning method is
only justified if action order creates measurable long-horizon effects. A GNN
or Transformer is unnecessary until the state includes customer/route graphs
and the compact feature baseline has been exhausted.

## Go / No-Go Criteria for Full RL

Proceed only if all are true on validation seeds:

1. The immediate best action varies with state; one action is not dominant in
   nearly every state.
2. A simple supervised/contextual predictor beats majority-action accuracy and
   deterministic UCB1 on held-out decisions.
3. The learned policy improves held-out distance or runtime without reducing
   feasibility.
4. The gain remains after accounting for model-inference and training cost.
5. There are enough independent instance seeds; transition count alone is not
   treated as sample size.

Otherwise retain E-fixed or E-adaptive as the final method and present RL as a
well-motivated future extension. Week 6 evidence already shows this is a real
possibility: relocate has the highest mean reward, while E-adaptive trails the
exhaustive fixed portfolio in five of nine aggregate cells.

## Risks and Controls

- **Reward hacking:** every accepted solution passes the independent validator.
- **Data leakage:** split by seed and keep profiles represented in every split.
- **Runtime bias:** record operator runtime and compare wall-clock budgets.
- **Overclaiming:** UCB1 is labelled adaptive selection, not RL.
- **Synthetic-only evidence:** use Schneider benchmarks before external claims.
- **Non-reproducibility:** fixed seeds and signatures cover routes, objectives,
  actions, acceptances, and termination; Week 6 reports 108/108 checks passed.
