"""Smoke test for RAG pipeline with fake provider (no network)."""

from __future__ import annotations

from pathlib import Path

from stock_market_rag.config import Settings
from stock_market_rag.pipeline.run import RagPipeline


class FakeProvider:
    def embed_texts(self, texts: list[str], *, model: str | None = None, batch_size: int = 100) -> list[list[float]]:
        _ = (model, batch_size)
        out: list[list[float]] = []
        for text in texts:
            s = float(len(text) % 10 + 1)
            out.append([s, s / 2.0, 1.0])
        return out

    def answer_with_context(self, *, question: str, context_chunks: list[str], model: str | None = None) -> str:
        _ = model
        return f"Answer based on {len(context_chunks)} chunks for: {question[:20]}"


def test_pipeline_smoke(tmp_path: Path) -> None:
    data_dir = tmp_path / "dataset"
    data_dir.mkdir()
    (data_dir / "doc1.txt").write_text("AMD revenue grew with AI demand.", encoding="utf-8")
    (data_dir / "doc2.txt").write_text("NVDA highlighted datacenter growth and margins.", encoding="utf-8")

    settings = Settings(
        openai_api_key="test-key",
        embedding_model="text-embedding-3-small",
        chat_model="gpt-4o-mini",
        embedding_batch_size=10,
        request_timeout=10,
        max_retries=1,
        chunk_size=50,
        chunk_overlap=10,
        top_k=2,
        log_json=False,
        dataset_root=data_dir,
    )

    pipeline = RagPipeline(settings=settings, provider=FakeProvider())
    result = pipeline.run(
        run_id="run123",
        dataset_root=data_dir,
        questions=["Which company has stronger AI growth signals?"],
        top_k=2,
    )

    assert result.run_id == "run123"
    assert result.metrics.docs_indexed == 2
    assert result.metrics.chunks_indexed > 0
    assert result.metrics.embedding_calls >= 2
    assert len(result.questions) == 1
    assert result.questions[0].answer
    assert result.questions[0].retrieved
