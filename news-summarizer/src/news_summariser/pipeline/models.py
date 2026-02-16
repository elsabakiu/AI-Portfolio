"""Typed models for pipeline input/output."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Article:
    title: str
    description: str
    content: str
    url: str
    source: str
    published_at: str


@dataclass
class ProcessedArticle(Article):
    summary: str
    sentiment: str


@dataclass
class FailureRecord:
    url: str
    title: str
    stage: str
    error: str


@dataclass
class ProviderUsage:
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class RunMetrics:
    n_fetched: int = 0
    n_processed: int = 0
    n_succeeded: int = 0
    n_failed: int = 0
    stage_latency_ms: dict[str, float] = field(default_factory=dict)
    token_usage_by_provider: dict[str, ProviderUsage] = field(default_factory=dict)


@dataclass
class RunResult:
    run_id: str
    source: str
    category: str | None
    query: str | None
    language: str
    mode: str
    requested_limit: int
    generated_at: str
    articles: list[ProcessedArticle]
    failures: list[FailureRecord]
    metrics: RunMetrics

    def to_dict(self) -> dict:
        data = asdict(self)
        return data
