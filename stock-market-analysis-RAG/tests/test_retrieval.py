"""Vector retrieval behavior tests."""

from __future__ import annotations

from stock_market_rag.pipeline.models import Chunk, EmbeddedChunk
from stock_market_rag.retrieval.vector_store import InMemoryVectorStore


def test_vector_store_returns_descending_similarity() -> None:
    store = InMemoryVectorStore()
    store.add(
        [
            EmbeddedChunk(chunk=Chunk(id="a", text="A", source="s"), embedding=[1.0, 0.0]),
            EmbeddedChunk(chunk=Chunk(id="b", text="B", source="s"), embedding=[0.5, 0.5]),
            EmbeddedChunk(chunk=Chunk(id="c", text="C", source="s"), embedding=[0.0, 1.0]),
        ]
    )

    rows = store.search_with_scores([1.0, 0.0], top_k=2)
    assert len(rows) == 2
    assert rows[0][0].chunk.id == "a"
    assert rows[0][1] >= rows[1][1]
