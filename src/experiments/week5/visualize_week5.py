#!/usr/bin/env python3
"""Week 5 result visualizations (matplotlib).

Reads ``results/week5_results.json`` produced by ``compare_week5_methods.py``
and renders four figures that support the Week 5 checkpoint:

1. ``week5_objective_by_profile.png`` - mean feasible objective per method
   across scales and stress profiles (the headline comparison).
2. ``week5_gap_vs_baseline.png`` - percentage objective gap of Methods C and D
   against baseline B; shows whether inter-route moves close the Week 4 gap.
3. ``week5_ls_gain.png`` - mean distance removed by local search, split into
   the 2-opt part (C) and the full 2-opt + inter-route part (D).
4. ``week5_representative_routes.png`` - route geometry for B, C, and D on the
   same 50-customer instance, showing where inter-route moves help.

All aggregate numbers come from the committed local run; only the route-geometry
panel re-solves one fixed instance so the drawn routes match the reported
behaviour.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend so the script runs without a display
import matplotlib.pyplot as plt

WEEK5_DIR = Path(__file__).resolve().parent
RESULTS_DIR = WEEK5_DIR / "results"
sys.path.insert(0, str(WEEK5_DIR))

# Tested method (D) red, Week 4 reference (C) amber, baseline (B) blue.
METHOD_STYLE = {
    "D_composite_inter_route": {"label": "D: + inter-route LS", "color": "#dc2626"},
    "C_composite_score": {"label": "C: composite + 2-opt", "color": "#f59e0b"},
    "B_nearest_customer": {"label": "B: nearest (baseline)", "color": "#2563eb"},
}
PROFILE_LABEL = {
    "baseline": "Baseline",
    "tight_tw": "Tight time windows",
    "small_battery": "Small battery",
}
METHOD_ORDER = ["D_composite_inter_route", "C_composite_score", "B_nearest_customer"]


def load_results() -> dict:
    path = RESULTS_DIR / "week5_results.json"
    if not path.exists():
        raise SystemExit(
            "week5_results.json not found. Run compare_week5_methods.py first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def plot_objective_by_profile(aggregate: list[dict]) -> None:
    """One subplot per profile; grouped bars of mean feasible objective."""
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
                values.append(row["mean_objective_feasible"] if row and row["mean_objective_feasible"] else 0.0)
            xs = [p + (offset - 1) * bar_width for p in positions]
            style = METHOD_STYLE[method]
            bars = ax.bar(xs, values, bar_width, label=style["label"], color=style["color"])
            for rect, value in zip(bars, values):
                if value > 0:
                    ax.text(rect.get_x() + rect.get_width() / 2, value, f"{value:.0f}",
                            ha="center", va="bottom", fontsize=6.5)
        ax.set_title(PROFILE_LABEL[profile], fontsize=11)
        ax.set_xticks(list(positions))
        ax.set_xticklabels([f"n={s}" for s in scales])
        ax.set_xlabel("Instance scale")
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        ax.margins(y=0.12)
    axes[0].set_ylabel("Mean feasible distance")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.suptitle("Week 5: mean feasible objective by method, scale, and profile", fontsize=13, y=1.06)
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False,
               fontsize=9, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(RESULTS_DIR / "week5_objective_by_profile.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_gap_vs_baseline(aggregate: list[dict]) -> None:
    """Percentage objective gap of C and D against baseline B (baseline profile).

    A negative gap means the method is shorter than B.  This is the figure that
    directly answers the Week 5 question: did inter-route moves close the Week 4
    medium-scale gap?
    """
    rows = [r for r in aggregate if r["profile"] == "baseline"]
    scales = sorted({r["scale"] for r in rows})

    def gap_pct(method: str, scale: int) -> float:
        m = next((r for r in rows if r["scale"] == scale and r["method"] == method), None)
        b = next((r for r in rows if r["scale"] == scale and r["method"] == "B_nearest_customer"), None)
        if not m or not b or not m["mean_objective_feasible"] or not b["mean_objective_feasible"]:
            return 0.0
        return 100.0 * (m["mean_objective_feasible"] - b["mean_objective_feasible"]) / b["mean_objective_feasible"]

    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    bar_width = 0.35
    positions = range(len(scales))
    for offset, method in enumerate(["C_composite_score", "D_composite_inter_route"]):
        gaps = [gap_pct(method, s) for s in scales]
        xs = [p + (offset - 0.5) * bar_width for p in positions]
        style = METHOD_STYLE[method]
        bars = ax.bar(xs, gaps, bar_width, label=style["label"], color=style["color"])
        for rect, value in zip(bars, gaps):
            va = "bottom" if value >= 0 else "top"
            ax.text(rect.get_x() + rect.get_width() / 2, value,
                    f"{value:+.1f}%", ha="center", va=va, fontsize=8)
    ax.axhline(0, color="#2563eb", linewidth=1.2, linestyle="--", label="B: baseline (0%)")
    ax.set_title("Objective gap vs nearest-customer baseline (baseline profile)\n"
                 "negative = shorter than baseline", fontsize=12)
    ax.set_xticks(list(positions))
    ax.set_xticklabels([f"n={s}" for s in scales])
    ax.set_xlabel("Instance scale")
    ax.set_ylabel("Objective gap vs B (%)")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "week5_gap_vs_baseline.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_ls_gain(aggregate: list[dict]) -> None:
    """Mean local-search distance gain for C (2-opt only) and D (2-opt + inter-route)."""
    profiles = [p for p in PROFILE_LABEL if any(r["profile"] == p for r in aggregate)]
    scales = sorted({r["scale"] for r in aggregate})
    fig, axes = plt.subplots(1, len(profiles), figsize=(5.2 * len(profiles), 4.4), sharey=True)
    if len(profiles) == 1:
        axes = [axes]
    bar_width = 0.35
    for ax, profile in zip(axes, profiles):
        positions = range(len(scales))
        for offset, method in enumerate(["C_composite_score", "D_composite_inter_route"]):
            gains = []
            for scale in scales:
                row = next(
                    (r for r in aggregate if r["profile"] == profile
                     and r["scale"] == scale and r["method"] == method),
                    None,
                )
                gains.append(row["mean_ls_gain"] if row else 0.0)
            xs = [p + (offset - 0.5) * bar_width for p in positions]
            style = METHOD_STYLE[method]
            bars = ax.bar(xs, gains, bar_width, label=style["label"], color=style["color"])
            for rect, value in zip(bars, gains):
                if value > 0:
                    ax.text(rect.get_x() + rect.get_width() / 2, value, f"{value:.0f}",
                            ha="center", va="bottom", fontsize=6.5)
        ax.set_title(PROFILE_LABEL[profile], fontsize=11)
        ax.set_xticks(list(positions))
        ax.set_xticklabels([f"n={s}" for s in scales])
        ax.set_xlabel("Instance scale")
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        ax.margins(y=0.12)
    axes[0].set_ylabel("Mean distance removed by local search")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.suptitle("Week 5: local-search gain (C = 2-opt only, D = 2-opt + inter-route)", fontsize=12.5, y=1.05)
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False,
               fontsize=9, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(RESULTS_DIR / "week5_ls_gain.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_representative_routes(scale: int = 50, seed_offset: int = 0) -> None:
    """Re-solve one fixed instance with B, C, and D and draw the routes."""
    from compare_week5_methods import (
        DEFAULT_SEED, apply_profile, solve_method,
        HYBRID_METHOD, COMPOSITE_METHOD, NEAREST_METHOD,
    )
    from compare_week3_baselines import generate_instance

    seed = DEFAULT_SEED + scale * 1000 + seed_offset
    instance = apply_profile(generate_instance(scale, seed), "baseline")
    methods = [NEAREST_METHOD, COMPOSITE_METHOD, HYBRID_METHOD]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), sharex=True, sharey=True)
    for ax, method in zip(axes, methods):
        routes, _t, _i, _g = solve_method(instance, method)
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
    fig.suptitle(f"Week 5 representative routes on one {scale}-customer instance", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(RESULTS_DIR / "week5_representative_routes.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    data = load_results()
    aggregate = data["aggregate"]
    plot_objective_by_profile(aggregate)
    plot_gap_vs_baseline(aggregate)
    plot_ls_gain(aggregate)
    plot_representative_routes()
    print("Wrote figures to", RESULTS_DIR)


if __name__ == "__main__":
    main()
