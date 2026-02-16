"""Metrics collection for run observability."""

from __future__ import annotations

from collections import defaultdict

from news_summariser.pipeline.models import ProviderUsage, RunMetrics


class MetricsCollector:
    def __init__(self) -> None:
        self._metrics = RunMetrics(
            stage_latency_ms={},
            token_usage_by_provider={},
        )
        self._stage_totals: dict[str, float] = defaultdict(float)
        self._stage_counts: dict[str, int] = defaultdict(int)

    @property
    def metrics(self) -> RunMetrics:
        return self._metrics

    def set_counts(self, *, fetched: int, processed: int, succeeded: int, failed: int) -> None:
        self._metrics.n_fetched = fetched
        self._metrics.n_processed = processed
        self._metrics.n_succeeded = succeeded
        self._metrics.n_failed = failed

    def record_stage_latency(self, stage: str, latency_ms: float) -> None:
        self._stage_totals[stage] += max(0.0, latency_ms)
        self._stage_counts[stage] += 1
        self._metrics.stage_latency_ms[stage] = round(
            self._stage_totals[stage] / max(1, self._stage_counts[stage]),
            2,
        )

    def record_usage(self, *, provider: str, input_tokens: int, output_tokens: int, estimated_cost_usd: float) -> None:
        usage = self._metrics.token_usage_by_provider.setdefault(provider, ProviderUsage())
        usage.requests += 1
        usage.input_tokens += max(0, input_tokens)
        usage.output_tokens += max(0, output_tokens)
        usage.estimated_cost_usd += max(0.0, estimated_cost_usd)

    def total_estimated_cost(self) -> float:
        return round(sum(usage.estimated_cost_usd for usage in self._metrics.token_usage_by_provider.values()), 6)
