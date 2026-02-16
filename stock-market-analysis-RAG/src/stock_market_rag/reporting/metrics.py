"""Run metrics utilities."""

from __future__ import annotations

from collections import defaultdict

from stock_market_rag.pipeline.models import UsageMetrics


class MetricsCollector:
    def __init__(self) -> None:
        self.metrics = UsageMetrics(stage_latency_ms={})
        self._stage_totals: dict[str, float] = defaultdict(float)
        self._stage_counts: dict[str, int] = defaultdict(int)

    def record_stage_latency(self, stage: str, latency_ms: float) -> None:
        self._stage_totals[stage] += max(0.0, latency_ms)
        self._stage_counts[stage] += 1
        self.metrics.stage_latency_ms[stage] = round(
            self._stage_totals[stage] / max(1, self._stage_counts[stage]),
            2,
        )
