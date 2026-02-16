"""Reporting serialization tests."""

from __future__ import annotations

from stock_market_rag.pipeline.models import QuestionResult, RagRunResult, RetrievedChunk, UsageMetrics
from stock_market_rag.reporting.console_report import build_console_report
from stock_market_rag.reporting.json_report import to_json_dict


def _sample() -> RagRunResult:
    return RagRunResult(
        run_id="abc123",
        dataset_root="/tmp/data",
        embedding_model="text-embedding-3-small",
        chat_model="gpt-4o-mini",
        questions=[
            QuestionResult(
                question="Q1",
                answer="A1",
                retrieved=[
                    RetrievedChunk(
                        chunk_id="doc-1",
                        source="doc.txt",
                        similarity=0.88,
                        text_preview="preview",
                    )
                ],
            )
        ],
        metrics=UsageMetrics(
            embedding_calls=2,
            chat_calls=1,
            chunks_indexed=10,
            docs_indexed=2,
            retrieval_requests=1,
            failed_docs=0,
            stage_latency_ms={"retrieval": 12.3},
        ),
        generated_at="2026-02-16T00:00:00Z",
    )


def test_console_report_contains_key_fields() -> None:
    text = build_console_report(_sample())
    assert "run_id: abc123" in text
    assert "docs_indexed=2" in text
    assert "Q1" in text


def test_json_schema_keys() -> None:
    payload = to_json_dict(_sample())
    assert payload["run_id"] == "abc123"
    assert isinstance(payload["questions"], list)
    assert "metrics" in payload
