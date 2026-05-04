from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import settings

DEFAULT_BUCKETS_MS = (50, 100, 250, 500, 1000, 2500, 5000, 10000)


def _labels_key(labels: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, str(value)) for key, value in labels.items() if value is not None))


def _format_labels(labels: dict[str, Any]) -> str:
    if not labels:
        return ""

    def escape(value: Any) -> str:
        return str(value).replace("\\", "\\\\").replace(chr(34), "\\\"")

    pairs = ",".join(
        f'{key}="{escape(value)}"'
        for key, value in labels.items()
    )
    return f"{{{pairs}}}"


@dataclass
class HistogramValue:
    name: str
    labels: dict[str, Any]
    sum: float = 0
    count: int = 0
    buckets: dict[float, int] = field(
        default_factory=lambda: {bucket: 0 for bucket in DEFAULT_BUCKETS_MS}
    )


class MetricsRegistry:
    def __init__(self, service: str, environment: str) -> None:
        self.service = service
        self.environment = environment
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._histograms: dict[tuple[str, tuple[tuple[str, str], ...]], HistogramValue] = {}

    def _base_labels(self, labels: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "service": self.service,
            "environment": self.environment,
            **(labels or {}),
        }

    def increment(self, name: str, labels: dict[str, Any] | None = None, value: float = 1) -> None:
        normalized = self._base_labels(labels)
        key = (name, _labels_key(normalized))
        self._counters[key] = self._counters.get(key, 0) + value

    def set_gauge(self, name: str, value: float, labels: dict[str, Any] | None = None) -> None:
        normalized = self._base_labels(labels)
        key = (name, _labels_key(normalized))
        self._gauges[key] = value

    def observe(self, name: str, value: float, labels: dict[str, Any] | None = None) -> None:
        normalized = self._base_labels(labels)
        key = (name, _labels_key(normalized))
        histogram = self._histograms.get(key)
        if histogram is None:
            histogram = HistogramValue(name=name, labels=normalized)
            self._histograms[key] = histogram
        histogram.sum += value
        histogram.count += 1
        for bucket in histogram.buckets:
            if value <= bucket:
                histogram.buckets[bucket] += 1

    def render(self) -> str:
        lines: list[str] = []

        for (name, labels_key), value in self._counters.items():
            lines.append(f"{name}_total{_format_labels(dict(labels_key))} {value}")

        for (name, labels_key), value in self._gauges.items():
            lines.append(f"{name}{_format_labels(dict(labels_key))} {value}")

        for histogram in self._histograms.values():
            for bucket, bucket_value in histogram.buckets.items():
                lines.append(
                    f"{histogram.name}_bucket{_format_labels({**histogram.labels, 'le': bucket})} {bucket_value}"
                )
            lines.append(
                f"{histogram.name}_bucket{_format_labels({**histogram.labels, 'le': '+Inf'})} {histogram.count}"
            )
            lines.append(f"{histogram.name}_sum{_format_labels(histogram.labels)} {histogram.sum}")
            lines.append(
                f"{histogram.name}_count{_format_labels(histogram.labels)} {histogram.count}"
            )

        return "\n".join(lines) + "\n"


metrics = MetricsRegistry(
    service="infracloud-langgraph-workflow",
    environment=settings.app_env,
)
