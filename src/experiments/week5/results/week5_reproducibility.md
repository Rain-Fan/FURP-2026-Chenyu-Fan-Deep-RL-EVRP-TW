# Week 5 Reproducibility Check

Status: **PASS**

The aggregate CSV comparison excludes measured runtime columns because runtime varies with system load.

## Fixed Week 4 Configuration

`/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 /Users/rain/Desktop/EVRP-TW-Research/src/experiments/week4/compare_week4_methods.py --scales 20 50 100 --instances-per-scale 12 --seed 20260706 --profiles baseline tight_tw small_battery`

## Result

- All deterministic aggregate cells matched across both runs.
