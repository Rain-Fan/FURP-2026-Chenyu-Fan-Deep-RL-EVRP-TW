#!/usr/bin/env python3
"""Week 4 result visualizations (matplotlib).

Reads ``results/week4_results.json`` produced by ``compare_week4_methods.py``
and renders four figures that support the Week 4 report:

1. ``week4_feasibility_by_profile.png`` - feasibility rate per method across
   scales and stress profiles.
2. ``week4_objective_by_profile.png`` - mean feasible objective per method.
3. ``week4_two_opt_gain.png`` - distance recovered by the 2-opt local search.
4. ``week4_representative_routes.png`` - route geometry for Methods A, B, and C
   on the same instance, showing why the composite method is more compact.

All numbers come from the committed local run; nothing here re-solves the
problem except the route-geometry panel, which re-runs the three solvers on one
fixed instance so the drawn routes match the reported method behaviour.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend so the script runs without a display
import matplotlib.pyplot as plt

WEEK4_DIR = Path(__file__).resolve().parent
RESULTS_DIR = WEEK4_DIR / "results"
sys.path.insert(0, str(WEEK4_DIR))

# Consistent palette with the rest of the project: tested method red, baseline
# blue, week3 reference amber.
METHOD_STYLE = {
    "C_composite_score": {"label": "C: composite + 2-opt", "color": "#dc2626"},
    "A_due_time_priority": {"label": "A: due-time (week3)", "color": "#f59e0b"},
    "B_nearest_customer": {"label": "B: nearest (baseline)", "color": "#2563eb"},
}
PROFILE_LABEL = {
    "baseline": "Baseline",
    "tight_tw": "Tight time windows",
    "small_battery": "Small battery",
}
METHOD_ORDER = ["C_composite_score", "A_due_time_priority", "B_nearest_customer"]


def load_results() -> dict:
    path = RESULTS_DIR / "week4_results.json"
    if not path.exists():
        raise SystemExit(
            "week4_results.json not found. Run compare_week4_methods.py first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _grouped_metric_figure(
    aggregate: list[dict],
    metric: str,
    title: str,
    ylabel: str,
    outfile: str,
    fmt: str = "{:.2f}",
) -> None:
    """Draw one subplot per profile with grouped bars over scales and methods."""
    profiles = [p for p in PROFILE_LABEL if any(r["profile"] == p for r in aggregate)]
    scales = sorted({r["scale"] for r in aggregate})
    fig, axes = plt.subplots(1, len(profiles), figsize=(5.2 * len(profiles), 4.6), sharey=True)
    if len(profiles) == 1:
        axes = [axes]

    bar_width = 0.26
    for ax, profile in zip(axes, profiles):
        positions = range(len(scales))
        for offset, method in enumerate(METHOD_ORDER):
            values = []
            for scale in scales:
                row = next(
                    (r for r in aggregate if r["profile"] == profile
                     and r["scale"] == scale and r["method"] == method),
                    None,
                )
                value = row[metric] if row and row[metric] is not None else 0.0
                values.append(value)
            xs = [p + (offset - 1) * bar_width for p in positions]
            style = METHOD_STYLE[method]
            bars = ax.bar(xs, values, bar_width, label=style["label"], color=style["color"])
            for rect, value in zip(bars, values):
                if value > 0:
                    ax.text(
                        rect.get_x() + rect.get_width() / 2,
                        value,
                        fmt.format(value),
                        ha="center", va="bottom", fontsize=6.5,
                    )
        ax.set_title(PROFILE_LABEL[profile], fontsize=11)
        ax.set_xticks(list(positions))
        ax.set_xticklabels([f"n={s}" for s in scales])
        ax.set_xlabel("Instance scale")
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        ax.margins(y=0.12)
    axes[0].set_ylabel(ylabel)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.suptitle(title, fontsize=13, y=1.06)
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False,
               fontsize=9, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(RESULTS_DIR / outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_two_opt_gain(aggregate: list[dict]) -> None:
    """Bar chart of the mean distance recovered by 2-opt for Method C."""
    profiles = [p for p in PROFILE_LABEL if any(r["profile"] == p for r in aggregate)]
    scales = sorted({r["scale"] for r in aggregate})
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    bar_width = 0.26
    positions = range(len(scales))
    profile_colors = {"baseline": "#dc2626", "tight_tw": "#7c3aed", "small_battery": "#0891b2"}
    for offset, profile in enumerate(profiles):
        gains = []
        for scale in scales:
            row = next(
                (r for r in aggregate if r["profile"] == profile
                 and r["scale"] == scale and r["method"] == "C_composite_score"),
                None,
            )
            gains.append(row["mean_two_opt_gain"] if row else 0.0)
        xs = [p + (offset - 1) * bar_width for p in positions]
        bars = ax.bar(xs, gains, bar_width, label=PROFILE_LABEL[profile],
                      color=profile_colors.get(profile, "#64748b"))
        for rect, value in zip(bars, gains):
            ax.text(rect.get_x() + rect.get_width() / 2, value, f"{value:.1f}",
                    ha="center", va="bottom", fontsize=8)
    ax.set_title("2-opt local-search gain for Method C\n(mean distance removed per instance)", fontsize=12)
    ax.set_xticks(list(positions))
    ax.set_xticklabels([f"n={s}" for s in scales])
    ax.set_xlabel("Instance scale")
    ax.set_ylabel("Mean distance recovered")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "week4_two_opt_gain.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_representative_routes(scale: int = 50, seed_offset: int = 0) -> None:
    """Re-solve one fixed instance with each method and draw the routes.

    Re-running the solvers here (instead of reading stored routes) keeps the
    figure self-contained and guarantees the drawn geometry matches the exact
    method behaviour reported in the tables.
    """
    from compare_week4_methods import (
        DEFAULT_SEED, apply_profile, generate_instance, greedy_solve,
        apply_two_opt, COMPOSITE_METHOD, DUE_TIME_METHOD, NEAREST_METHOD,
    )

    seed = DEFAULT_SEED + scale * 1000 + seed_offset
    instance = apply_profile(generate_instance(scale, seed), "baseline")
    methods = [NEAREST_METHOD, DUE_TIME_METHOD, COMPOSITE_METHOD]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), sharex=True, sharey=True)
    for ax, method in zip(axes, methods):
        routes, _ = greedy_solve(instance, method)
        if method == COMPOSITE_METHOD:
            routes, _, _ = apply_two_opt(instance, routes)
        total = 0.0
        for route in routes:
            xs = [instance.node(n).x for n in route]
            ys = [instance.node(n).y for n in route]
            ax.plot(xs, ys, "-", color="#94a3b8", linewidth=0.9, zorder=1)
            for a, b in zip(route, route[1:]):
                na, nb = instance.node(a), instance.node(b)
                total += ((na.x - nb.x) ** 2 + (na.y - nb.y) ** 2) ** 0.5
        cx = [c.x for c in instance.customers]
        cy = [c.y for c in instance.customers]
        ax.scatter(cx, cy, s=18, color="#1e293b", zorder=3, label="customers")
        sx = [s.x for s in instance.stations]
        sy = [s.y for s in instance.stations]
        ax.scatter(sx, sy, s=70, marker="^", color="#16a34a", zorder=3, label="stations")
        ax.scatter([instance.depot.x], [instance.depot.y], s=140, marker="*",
                   color="#dc2626", zorder=4, label="depot")
        style = METHOD_STYLE[method]
        ax.set_title(f"{style['label']}\ndistance={total:.1f}, vehicles={len(routes)}", fontsize=10)
        ax.set_aspect("equal")
        ax.grid(linestyle=":", alpha=0.4)
    axes[0].legend(loc="upper right", fontsize=7, framealpha=0.9)
    fig.suptitle(f"Representative routes on one {scale}-customer EVRP-TW instance", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(RESULTS_DIR / "week4_representative_routes.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    data = load_results()
    aggregate = data["aggregate"]
    _grouped_metric_figure(
        aggregate, "feasibility_rate",
        "Feasibility rate by method, scale, and stress profile",
        "Feasibility rate", "week4_feasibility_by_profile.png", fmt="{:.2f}",
    )
    _grouped_metric_figure(
        aggregate, "mean_objective_feasible",
        "Mean feasible objective (route distance) by method",
        "Mean feasible distance", "week4_objective_by_profile.png", fmt="{:.0f}",
    )
    plot_two_opt_gain(aggregate)
    plot_representative_routes()
    print("Wrote figures to", RESULTS_DIR)


if __name__ == "__main__":
    main()
