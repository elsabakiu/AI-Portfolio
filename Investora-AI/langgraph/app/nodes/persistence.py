from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..repositories import RunRepository
from ..state import GraphState

logger = logging.getLogger(__name__)
run_repo = RunRepository()


def persist_snapshot_node(state: GraphState) -> GraphState:
    from ..event_store import init_db
    from ..models import AnalysisSnapshot
    from ..monitor_client import post_monitor_event

    snapshot = AnalysisSnapshot(
        run_id=state["run_id"],
        run_date=state["run_date"],
        timestamp=datetime.now(timezone.utc).isoformat(),
        scope=state.get("scope", "full"),
        tickers=state["tickers"],
        scores=state["scores"],
        signal_events=state["signal_events"],
        failed_tickers=state["failed_tickers"],
        error_count=len(state["errors"]),
    )
    try:
        init_db()
        run_repo.save_snapshot(snapshot)
        logger.info("persist_snapshot_node", extra={"run_id": state["run_id"]})
    except Exception as exc:  # noqa: BLE001
        state["errors"].append({"ticker": "*", "tool": "event_store", "error": str(exc)})

    run_status = "error" if state["errors"] else "ok"
    post_monitor_event(
        run_id=state["run_id"],
        run_date=state["run_date"],
        status=run_status,
        scope=state.get("scope", "full"),
        error_count=len(state["errors"]),
        signal_count=len(state["signal_events"]),
    )
    return state
