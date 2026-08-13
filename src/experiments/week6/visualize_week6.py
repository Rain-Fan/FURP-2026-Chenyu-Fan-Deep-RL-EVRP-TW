#!/usr/bin/env python3
"""Generate Week 6 integration and adaptive-search figures."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
FIGURE_NAMES = (
    "week6_workflow.png",
    "week6_objective_feasibility.png",
    "week6_quality_runtime.png",
    "week6_operator_heatmap.png",
    "week6_convergence.png",
    "week6_improvement_distribution.png",
)

METHOD_ORDER = (
    "B_nearest_customer",
    "D_composite_inter_route",
    "E_fixed_portfolio",
    "E_adaptive_portfolio",
)
STYLE = {
    "B_nearest_customer": ("B: nearest", "#4C78A8"),
    "D_composite_inter_route": ("D: fixed hybrid", "#F58518"),
    "E_fixed_portfolio": ("E-fixed: portfolio", "#54A24B"),
    "E_adaptive_portfolio": ("E-adaptive: UCB1", "#B279A2"),
}
PROFILE_ORDER = ("baseline", "tight_tw", "small_battery")
ACTION_ORDER = ("two_opt", "relocate", "swap")


def _save(fig, path: Path) -> None:
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_workflow(output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")
    boxes = [
        (0.4, 2.8, 1.7, 1.0, "EVRP-TW\ninstance", "#E8F1FA"),
        (2.8, 4.5, 2.0, 1.0, "Nearest\nconstruction", "#DCEAF7"),
        (2.8, 1.3, 2.0, 1.0, "Composite\nconstruction", "#FCE8D5"),
        (5.4, 2.8, 1.8, 1.0, "Independent\nvalidation", "#F2F2F2"),
        (7.8, 4.5, 1.8, 1.0, "Fixed order\n2-opt → relocate/swap", "#DDF0D8"),
        (7.8, 1.3, 1.8, 1.0, "Adaptive UCB1\nselects operator", "#EADCF0"),
        (10.2, 2.8, 1.5, 1.0, "Best feasible\nsolution", "#D9EFEA"),
    ]
    for x, y, width, height, label, color in boxes:
        patch = plt.Rectangle((x, y), width, height, facecolor=color, edgecolor="#334155", linewidth=1.4)
        ax.add_patch(patch)
        ax.text(x + width / 2, y + height / 2, label, ha="center", va="center", fontsize=10)
    arrows = [
        ((2.1, 3.3), (2.8, 5.0)), ((2.1, 3.3), (2.8, 1.8)),
        ((4.8, 5.0), (5.4, 3.5)), ((4.8, 1.8), (5.4, 3.1)),
        ((7.2, 3.5), (7.8, 5.0)), ((7.2, 3.1), (7.8, 1.8)),
        ((9.6, 5.0), (10.2, 3.5)), ((9.6, 1.8), (10.2, 3.1)),
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "color": "#475569", "lw": 1.5})
    ax.text(6, 6.35, "Week 6 integrated EVRP-TW workflow", ha="center", fontsize=15, weight="bold")
    ax.text(6, 0.45, "Every accepted state is independently revalidated; infeasible candidates are not compared by objective.", ha="center", fontsize=9, color="#475569")
    _save(fig, output_dir / "week6_workflow.png")


def plot_objective_feasibility(payload: dict, output_dir: Path) -> None:
    rows = payload["aggregate"]
    profiles = [p for p in PROFILE_ORDER if any(r["profile"] == p for r in rows)]
    scales = sorted({int(r["scale"]) for r in rows})
    cells = [(p, s) for p in profiles for s in scales]
    x = np.arange(len(cells))
    width = 0.19
    fig, (ax_obj, ax_feas) = plt.subplots(2, 1, figsize=(max(9, len(cells) * 1.25), 8.2), sharex=True)
    for index, method in enumerate(METHOD_ORDER):
        label, color = STYLE[method]
        objectives, rates = [], []
        for profile, scale in cells:
            row = next((r for r in rows if r["profile"] == profile and int(r["scale"]) == scale and r["method"] == method), None)
            objectives.append(np.nan if row is None or row["mean_objective_feasible"] is None else row["mean_objective_feasible"])
            rates.append(0.0 if row is None else 100.0 * row["feasibility_rate"])
        position = x + (index - 1.5) * width
        ax_obj.bar(position, objectives, width, label=label, color=color)
        ax_feas.bar(position, rates, width, color=color)
    ax_obj.set_ylabel("Mean feasible distance")
    ax_obj.set_title("Solution quality (only independently feasible solutions)")
    ax_obj.grid(axis="y", linestyle=":", alpha=0.4)
    ax_obj.legend(ncol=2, fontsize=8)
    ax_feas.set_ylabel("Feasibility rate (%)")
    ax_feas.set_ylim(0, 108)
    ax_feas.axhline(100, color="#64748b", linewidth=0.8, linestyle="--")
    ax_feas.grid(axis="y", linestyle=":", alpha=0.4)
    ax_feas.set_xticks(x, [f"{profile}\nn={scale}" for profile, scale in cells], rotation=0)
    fig.suptitle("Week 6 objective and feasibility comparison", fontsize=14)
    fig.tight_layout()
    _save(fig, output_dir / "week6_objective_feasibility.png")


def plot_quality_runtime(payload: dict, output_dir: Path) -> None:
    rows = payload["aggregate"]
    fig, ax = plt.subplots(figsize=(9.2, 6.3))
    for method in METHOD_ORDER:
        label, color = STYLE[method]
        subset = [r for r in rows if r["method"] == method and r["mean_objective_feasible"] is not None]
        ax.scatter(
            [max(r["mean_runtime_sec"], 1e-7) for r in subset],
            [r["mean_objective_feasible"] for r in subset],
            s=[45 + int(r["scale"]) * 0.8 for r in subset],
            color=color,
            alpha=0.82,
            edgecolor="white",
            linewidth=0.7,
            label=label,
        )
    ax.set_xscale("log")
    ax.set_xlabel("Mean runtime per instance (seconds, log scale)")
    ax.set_ylabel("Mean feasible distance (lower is better)")
    ax.set_title("Quality–runtime trade-off across profiles and scales")
    ax.grid(linestyle=":", alpha=0.45)
    ax.legend(fontsize=9)
    _save(fig, output_dir / "week6_quality_runtime.png")


def plot_operator_heatmap(payload: dict, output_dir: Path) -> None:
    trace = payload["adaptive_trace"]
    profiles = [p for p in PROFILE_ORDER if any(r.get("profile") == p for r in trace)] or ["baseline"]
    counts = np.zeros((len(profiles), len(ACTION_ORDER)))
    rewards = np.zeros_like(counts)
    for i, profile in enumerate(profiles):
        for j, action in enumerate(ACTION_ORDER):
            rows = [r for r in trace if r.get("profile") == profile and r["action"] == action]
            counts[i, j] = len(rows)
            rewards[i, j] = np.mean([r["reward"] for r in rows]) if rows else 0.0
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8))
    for ax, matrix, title, cmap, fmt in (
        (axes[0], counts, "Action selections", "Blues", ".0f"),
        (axes[1], rewards, "Mean normalized reward", "RdYlGn", ".4f"),
    ):
        image = ax.imshow(matrix, aspect="auto", cmap=cmap)
        ax.set_xticks(range(len(ACTION_ORDER)), ACTION_ORDER)
        ax.set_yticks(range(len(profiles)), profiles)
        ax.set_title(title)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, format(matrix[i, j], fmt), ha="center", va="center", fontsize=9)
        fig.colorbar(image, ax=ax, shrink=0.82)
    fig.suptitle("E-adaptive operator usage and observed reward")
    fig.tight_layout()
    _save(fig, output_dir / "week6_operator_heatmap.png")


def plot_convergence(payload: dict, output_dir: Path) -> None:
    trace = [r for r in payload["adaptive_trace"] if r.get("method") == "E_adaptive_portfolio"]
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in trace:
        key = (row.get("profile"), row.get("scale"), row.get("instance_seed"), row.get("construction_source"))
        groups[key].append(row)
    ranked = sorted(groups.items(), key=lambda item: len(item[1]), reverse=True)[:4]
    fig, ax = plt.subplots(figsize=(9.3, 5.8))
    if not ranked:
        ax.text(0.5, 0.5, "No adaptive trace rows", ha="center", va="center")
    for key, rows in ranked:
        rows = sorted(rows, key=lambda row: row["step"])
        trajectory = [rows[0]["objective_before"]]
        current = trajectory[0]
        for row in rows:
            if row["accepted"]:
                current = row["objective_after"]
            trajectory.append(current)
        label = f"{key[0]} n={key[1]} seed={key[2]} {key[3]}"
        ax.step(range(len(trajectory)), trajectory, where="post", marker="o", ms=3, label=label)
    ax.set_xlabel("Adaptive decision step")
    ax.set_ylabel("Current feasible distance")
    ax.set_title("Representative E-adaptive search trajectories")
    ax.grid(linestyle=":", alpha=0.4)
    if ranked:
        ax.legend(fontsize=7)
    _save(fig, output_dir / "week6_convergence.png")


def plot_improvement_distribution(payload: dict, output_dir: Path) -> None:
    instances = payload["instances"]
    groups: dict[str, list[float]] = defaultdict(list)
    keys = sorted({(r["profile"], r["scale"], r["seed"]) for r in instances})
    for profile, scale, seed in keys:
        adaptive = next((r for r in instances if r["profile"] == profile and r["scale"] == scale and r["seed"] == seed and r["method"] == "E_adaptive_portfolio"), None)
        reference = next((r for r in instances if r["profile"] == profile and r["scale"] == scale and r["seed"] == seed and r["method"] == "D_composite_inter_route"), None)
        if adaptive and reference and adaptive["feasible"] and reference["feasible"]:
            groups[f"{profile}\nn={scale}"].append(100.0 * (reference["objective"] - adaptive["objective"]) / reference["objective"])
    labels = list(groups) or ["no jointly\nfeasible pairs"]
    values = [groups[label] for label in labels] if groups else [[0.0]]
    fig, ax = plt.subplots(figsize=(max(8.5, len(labels) * 1.1), 5.8))
    violin = ax.violinplot(values, showmeans=True, showextrema=True)
    for body in violin["bodies"]:
        body.set_facecolor(STYLE["E_adaptive_portfolio"][1])
        body.set_alpha(0.65)
    ax.axhline(0, color="#475569", linestyle="--", linewidth=1)
    ax.set_xticks(range(1, len(labels) + 1), labels)
    ax.set_ylabel("E-adaptive improvement over D (%)\n(positive = shorter)")
    ax.set_title("Per-instance adaptive portfolio improvement distribution")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    _save(fig, output_dir / "week6_improvement_distribution.png")


def generate_all(payload: dict, output_dir: Path = RESULTS_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_workflow(output_dir)
    plot_objective_feasibility(payload, output_dir)
    plot_quality_runtime(payload, output_dir)
    plot_operator_heatmap(payload, output_dir)
    plot_convergence(payload, output_dir)
    plot_improvement_distribution(payload, output_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RESULTS_DIR / "week6_results.json")
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    generate_all(payload, args.output_dir)
    print(json.dumps({"output_dir": str(args.output_dir), "figures": list(FIGURE_NAMES)}, indent=2))


if __name__ == "__main__":
    main()
