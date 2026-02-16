"""In-memory vector store with cosine similarity."""

from __future__ import annotations

import numpy as np

from stock_market_rag.pipeline.models import EmbeddedChunk


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._items: list[EmbeddedChunk] = []

    def add(self, items: list[EmbeddedChunk]) -> None:
        self._items.extend(items)

    def count(self) -> int:
        return len(self._items)

    def search_with_scores(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 3,
    ) -> list[tuple[EmbeddedChunk, float]]:
        if not self._items:
            return []

        query = np.array(query_embedding, dtype=float)
        scored: list[tuple[float, EmbeddedChunk]] = []

        for item in self._items:
            emb = np.array(item.embedding, dtype=float)
            denom = np.linalg.norm(query) * np.linalg.norm(emb)
            similarity = float(np.dot(query, emb) / denom) if denom else 0.0
            scored.append((similarity, item))

        scored.sort(key=lambda row: row[0], reverse=True)
        return [(item, score) for score, item in scored[:top_k]]
