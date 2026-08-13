#!/usr/bin/env python3
"""Generate Week 7 research figures from the local JSON result bundle."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
for relative in ("src/experiments/week3", "src/experiments/week4"):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from compare_week3_baselines import generate_instance  # noqa: E402
from compare_week4_methods import apply_profile  # noqa: E402
from train_week7_rl import F_DQN_METHOD, METHODS  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
FIGURE_NAMES = (
    "week7_training_curve.png",
    "week7_objective_feasibility.png",
    "week7_quality_runtime.png",
    "week7_action_selection.png",
    "week7_policy_state_heatmap.png",
    "week7_representative_routes.png",
)
COLORS = {
    "D_composite_inter_route": "#d97706",
    "E_fixed_portfolio": "#7c3aed",
    "E_adaptive_portfolio": "#2563eb",
    F_DQN_METHOD: "#dc2626",
}
LABELS = {
    "D_composite_inter_route": "D fixed",
    "E_fixed_portfolio": "E fixed portfolio",
    "E_adaptive_portfolio": "E UCB1",
    F_DQN_METHOD: "F Double DQN",
}


def _save(fig, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _training_curve(payload, output_dir: Path) -> None:
    history = payload["training_history"]
    episodes = np.array([row["episode"] for row in history])
    returns = np.array([row["return"] for row in history], dtype=float)
    improvements = np.array([row["improvement_pct"] for row in history], dtype=float)
    losses = np.array([np.nan if row["mean_loss"] is None else row["mean_loss"] for row in history], dtype=float)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    axes[0].plot(episodes, returns, color="#2563eb", alpha=0.65)
    axes[0].set(title="Episode return", xlabel="Episode", ylabel="Return")
    axes[1].plot(episodes, improvements, color="#059669", alpha=0.65)
    axes[1].set(title="Feasible distance improvement", xlabel="Episode", ylabel="Improvement (%)")
    mask = np.isfinite(losses)
    axes[2].plot(episodes[mask], losses[mask], color="#dc2626", alpha=0.65)
    axes[2].set(title="Mean Huber loss", xlabel="Episode", ylabel="Loss")
    fig.suptitle("Week 7 Double-DQN training on local EVRP-TW instances", fontsize=15, fontweight="bold")
    _save(fig, output_dir / FIGURE_NAMES[0])


def _objective_feasibility(payload, output_dir: Path) -> None:
    aggregate = [row for row in payload["aggregate"] if row["profile"] == "baseline"]
    scales = sorted({int(row["scale"]) for row in aggregate})
    methods = list(METHODS)
    x = np.arange(len(scales))
    width = 0.19
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    for index, method in enumerate(methods):
        rows = [next(row for row in aggregate if row["scale"] == scale and row["method"] == method) for scale in scales]
        axes[0].bar(x + (index - 1.5) * width, [row["mean_objective_feasible"] or 0 for row in rows], width, label=LABELS[method], color=COLORS[method])
        axes[1].bar(x + (index - 1.5) * width, [row["feasibility_rate"] for row in rows], width, color=COLORS[method])
    axes[0].set(title="Held-out mean feasible objective", xlabel="Customers", ylabel="Distance", xticks=x, xticklabels=scales)
    axes[1].set(title="Held-out feasibility rate", xlabel="Customers", ylabel="Rate", xticks=x, xticklabels=scales, ylim=(0, 1.08))
    axes[0].legend(fontsize=8)
    fig.suptitle("Week 7 held-out baseline-profile comparison", fontsize=15, fontweight="bold")
    _save(fig, output_dir / FIGURE_NAMES[1])


def _quality_runtime(payload, output_dir: Path) -> None:
    aggregate = payload["aggregate"]
    fig, ax = plt.subplots(figsize=(8, 5.2))
    for method in METHODS:
        rows = [row for row in aggregate if row["method"] == method and row["mean_objective_feasible"] is not None]
        ax.scatter([row["mean_runtime_sec"] for row in rows], [row["mean_objective_feasible"] for row in rows], s=[35 + row["scale"] for row in rows], alpha=0.75, color=COLORS[method], label=LABELS[method])
    ax.set(xlabel="Mean runtime (s, log scale)", ylabel="Mean feasible distance", title="Quality/runtime trade-off across all held-out cells")
    ax.set_xscale("symlog", linthresh=1e-3)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    _save(fig, output_dir / FIGURE_NAMES[2])


def _action_selection(payload, output_dir: Path) -> None:
    trace = payload["action_trace"]
    counts = Counter(row["action"] for row in trace)
    accepted = Counter(row["action"] for row in trace if row["accepted"])
    actions = ["two_opt", "relocate", "swap"]
    x = np.arange(3)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    axes[0].bar(x, [counts[action] for action in actions], color=["#059669", "#dc2626", "#7c3aed"])
    axes[0].set(title="Greedy DQN action selections", xticks=x, xticklabels=actions, ylabel="Count")
    axes[1].bar(x, [accepted[action] / max(1, counts[action]) for action in actions], color=["#059669", "#dc2626", "#7c3aed"])
    axes[1].set(title="Accepted transition rate", xticks=x, xticklabels=actions, ylabel="Accepted / selected", ylim=(0, 1))
    fig.suptitle("Week 7 learned-policy behavior on held-out instances", fontsize=15, fontweight="bold")
    _save(fig, output_dir / FIGURE_NAMES[3])


def _policy_state_heatmap(payload, output_dir: Path) -> None:
    trace = payload["action_trace"]
    actions = ["two_opt", "relocate", "swap"]
    labels = ["scale", "vehicles", "obj ratio", "gain", "step", "stagnation", "last reward", "accept rate", "last 2opt", "last relocate", "last swap", "source"]
    matrix = np.zeros((3, 12), dtype=float)
    for index, action in enumerate(actions):
        states = [row["state"] for row in trace if row["action"] == action]
        if states:
            matrix[index] = np.mean(np.asarray(states, dtype=float), axis=0)
    fig, ax = plt.subplots(figsize=(12, 3.8))
    image = ax.imshow(matrix, aspect="auto", cmap="coolwarm")
    ax.set(yticks=np.arange(3), yticklabels=actions, xticks=np.arange(12), xticklabels=labels, title="Mean observed state when each action was selected")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    fig.colorbar(image, ax=ax, shrink=0.8)
    _save(fig, output_dir / FIGURE_NAMES[4])


def _representative_routes(payload, output_dir: Path) -> None:
    rows = payload["instances"]
    dqn_rows = [row for row in rows if row["method"] == F_DQN_METHOD and row["feasible"]]
    chosen = min(dqn_rows, key=lambda row: (abs(int(row["scale"]) - 50), row["profile"] != "baseline", int(row["seed"])))
    selected = [row for row in rows if row["profile"] == chosen["profile"] and row["scale"] == chosen["scale"] and row["seed"] == chosen["seed"]]
    instance = apply_profile(generate_instance(int(chosen["scale"]), int(chosen["seed"])), str(chosen["profile"]))
    coords = {node.idx: (node.x, node.y) for node in instance.nodes}
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.2))
    for ax, method in zip(axes, METHODS):
        row = next(item for item in selected if item["method"] == method)
        for route in row["routes"]:
            points = np.asarray([coords[int(node)] for node in route])
            ax.plot(points[:, 0], points[:, 1], color=COLORS[method], linewidth=0.9, alpha=0.65)
        ax.scatter([node.x for node in instance.customers], [node.y for node in instance.customers], s=7, color="#94a3b8")
        ax.scatter(instance.depot.x, instance.depot.y, s=45, color="#059669", marker="*")
        ax.set_title(f"{LABELS[method]}\nobj={row['objective']}", fontsize=9)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.suptitle(f"Same held-out instance: {chosen['profile']}, n={chosen['scale']}, seed={chosen['seed']}", fontsize=14, fontweight="bold")
    _save(fig, output_dir / FIGURE_NAMES[5])


def generate_all(payload: dict[str, object], output_dir: Path = RESULTS_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generators = (_training_curve, _objective_feasibility, _quality_runtime, _action_selection, _policy_state_heatmap, _representative_routes)
    for generate in generators:
        generate(payload, output_dir)
    return [output_dir / name for name in FIGURE_NAMES]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RESULTS_DIR / "week7_results.json")
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    for path in generate_all(payload, args.output_dir):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
