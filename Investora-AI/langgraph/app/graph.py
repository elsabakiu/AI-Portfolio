from __future__ import annotations

import logging
import time
from functools import lru_cache
from typing import Callable

from .graph_constants import DEFAULT_UNIVERSE, REPORT_DIR, UNIVERSE_PATH
from .metrics import record_node_timing
from .node_registry import NODE_REGISTRY
from .state import GraphState

logger = logging.getLogger(__name__)

# Backward-compatible exports for existing API imports.
_UNIVERSE_PATH = UNIVERSE_PATH
_REPORT_DIR = REPORT_DIR

# Re-export core node callables for compatibility with direct imports.
init_state = NODE_REGISTRY["init_state"]
plan_next_action = NODE_REGISTRY["plan_next_action"]
execute_tool_action = NODE_REGISTRY["execute_tool_action"]
compute_scores_node = NODE_REGISTRY["compute_scores"]
detect_anomalies_node = NODE_REGISTRY["detect_anomalies"]
retrieve_rag_context_node = NODE_REGISTRY["retrieve_rag_context"]
synthesize_evidence_node = NODE_REGISTRY["synthesize_evidence"]
emit_signals_node = NODE_REGISTRY["emit_signals"]
personalize_signals_node = NODE_REGISTRY["personalize_signals"]
check_user_alerts_node = NODE_REGISTRY["check_user_alerts"]
post_alerts_node = NODE_REGISTRY["post_alerts"]
post_candidates_node = NODE_REGISTRY["post_candidates"]
assemble_report_json_node = NODE_REGISTRY["assemble_report_json"]
assemble_markdown_node = NODE_REGISTRY["assemble_markdown"]
post_to_n8n_node = NODE_REGISTRY["post_to_n8n"]
persist_report_node = NODE_REGISTRY["persist_report"]
persist_snapshot_node = NODE_REGISTRY["persist_snapshot"]


def planner_router(state: GraphState) -> str:
    action = state.get("action")
    if action in {"market", "fundamentals", "news"}:
        return "execute_tool_action"
    return "compute"


def _timed_node(name: str, fn: Callable[[GraphState], GraphState]) -> Callable[[GraphState], GraphState]:
    def _wrapped(state: GraphState) -> GraphState:
        started = time.perf_counter()
        out = fn(state)
        duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
        record_node_timing(name, duration_ms)
        timings = out.get("node_timings")
        if not isinstance(timings, dict):
            timings = {}
        timings[name] = duration_ms
        out["node_timings"] = timings
        logger.info(
            "node_timing",
            extra={"run_id": out.get("run_id", state.get("run_id", "")), "node": name, "duration_ms": duration_ms},
        )
        return out

    return _wrapped


@lru_cache(maxsize=1)
def _compiled_graph_singleton():
    from .graph_builder import compile_graph

    return compile_graph(timed_node=_timed_node, planner_router=planner_router)


def build_graph(force_rebuild: bool = False):
    """Return compiled graph app; cached singleton by default for performance."""
    if force_rebuild:
        _compiled_graph_singleton.cache_clear()
    return _compiled_graph_singleton()
