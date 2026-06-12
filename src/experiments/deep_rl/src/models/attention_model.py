"""Transformer encoder for EVRP-TW node embeddings."""

from __future__ import annotations

import torch
from torch import nn


class AttentionEncoder(nn.Module):
    def __init__(
        self,
        input_dim: int = 9,
        embedding_dim: int = 128,
        num_heads: int = 8,
        num_layers: int = 3,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.input_projection = nn.Linear(input_dim, embedding_dim)
        layer = nn.TransformerEncoderLayer(
            d_model=embedding_dim,
            nhead=num_heads,
            dim_feedforward=embedding_dim * 4,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=num_layers)
        self.normalization = nn.LayerNorm(embedding_dim)

    def forward(self, node_features: torch.Tensor) -> torch.Tensor:
        embeddings = self.input_projection(node_features)
        return self.normalization(self.encoder(embeddings))
