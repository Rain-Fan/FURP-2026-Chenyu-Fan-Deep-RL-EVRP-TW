# EVRP-TW DeepRL

An end-to-end research baseline for solving the Electric Vehicle Routing
Problem with Time Windows (EVRP-TW) using attention-based reinforcement
learning.

The repository includes:

- a batched PyTorch EVRP-TW environment;
- capacity, time-window, battery, charging, and fleet constraints;
- dynamic feasibility masks;
- a deterministic greedy baseline;
- Transformer node encoding and pointer-style decoding;
- REINFORCE with a self-critical greedy baseline;
- PPO with clipped policy updates and a value head;
- training, evaluation, checkpointing, metrics, and route visualisation;
- unit and integration tests.

This is a reproducible research baseline, not a claim of state-of-the-art
performance.

## Problem Model

Each instance contains one depot, customer nodes, charging stations, and a
homogeneous electric fleet. A solution must:

1. serve every customer exactly once;
2. respect vehicle capacity;
3. start service inside each customer's time window;
4. keep battery energy non-negative;
5. preserve enough energy after customer service to reach a depot or station;
6. use no more than the available number of vehicles;
7. finish each route at the depot.

Returning to the depot starts a new vehicle route and resets load, battery, and
route time. Visiting a charging station restores the battery to full and adds
charging time.

## Installation

### Conda

```bash
conda env create -f environment.yml
conda activate evrp-tw-deeprl
```

### Python virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Apple Silicon automatically uses MPS when available. CUDA is selected first on
supported Linux systems, otherwise execution falls back to CPU.

## Quick Start

Run the greedy baseline:

```bash
python scripts/evaluate.py \
  --config experiments/configs/baseline.yaml
```

Train with REINFORCE:

```bash
python scripts/train.py \
  --config experiments/configs/reinforce.yaml
```

Train with PPO:

```bash
python scripts/train.py \
  --config experiments/configs/ppo.yaml
```

Evaluate a checkpoint:

```bash
python scripts/evaluate.py \
  --config experiments/configs/reinforce.yaml \
  --checkpoint experiments/results/reinforce/model_final.pt
```

Visualise a route:

```bash
python scripts/visualize_routes.py \
  --config experiments/configs/reinforce.yaml \
  --checkpoint experiments/results/reinforce/model_final.pt \
  --output figures/learned_route.png
```

Run the two-iteration execution check:

```bash
python scripts/train.py --config experiments/configs/smoke.yaml
```

## Tests

```bash
pytest -q
```

The tests cover deterministic data generation, dataset persistence, capacity
and battery masks, charging transitions, model output masks, the greedy
baseline, and one optimisation step for both REINFORCE and PPO.

## Configuration

Experiment YAML files control:

- problem size and number of charging stations;
- fleet capacity, battery, energy, speed, and charging rate;
- customer demand and time-window generation;
- neural-network size;
- optimiser and algorithm hyperparameters;
- batch size, iterations, checkpoints, and output paths.

Generated training instances use separate deterministic seeds at every
iteration. Evaluation uses a fixed seed for fair comparisons.

## Outputs

Training writes:

```text
model_final.pt
checkpoint_<iteration>.pt
history.json
training_curve.png
```

Evaluation writes `evaluation.json`. Generated experiment outputs and model
weights are ignored by Git.

## Repository Structure

```text
src/env/          EVRP-TW state transitions and feasibility masks
src/models/       Transformer encoder, pointer decoder, policy/value network
src/algorithms/   greedy baseline, REINFORCE, and PPO
src/utils/        data, configuration, metrics, and plotting
scripts/          training, evaluation, and visualisation commands
experiments/      YAML configurations and generated results
tests/            automated validation
docs/             research proposal, notes, and experiment plan
```

## Research Limitations

The current model assumes homogeneous vehicles, Euclidean travel, deterministic
speed, linear energy use, and full linear recharging. It does not yet implement
partial charging, nonlinear charging curves, stochastic travel times, load-
dependent energy, heterogeneous fleets, or public Schneider/Solomon loaders.

Objective comparisons should only be made among feasible solutions. Short
smoke-training runs verify execution but are not meaningful performance
experiments.
