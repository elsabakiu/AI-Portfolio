"""Backward-compatible vector store API."""

from __future__ import annotations

from dataclasses import dataclass

from lab2_rag_openai.chunking import Chunk
from stock_market_rag.pipeline.models import EmbeddedChunk as _EmbeddedChunk
from stock_market_rag.pipeline.models import Chunk as _Chunk
from stock_market_rag.retrieval.vector_store import InMemoryVectorStore as _InMemoryVectorStore


@dataclass
class EmbeddedChunk:
    chunk: Chunk
    embedding: list[float]


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._store = _InMemoryVectorStore()

    def add(self, items: list[EmbeddedChunk]) -> None:
        converted = [
            _EmbeddedChunk(chunk=_Chunk(id=i.chunk.id, text=i.chunk.text, source=i.chunk.source), embedding=i.embedding)
            for i in items
        ]
        self._store.add(converted)

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[EmbeddedChunk]:
        return [item for item, _ in self.search_with_scores(query_embedding, top_k)]

    def search_with_scores(self, query_embedding: list[float], top_k: int = 3) -> list[tuple[EmbeddedChunk, float]]:
        rows = self._store.search_with_scores(query_embedding=query_embedding, top_k=top_k)
        out: list[tuple[EmbeddedChunk, float]] = []
        for item, score in rows:
            out.append(
                (
                    EmbeddedChunk(
                        chunk=Chunk(id=item.chunk.id, text=item.chunk.text, source=item.chunk.source),
                        embedding=item.embedding,
                    ),
                    score,
                )
            )
        return out
