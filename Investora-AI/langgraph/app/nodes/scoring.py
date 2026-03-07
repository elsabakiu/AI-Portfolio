from __future__ import annotations

from ..scoring import compute_all_scores
from ..settings import get_settings
from ..state import GraphState

settings = get_settings()


def compute_scores_node(state: GraphState) -> GraphState:
    quality_weight = settings.pipeline.quality_weight
    momentum_weight = settings.pipeline.momentum_weight

    failed = set(state["failed_tickers"])
    eligible = {
        t: data
        for t, data in state["per_ticker_data"].items()
        if t not in failed and all(k in data for k in ("market", "news"))
    }

    if not eligible:
        state["errors"].append({"ticker": "*", "tool": "compute_scores", "error": "No eligible tickers to score"})
        state["scores"] = {}
        return state

    scores, raw_components = compute_all_scores(eligible, quality_weight=quality_weight, momentum_weight=momentum_weight)
    for ticker, raw in raw_components.items():
        for t, v in raw.items():
            state["per_ticker_data"].setdefault(t, {})[ticker] = v

    state["scores"] = scores
    return state
