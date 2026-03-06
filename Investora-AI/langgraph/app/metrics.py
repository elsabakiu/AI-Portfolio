from __future__ import annotations

import threading
from collections import defaultdict
from statistics import mean
from typing import Any, Dict, List

_lock = threading.Lock()
_node_timings: Dict[str, List[float]] = defaultdict(list)
_provider_counters: Dict[str, int] = defaultdict(int)


def record_node_timing(node_name: str, duration_ms: float) -> None:
    with _lock:
        _node_timings[node_name].append(duration_ms)


def record_provider_call(provider_name: str) -> None:
    with _lock:
        _provider_counters[provider_name] += 1


def snapshot_metrics() -> Dict[str, Any]:
    with _lock:
        node_stats = {
            name: {
                "count": len(samples),
                "avg_ms": round(mean(samples), 2) if samples else 0.0,
                "last_ms": round(samples[-1], 2) if samples else 0.0,
            }
            for name, samples in _node_timings.items()
        }
        provider_stats = dict(_provider_counters)
    return {
        "node_timings": node_stats,
        "provider_counters": provider_stats,
    }


def reset_metrics() -> None:
    with _lock:
        _node_timings.clear()
        _provider_counters.clear()
