#!/usr/bin/env python3
"""Week 5 reproducibility check (Track B consolidation).

The Week 5 lab asks: "Are the results reproducible with the same settings?"
This script answers that question with evidence instead of assertion.

For each (profile, scale, seed, method) it solves the same instance several
times and checks that the algorithmic output is identical every time: the route
list and the objective distance.  Runtime is expected to vary and is therefore
ignored.

If any instance produces different routes or a different objective across
repeats, the method is not deterministic and the check fails loudly.  A passing
run is written to ``results/reproducibility_report.md`` and
``results/reproducibility_report.json`` so the claim can be inspected later.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "week3"))
from compare_week3_baselines import distance, generate_instance  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_week5_methods import (  # noqa: E402
    METHODS,
    RESULTS_DIR,
    apply_profile,
    solve_method,
)

DEFAULT_SCALES = (20, 50, 100)
DEFAULT_INSTANCES_PER_SCALE = 5
DEFAULT_SEED = 20260713
DEFAULT_REPEATS = 3
PROFILES = ("baseline", "tight_tw", "small_battery")


def _route_distance(instance, route: list[int]) -> float:
    return sum(distance(instance.node(a), instance.node(b)) for a, b in zip(route, route[1:]))


def solve_signature(instance, method: str) -> tuple[tuple[tuple[int, ...], ...], float]:
    """Return a hashable fingerprint of a solution: routes and total distance."""
    routes, _two_opt, _inter, _gain = solve_method(instance, method)
    total = sum(_route_distance(instance, route) for route in routes)
    frozen = tuple(tuple(route) for route in routes)
    return frozen, round(total, 6)


def check_instance(profile: str, scale: int, seed: int, method: str, repeats: int) -> dict:
    """Solve one instance ``repeats`` times and compare the fingerprints."""
    instance = apply_profile(generate_instance(scale, seed), profile)
    signatures = [solve_signature(instance, method) for _ in range(repeats)]
    first_routes, first_distance = signatures[0]
    stable = all(sig == signatures[0] for sig in signatures)
    return {
        "profile": profile,
        "scale": scale,
        "seed": seed,
        "method": method,
        "repeats": repeats,
        "stable": stable,
        "objective_distance": first_distance,
        "vehicles": len(first_routes),
        "distinct_objectives": sorted({sig[1] for sig in signatures}),
    }


def run_check(scales, instances_per_scale, base_seed, repeats) -> list[dict]:
    records: list[dict] = []
    for profile in PROFILES:
        for scale in scales:
            for offset in range(instances_per_scale):
                seed = base_seed + scale * 1000 + offset
                for method in METHODS:
                    records.append(check_instance(profile, scale, seed, method, repeats))
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", nargs="+", type=int, default=list(DEFAULT_SCALES))
    parser.add_argument("--instances-per-scale", type=int, default=DEFAULT_INSTANCES_PER_SCALE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_started = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    records = run_check(args.scales, args.instances_per_scale, args.seed, args.repeats)
    total = len(records)
    stable = sum(1 for r in records if r["stable"])
    unstable = [r for r in records if not r["stable"]]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "run_started_local": run_started,
        "repeats_per_instance": args.repeats,
        "checks_total": total,
        "checks_stable": stable,
        "checks_unstable": len(unstable),
        "all_stable": not unstable,
        "unstable_examples": unstable[:10],
    }
    (RESULTS_DIR / "reproducibility_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Week 5 Reproducibility Check",
        "",
        f"Run started: `{run_started}`",
        "",
        f"Each instance was solved {args.repeats} times with the same settings; a "
        "check passes when the routes and objective distance are identical across "
        "all repeats (runtime is allowed to vary).",
        "",
        f"- Total checks: {total}",
        f"- Stable (identical across repeats): {stable}",
        f"- Unstable: {len(unstable)}",
        f"- All deterministic: {'yes' if not unstable else 'NO'}",
        "",
    ]
    if unstable:
        lines.append("## Unstable instances")
        lines.append("")
        for r in unstable[:10]:
            lines.append(
                f"- {r['method']} on {r['profile']} scale={r['scale']} seed={r['seed']}: "
                f"objectives {r['distinct_objectives']}"
            )
    else:
        lines.append(
            "All methods (D, C, B) produced identical solutions on every repeat, "
            "so the reported results are fully reproducible with a fixed seed."
        )
    (RESULTS_DIR / "reproducibility_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "checks_total": total,
        "checks_stable": stable,
        "all_stable": not unstable,
    }, indent=2))


if __name__ == "__main__":
    main()
