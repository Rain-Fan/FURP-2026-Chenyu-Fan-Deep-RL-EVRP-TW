# Official Algorithm Source Files

This directory stores upstream source files for algorithms used as references
in the experiment work.  Files in this directory should be treated as the
official algorithm code.  Project-written comparison scripts elsewhere in
`src/experiments` are wrappers, adapters, data generators, or reports; they are
not official algorithm implementations.

## OR-Tools Routing Samples

Source repository: `google/or-tools`

Reference: https://github.com/google/or-tools/tree/stable/ortools/constraint_solver/samples

License: Apache License 2.0, copied in `or_tools/LICENSE`.

| Local file | Upstream file | Experiment role |
|---|---|---|
| `or_tools/tsp.py` | `ortools/constraint_solver/samples/tsp.py` | Official TSP routing sample. |
| `or_tools/vrp.py` | `ortools/constraint_solver/samples/vrp.py` | Official VRP routing sample. |
| `or_tools/vrp_capacity.py` | `ortools/constraint_solver/samples/vrp_capacity.py` | Official CVRP-style capacity routing sample. |
| `or_tools/vrp_time_windows.py` | `ortools/constraint_solver/samples/vrp_time_windows.py` | Official VRPTW routing sample. |

## POMO CVRP Source

Source repository: `yd-kwon/POMO`

Reference: https://github.com/yd-kwon/POMO/tree/master/NEW_py_ver/CVRP

The upstream README states that the `OLD_ipynb_ver` files are the original
2020 paper code and the `NEW_py_ver` files are the newer Python-version code.
This repository keeps the CVRP/POMO Python-version files as official upstream
reference code.

| Local file | Upstream file |
|---|---|
| `pomo_cvrp/CVRProblemDef.py` | `NEW_py_ver/CVRP/CVRProblemDef.py` |
| `pomo_cvrp/CVRPEnv.py` | `NEW_py_ver/CVRP/POMO/CVRPEnv.py` |
| `pomo_cvrp/CVRPModel.py` | `NEW_py_ver/CVRP/POMO/CVRPModel.py` |
| `pomo_cvrp/CVRPTester.py` | `NEW_py_ver/CVRP/POMO/CVRPTester.py` |
| `pomo_cvrp/CVRPTrainer.py` | `NEW_py_ver/CVRP/POMO/CVRPTrainer.py` |
| `pomo_cvrp/train_n100.py` | `NEW_py_ver/CVRP/POMO/train_n100.py` |
| `pomo_cvrp/test_n100.py` | `NEW_py_ver/CVRP/POMO/test_n100.py` |
| `pomo_cvrp/utils/utils.py` | `NEW_py_ver/utils/utils.py` |
| `pomo_cvrp/UPSTREAM_README.md` | `README.md` |

## Important Provenance Rule

If a future experiment needs an algorithm implementation, first add the
official upstream source file here and record its source.  If no official
source exists, the method should be documented as a project-written adapter or
experimental baseline, not as official algorithm code.
