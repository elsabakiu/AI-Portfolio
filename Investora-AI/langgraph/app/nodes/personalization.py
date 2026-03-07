from __future__ import annotations

import logging
from typing import Any, Dict, List

from ..alert_checker import check_user_alerts
from ..personalization import build_user_bundle
from ..repositories import BundleRepository
from ..state import GraphState

logger = logging.getLogger(__name__)
bundle_repo = BundleRepository()


def emit_signals_node(state: GraphState) -> GraphState:
    from ..models import build_signal_events

    base_events = build_signal_events(
        run_id=state["run_id"],
        run_date=state["run_date"],
        scores=state["scores"],
        failed_tickers=state["failed_tickers"],
        synthesis=state["per_ticker_synthesis"],
    )
    anomaly_events = list(state.get("anomaly_signals", []))
    seen_ids = {ev["id"] for ev in base_events}
    state["signal_events"] = base_events + [ev for ev in anomaly_events if ev["id"] not in seen_ids]
    logger.info(
        "emit_signals_node",
        extra={
            "run_id": state["run_id"],
            "signal_count": len(state["signal_events"]),
            "anomaly_count": len(anomaly_events),
        },
    )
    return state


def personalize_signals_node(state: GraphState) -> GraphState:
    bundles: Dict[str, Dict[str, Any]] = {}
    users = state.get("user_profiles", [])
    if not users:
        state["personalized_bundles"] = {}
        return state

    for profile in users:
        user_id = profile.get("user_id", "")
        if not user_id:
            continue
        try:
            bundle = build_user_bundle(
                user_profile=profile,
                signal_events=state.get("signal_events", []),
                scores=state.get("scores", {}),
                run_id=state["run_id"],
                run_date=state["run_date"],
                per_ticker_data=state.get("per_ticker_data", {}),
            )
            bundle_repo.save_user_bundle(bundle)
            bundles[user_id] = bundle
        except Exception as exc:  # noqa: BLE001
            state["errors"].append({"ticker": user_id, "tool": "personalize_signals", "error": str(exc)})
            logger.warning("personalize_signals_node: user %s failed: %s", user_id, exc)

    state["personalized_bundles"] = bundles
    logger.info(
        "personalize_signals_node",
        extra={"run_id": state["run_id"], "user_count": len(users), "saved_bundles": len(bundles)},
    )
    return state


def check_user_alerts_node(state: GraphState) -> GraphState:
    try:
        triggered = check_user_alerts()
        state["triggered_user_alerts"] = triggered
        logger.info(
            "check_user_alerts_node",
            extra={"run_id": state["run_id"], "triggered_count": len(triggered)},
        )
    except Exception as exc:  # noqa: BLE001
        state["errors"].append({"ticker": "*", "tool": "check_user_alerts", "error": str(exc)})
    return state
