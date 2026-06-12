# `/src` - Deep RL for EVRP-TW

> **Deep Reinforcement Learning for the Electric Vehicle Routing Problem with
> Time Windows**

## Directory Structure

```text
/src
  README.md
  data/                  Shared dataset notes or links
  experiments/deep_rl/   Reproducible implementation and experiment package
  results/               Selected figures and compact result summaries
```

The Deep RL experiment package contains:

```text
src/                     Environment, models, algorithms, and utilities
scripts/                 Training, evaluation, and route visualisation
experiments/configs/     Greedy, REINFORCE, PPO, and smoke configurations
tests/                   Unit and integration tests
notebooks/               Research and demonstration notebooks
docs/                    Proposal, paper notes, and experiment plan
```

## Getting Started

```bash
cd src/experiments/deep_rl
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python scripts/evaluate.py --config experiments/configs/baseline.yaml
python scripts/train.py --config experiments/configs/smoke.yaml
```

Conda users can instead create the environment from `environment.yml`.

## Notes

- Generated checkpoints, logs, and large datasets are excluded from Git.
- Objective values should only be compared for feasible solutions.
- Exact seeds and YAML configurations should be retained with every result.

---

_Project by Chenyu Fan · UNNC FURP 2026_
