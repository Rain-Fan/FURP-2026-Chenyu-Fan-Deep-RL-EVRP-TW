"""Unified command-line interface for training, evaluation, and visualisation."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch
from tqdm import trange

from src.algorithms.baseline import greedy_solve
from src.algorithms.ppo import ppo_step
from src.algorithms.reinforce import policy_rollout, reinforce_step
from src.models.policy_network import PolicyNetwork
from src.utils.config import load_config
from src.utils.data_loader import DataConfig, generate_batch
from src.utils.metrics import summarize
from src.utils.visualization import plot_routes, plot_training_history


def select_device(requested: str) -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def build_model(config: dict[str, Any], device: torch.device) -> PolicyNetwork:
    return PolicyNetwork(**config.get("model", {})).to(device)


def save_checkpoint(
    path: Path,
    model: PolicyNetwork,
    optimizer: torch.optim.Optimizer,
    config: dict[str, Any],
    iteration: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "config": config,
            "iteration": iteration,
        },
        path,
    )


def load_checkpoint(
    path: str | Path,
    device: torch.device,
) -> tuple[PolicyNetwork, dict[str, Any]]:
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    config = checkpoint["config"]
    model = build_model(config, device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, config


def train(config_path: str | Path) -> Path:
    config = load_config(config_path)
    set_seed(int(config["seed"]))
    device = select_device(config.get("device", "auto"))
    data_config = DataConfig(**config["data"])
    model = build_model(config, device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config["learning_rate"]))
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, float]] = []

    for iteration in trange(1, int(config["iterations"]) + 1, desc=config["algorithm"]):
        batch = generate_batch(
            int(config["batch_size"]),
            data_config,
            device=device,
            seed=int(config["seed"]) + iteration,
        )
        if config["algorithm"] == "reinforce":
            metrics = reinforce_step(
                model,
                optimizer,
                batch,
                entropy_coefficient=float(config.get("entropy_coefficient", 0.01)),
            )
        elif config["algorithm"] == "ppo":
            metrics = ppo_step(
                model,
                optimizer,
                batch,
                update_epochs=int(config.get("update_epochs", 4)),
                clip_epsilon=float(config.get("clip_epsilon", 0.2)),
                value_coefficient=float(config.get("value_coefficient", 0.5)),
                entropy_coefficient=float(config.get("entropy_coefficient", 0.01)),
                gamma=float(config.get("gamma", 1.0)),
                gae_lambda=float(config.get("gae_lambda", 0.95)),
            )
        else:
            raise ValueError(f"Unsupported algorithm: {config['algorithm']}")

        metrics["iteration"] = iteration
        history.append(metrics)
        if iteration % int(config.get("checkpoint_every", 25)) == 0:
            save_checkpoint(output_dir / f"checkpoint_{iteration}.pt", model, optimizer, config, iteration)

    checkpoint_path = output_dir / "model_final.pt"
    save_checkpoint(checkpoint_path, model, optimizer, config, int(config["iterations"]))
    (output_dir / "history.json").write_text(
        json.dumps(history, indent=2) + "\n",
        encoding="utf-8",
    )
    plot_training_history(history, output_dir / "training_curve.png")
    print(json.dumps({"checkpoint": str(checkpoint_path), "device": str(device)}, indent=2))
    return checkpoint_path


@torch.no_grad()
def evaluate(
    config_path: str | Path,
    checkpoint_path: str | Path | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    device = select_device(config.get("device", "auto"))
    data_config = DataConfig(**config["data"])
    data = generate_batch(
        int(config["batch_size"]),
        data_config,
        device=device,
        seed=int(config["seed"]),
    )
    baseline = greedy_solve(data)
    report: dict[str, Any] = {
        "device": str(device),
        "baseline": summarize(
            baseline["cost"],
            baseline["feasible"],
            baseline["distance"],
            baseline["vehicles_used"],
        ),
    }
    if checkpoint_path is not None:
        model, _ = load_checkpoint(checkpoint_path, device)
        rollout = policy_rollout(model, data, decode_type="greedy")
        report["policy"] = summarize(rollout.cost, rollout.feasible)

    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "evaluation.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return report


@torch.no_grad()
def visualize(
    config_path: str | Path,
    output: str | Path,
    checkpoint_path: str | Path | None = None,
) -> None:
    config = load_config(config_path)
    device = select_device(config.get("device", "auto"))
    data_config = DataConfig(**config["data"])
    data = generate_batch(1, data_config, device=device, seed=int(config["seed"]))
    if checkpoint_path is None:
        solution = greedy_solve(data)
        routes = solution["routes"][0]
        title = "Greedy EVRP-TW route"
    else:
        model, _ = load_checkpoint(checkpoint_path, device)
        rollout = policy_rollout(model, data, decode_type="greedy")
        sequence = rollout.actions[0].tolist()
        routes = [[0]]
        for node in sequence:
            routes[-1].append(node)
            if node == 0 and len(routes[-1]) > 1:
                routes.append([0])
        routes = [route for route in routes if len(route) > 1]
        title = "Deep RL EVRP-TW route"
    plot_routes(
        data["coords"][0],
        data["node_type"][0],
        routes,
        output,
        title=title,
    )
    print(f"Saved route plot to {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    train_parser = commands.add_parser("train")
    train_parser.add_argument("--config", required=True)
    evaluate_parser = commands.add_parser("evaluate")
    evaluate_parser.add_argument("--config", required=True)
    evaluate_parser.add_argument("--checkpoint")
    visual_parser = commands.add_parser("visualize")
    visual_parser.add_argument("--config", required=True)
    visual_parser.add_argument("--checkpoint")
    visual_parser.add_argument("--output", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "train":
        train(args.config)
    elif args.command == "evaluate":
        evaluate(args.config, args.checkpoint)
    elif args.command == "visualize":
        visualize(args.config, args.output, args.checkpoint)


if __name__ == "__main__":
    main()
