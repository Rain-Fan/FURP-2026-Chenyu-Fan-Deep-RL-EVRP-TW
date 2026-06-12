"""Pointer decoder with dynamic EVRP-TW context."""

from __future__ import annotations

import math

import torch
from torch import nn


class PointerDecoder(nn.Module):
    def __init__(self, embedding_dim: int = 128, state_dim: int = 4):
        super().__init__()
        self.state_projection = nn.Linear(state_dim, embedding_dim)
        self.query_projection = nn.Linear(embedding_dim * 3, embedding_dim)
        self.key_projection = nn.Linear(embedding_dim, embedding_dim, bias=False)
        self.value_head = nn.Sequential(
            nn.Linear(embedding_dim * 2, embedding_dim),
            nn.GELU(),
            nn.Linear(embedding_dim, 1),
        )
        self.scale = 1 / math.sqrt(embedding_dim)

    def forward(
        self,
        embeddings: torch.Tensor,
        state_features: torch.Tensor,
        current_node: torch.Tensor,
        action_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        batch_idx = torch.arange(embeddings.size(0), device=embeddings.device)
        current = embeddings[batch_idx, current_node]
        graph = embeddings.mean(dim=1)
        dynamic = self.state_projection(state_features)
        query = self.query_projection(torch.cat((current, graph, dynamic), dim=-1))
        keys = self.key_projection(embeddings)
        logits = torch.einsum("bd,bnd->bn", query, keys) * self.scale
        logits = 10.0 * torch.tanh(logits)
        logits = logits.masked_fill(~action_mask, torch.finfo(logits.dtype).min)
        value = self.value_head(torch.cat((graph, dynamic), dim=-1)).squeeze(-1)
        return logits, value
