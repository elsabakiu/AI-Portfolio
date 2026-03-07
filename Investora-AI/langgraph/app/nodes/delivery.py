from __future__ import annotations

import logging
from typing import Any, Dict, List

from ..alert_client import post_alerts_to_n8n, post_user_alerts_to_n8n
from ..graph_constants import REPORT_DIR
from ..n8n_client import post_candidates_to_n8n, post_report_to_n8n
from ..reporting import build_markdown, build_report, persist_report
from ..state import GraphState
from ..weekly_digest import build_weekly_user_digest
from .shared import should_skip_post

logger = logging.getLogger(__name__)


def post_alerts_node(state: GraphState) -> GraphState:
    if should_skip_post(state):
        return state

    profiles_by_user = {str(p.get("user_id", "")): p for p in state.get("user_profiles", [])}
    bundles = state.get("personalized_bundles", {}) or {}
    for user_id, bundle in bundles.items():
        profile = profiles_by_user.get(user_id, {})
        if not profile or not bool(profile.get("alert_notifications", True)):
            continue
        chat_id = str(profile.get("telegram_chat_id", "")).strip()
        if not chat_id:
            continue

        all_signals = list(bundle.get("watchlist_signals", [])) + list(bundle.get("discovery_signals", []))
        important = [s for s in all_signals if str(s.get("urgency", "")).lower() == "high"]
        seen: set[str] = set()
        deduped: List[Dict[str, Any]] = []
        for s in important:
            sid = str(s.get("signal_id", ""))
            if sid and sid in seen:
                continue
            if sid:
                seen.add(sid)
            deduped.append(s)
        if not deduped:
            continue
        try:
            post_alerts_to_n8n(
                deduped,
                run_id=state["run_id"],
                run_date=state["run_date"],
                user_id=user_id,
                telegram_chat_id=chat_id,
            )
        except Exception as exc:  # noqa: BLE001
            state["errors"].append({"ticker": user_id, "tool": "alert_webhook", "error": str(exc)})

    user_alerts = state.get("triggered_user_alerts", [])
    if user_alerts:
        try:
            post_user_alerts_to_n8n(user_alerts, run_id=state["run_id"], run_date=state["run_date"])
        except Exception as exc:  # noqa: BLE001
            state["errors"].append({"ticker": "*", "tool": "user_alert_webhook", "error": str(exc)})

    return state


def post_candidates_node(state: GraphState) -> GraphState:
    if should_skip_post(state):
        return state

    if not bool(state.get("trigger_weekly_digest", False)):
        return state

    if state.get("scope", "full") != "full":
        return state

    profiles_by_user = {str(p.get("user_id", "")): p for p in state.get("user_profiles", [])}
    bundles = state.get("personalized_bundles", {}) or {}
    for user_id, bundle in bundles.items():
        profile = profiles_by_user.get(user_id, {})
        if not profile:
            continue
        if not bool(profile.get("weekly_email_digest", profile.get("daily_email_digest", False))):
            continue
        email = str(profile.get("email", "")).strip()
        if not email:
            continue
        try:
            digest = build_weekly_user_digest(profile, bundle, lookback_days=7)
            post_candidates_to_n8n(digest, run_id=state["run_id"], run_date=state["run_date"])
        except Exception as exc:  # noqa: BLE001
            state["errors"].append({"ticker": user_id, "tool": "candidate_webhook", "error": str(exc)})
    return state


def assemble_report_json_node(state: GraphState) -> GraphState:
    report = build_report(
        run_date=state["run_date"],
        per_ticker_data=state["per_ticker_data"],
        scores=state["scores"],
        report_dir=str(REPORT_DIR),
        errors=state["errors"],
        synthesis=state["per_ticker_synthesis"],
        rag_context=state.get("per_ticker_rag_context"),
        rag_stats=state.get("rag_stats"),
    )
    if report is not None:
        report["anomaly_signals"] = state.get("anomaly_signals", [])  # type: ignore[typeddict-unknown-key]
    state["report_json"] = report
    return state


def assemble_markdown_node(state: GraphState) -> GraphState:
    state["report_markdown"] = build_markdown(state["report_json"] or {})
    return state


def post_to_n8n_node(state: GraphState) -> GraphState:
    if should_skip_post(state):
        return state

    if not state["report_json"]:
        state["errors"].append({"ticker": "*", "tool": "n8n", "error": "No report payload to post"})
        return state

    try:
        post_report_to_n8n(state["report_json"])
    except Exception as exc:  # noqa: BLE001
        state["errors"].append({"ticker": "*", "tool": "n8n", "error": str(exc)})
    return state


def persist_report_node(state: GraphState) -> GraphState:
    if not state["report_json"]:
        return state
    path = persist_report(state["report_json"], state["run_date"], report_dir=str(REPORT_DIR))
    logger.info("persist_report", extra={"path": path, "run_date": state["run_date"]})
    return state
