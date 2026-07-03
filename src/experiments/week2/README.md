# Week 2: Official POMO and OR-Tools Reference Files

This folder is aligned around official upstream source files for the methods
studied in Week 2.  Project-written EVRP-TW comparison code is kept separately
under `project_adapters/`.

## Official POMO CVRP Source

`pomo_cvrp/` contains source files copied from:

https://github.com/yd-kwon/POMO/tree/master/NEW_py_ver/CVRP

| Local file | Upstream file |
|---|---|
| `pomo_cvrp/CVRProblemDef.py` | `NEW_py_ver/CVRP/CVRProblemDef.py` |
| `pomo_cvrp/CVRPEnv.py` | `NEW_py_ver/CVRP/POMO/CVRPEnv.py` |
| `pomo_cvrp/CVRPModel.py` | `NEW_py_ver/CVRP/POMO/CVRPModel.py` |
| `pomo_cvrp/CVRPTrainer.py` | `NEW_py_ver/CVRP/POMO/CVRPTrainer.py` |
| `pomo_cvrp/CVRPTester.py` | `NEW_py_ver/CVRP/POMO/CVRPTester.py` |
| `pomo_cvrp/train_n100.py` | `NEW_py_ver/CVRP/POMO/train_n100.py` |
| `pomo_cvrp/test_n100.py` | `NEW_py_ver/CVRP/POMO/test_n100.py` |
| `pomo_cvrp/utils/utils.py` | `NEW_py_ver/utils/utils.py` |

## Official OR-Tools Reference Samples

`or_tools/` contains official Google OR-Tools routing samples relevant to the
Week 2 comparison context:

- `vrp_capacity.py`
- `vrp_time_windows.py`
- `LICENSE`

Source:

https://github.com/google/or-tools/tree/stable/ortools/constraint_solver/samples

## Project Adapters

`project_adapters/` contains project-written EVRP-TW comparison files:

- `compare_week2_baselines.py`
- `evrp_tw_common.py`
- `genetic_algorithm.py`
- `or_tools_cvrptw.py`
- `pomo_style.py`

These files are retained because there is no exact official EVRP-TW comparison
script for this repository's synthetic setup.  They should be cited as project
adapters or simplified recreations, not as official algorithm source files.

## Existing Result Artifacts

The `results/` folder contains previously generated local comparison artifacts:

- `week2_results.json`
- `week2_results.csv`
- `week2_results.md`
