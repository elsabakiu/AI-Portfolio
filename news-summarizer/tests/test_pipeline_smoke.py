"""Smoke test for end-to-end pipeline orchestration with fakes."""

from __future__ import annotations

from dataclasses import dataclass

from news_summariser.config import Settings
from news_summariser.pipeline.models import Article
from news_summariser.pipeline.run import PipelineRunner


class FakeNewsClient:
    def fetch_articles(self, *, category, query, limit, language):  # noqa: ANN001
        _ = (category, query, language)
        return [
            Article(
                title="A",
                description="A desc",
                content="A content",
                url="https://example.com/a",
                source="NewsAPI",
                published_at="2026-02-01T10:00:00Z",
            ),
            Article(
                title="B",
                description="B desc",
                content="B content",
                url="https://example.com/b",
                source="NewsAPI",
                published_at="2026-02-01T09:00:00Z",
            ),
        ][:limit]


class FakeGdeltClient:
    def fetch_articles(self, *, category, query, limit, language):  # noqa: ANN001
        _ = (category, query, limit, language)
        return [
            Article(
                title="A duplicate",
                description="dup",
                content="dup",
                url="https://example.com/a",
                source="GDELT",
                published_at="2026-02-01T11:00:00Z",
            )
        ]


@dataclass
class FakeUsage:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float


class FakeOpenAIClient:
    def generate(self, prompt: str, *, model=None):  # noqa: ANN001
        _ = model
        return f"summary::{prompt[:20]}", FakeUsage("openai", "gpt-4o-mini", 10, 5, 0.00001)


class FakeCohereClient:
    def generate(self, prompt: str, *, model=None):  # noqa: ANN001
        _ = (model, prompt)
        return "neutral, confidence 70", FakeUsage("cohere", "command-a", 8, 4, 0.00002)


def test_pipeline_smoke_schema_stable() -> None:
    settings = Settings(
        openai_api_key="x",
        cohere_api_key="y",
        news_api_key="z",
        openai_model="gpt-4o-mini",
        cohere_model="command-a-03-2025",
        request_timeout=30,
        max_retries=1,
        openai_rpm=100,
        cohere_rpm=100,
        news_api_rpm=100,
        gdelt_rpm=100,
        daily_budget=5.0,
        default_category="technology",
        default_limit=5,
        max_limit=10,
        async_max_concurrent=2,
        llm_primary="openai",
        log_json=False,
        debug_log_article_text=False,
    )

    runner = PipelineRunner(
        settings=settings,
        news_client=FakeNewsClient(),
        gdelt_client=FakeGdeltClient(),
        openai_client=FakeOpenAIClient(),
        cohere_client=FakeCohereClient(),
    )

    result = runner.run(
        run_id="run123",
        source="all",
        category="technology",
        query=None,
        limit=5,
        language="en",
        mode="sync",
    )

    assert result.run_id == "run123"
    assert result.metrics.n_fetched == 2
    assert result.metrics.n_processed == 2
    assert result.metrics.n_succeeded == 2
    assert result.metrics.n_failed == 0
    assert result.articles[0].summary
    assert result.articles[0].sentiment

    payload = result.to_dict()
    assert set(payload.keys()) == {
        "run_id",
        "source",
        "category",
        "query",
        "language",
        "mode",
        "requested_limit",
        "generated_at",
        "articles",
        "failures",
        "metrics",
    }
    assert "token_usage_by_provider" in payload["metrics"]
