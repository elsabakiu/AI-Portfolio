"""Tests for console/json reporting outputs."""

from __future__ import annotations

from news_summariser.pipeline.models import (
    FailureRecord,
    ProcessedArticle,
    ProviderUsage,
    RunMetrics,
    RunResult,
)
from news_summariser.reporting.console_report import build_console_report
from news_summariser.reporting.json_report import to_json_dict


def _sample_result() -> RunResult:
    return RunResult(
        run_id="abc123",
        source="newsapi",
        category="technology",
        query=None,
        language="en",
        mode="sync",
        requested_limit=2,
        generated_at="2026-02-16T20:00:00Z",
        articles=[
            ProcessedArticle(
                title="A",
                description="desc",
                content="content",
                url="https://example.com/a",
                source="NewsAPI",
                published_at="2026-02-16T12:00:00Z",
                summary="Short summary",
                sentiment="Neutral",
            )
        ],
        failures=[FailureRecord(url="", title="", stage="fetch", error="none")],
        metrics=RunMetrics(
            n_fetched=2,
            n_processed=2,
            n_succeeded=1,
            n_failed=1,
            stage_latency_ms={"fetch": 120.5, "article_process": 300.2},
            token_usage_by_provider={
                "openai": ProviderUsage(requests=1, input_tokens=123, output_tokens=45, estimated_cost_usd=0.0002)
            },
        ),
    )


def test_console_report_contains_summary_fields() -> None:
    report = build_console_report(_sample_result())
    assert "run_id: abc123" in report
    assert "n_fetched=2" in report
    assert "estimated_total_cost_usd=" in report


def test_json_report_schema() -> None:
    payload = to_json_dict(_sample_result())
    assert payload["run_id"] == "abc123"
    assert payload["metrics"]["n_succeeded"] == 1
    assert isinstance(payload["articles"], list)
