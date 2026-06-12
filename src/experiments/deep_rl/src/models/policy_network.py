"""Attention-based policy and critic for EVRP-TW."""

from __future__ import annotations

import torch
from torch import nn

from src.env.state import EVRPTWState
from src.models.attention_model import AttentionEncoder
from src.models.pointer_network import PointerDecoder


def node_features(data: dict[str, torch.Tensor]) -> torch.Tensor:
    capacity = data["vehicle_capacity"][:, None]
    horizon = data["time_horizon"][:, None]
    node_type = data["node_type"]
    return torch.cat(
        (
            data["coords"],
            data["demand"].unsqueeze(-1) / capacity.unsqueeze(-1),
            data["ready_time"].unsqueeze(-1) / horizon.unsqueeze(-1),
            data["due_time"].unsqueeze(-1) / horizon.unsqueeze(-1),
            data["service_time"].unsqueeze(-1) / horizon.unsqueeze(-1),
            torch.nn.functional.one_hot(node_type, num_classes=3).float(),
        ),
        dim=-1,
    )


def state_features(
    data: dict[str, torch.Tensor],
    state: EVRPTWState,
) -> torch.Tensor:
    return torch.stack(
        (
            1.0 - state.used_capacity / data["vehicle_capacity"],
            state.battery / data["battery_capacity"],
            state.time / data["time_horizon"],
            1.0 - (state.vehicles_used.float() - 1) / data["num_vehicles"].float(),
        ),
        dim=-1,
    )


class PolicyNetwork(nn.Module):
    def __init__(
        self,
        embedding_dim: int = 128,
        num_heads: int = 8,
        num_layers: int = 3,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.encoder = AttentionEncoder(
            embedding_dim=embedding_dim,
            num_heads=num_heads,
            num_layers=num_layers,
            dropout=dropout,
        )
        self.decoder = PointerDecoder(embedding_dim=embedding_dim)

    def encode(self, data: dict[str, torch.Tensor]) -> torch.Tensor:
        return self.encoder(node_features(data))

    def decode(
        self,
        embeddings: torch.Tensor,
        data: dict[str, torch.Tensor],
        state: EVRPTWState,
        action_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        return self.decoder(
            embeddings,
            state_features(data, state),
            state.current_node,
            action_mask,
        )

    def forward(
        self,
        data: dict[str, torch.Tensor],
        state: EVRPTWState,
        action_mask: torch.Tensor,
        embeddings: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        embeddings = self.encode(data) if embeddings is None else embeddings
        return self.decode(embeddings, data, state, action_mask)
