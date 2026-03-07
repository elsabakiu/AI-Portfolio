from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from ..graph_constants import UNIVERSE_PATH
from ..mcp_tools.anomaly_detector import build_anomaly_signal_event, detect_score_delta, detect_volume_spike
from ..state import GraphState

logger = logging.getLogger(__name__)


def detect_anomalies_node(state: GraphState) -> GraphState:
    from ..event_store import load_recent_runs, load_run

    run_id = state["run_id"]
    run_date = state["run_date"]
    scores = state.get("scores", {})
    anomaly_events: List[Dict[str, Any]] = []

    prior_scores_by_ticker: Dict[str, Dict[str, float]] = {}
    try:
        recent = load_recent_runs(limit=2)
        prior_run_meta = next((r for r in recent if r["run_id"] != run_id), None)
        if prior_run_meta:
            prior_snapshot = load_run(prior_run_meta["run_id"])
            if prior_snapshot:
                prior_scores_by_ticker = prior_snapshot.get("scores", {})
    except Exception as exc:  # noqa: BLE001
        logger.warning("detect_anomalies_node: could not load prior run scores: %s", exc)

    volume_by_ticker: Dict[str, Dict[str, float]] = {}
    try:
        if UNIVERSE_PATH.exists():
            with UNIVERSE_PATH.open() as f:
                universe_data = json.load(f)
            for entry in universe_data.get("tickers", []):
                t = entry.get("ticker", "")
                if t and "mock_volume" in entry and "mock_avg_volume" in entry:
                    volume_by_ticker[t] = {
                        "volume": float(entry["mock_volume"]),
                        "avg_volume": float(entry["mock_avg_volume"]),
                    }
    except Exception as exc:  # noqa: BLE001
        logger.warning("detect_anomalies_node: could not load volume data: %s", exc)

    for ticker, score_block in scores.items():
        try:
            vol_data = volume_by_ticker.get(ticker)
            if vol_data:
                anomaly = detect_volume_spike(
                    ticker=ticker,
                    volume=vol_data["volume"],
                    avg_volume=vol_data["avg_volume"],
                )
                if anomaly:
                    anomaly_events.append(build_anomaly_signal_event(ticker, anomaly, run_id, run_date, score_block))

            prior = prior_scores_by_ticker.get(ticker)
            if prior:
                anomaly = detect_score_delta(ticker=ticker, current_scores=score_block, prior_scores=prior)
                if anomaly:
                    anomaly_events.append(build_anomaly_signal_event(ticker, anomaly, run_id, run_date, score_block))
        except Exception as exc:  # noqa: BLE001
            logger.warning("detect_anomalies_node: ticker %s failed: %s", ticker, exc)
            state["errors"].append({"ticker": ticker, "tool": "detect_anomalies", "error": str(exc)})

    state["anomaly_signals"] = anomaly_events
    logger.info(
        "detect_anomalies_node: %d anomaly signal(s) produced",
        len(anomaly_events),
        extra={"run_id": run_id},
    )
    return state
