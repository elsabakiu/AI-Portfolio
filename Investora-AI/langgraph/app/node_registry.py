from __future__ import annotations

from typing import Callable, Dict

from .nodes.anomalies import detect_anomalies_node
from .nodes.data_collection import execute_tool_action, init_state, plan_next_action
from .nodes.delivery import (
    assemble_markdown_node,
    assemble_report_json_node,
    persist_report_node,
    post_alerts_node,
    post_candidates_node,
    post_to_n8n_node,
)
from .nodes.evidence import retrieve_rag_context_node, synthesize_evidence_node
from .nodes.persistence import persist_snapshot_node
from .nodes.personalization import check_user_alerts_node, emit_signals_node, personalize_signals_node
from .nodes.scoring import compute_scores_node
from .state import GraphState

NODE_REGISTRY: Dict[str, Callable[[GraphState], GraphState]] = {
    "init_state": init_state,
    "plan_next_action": plan_next_action,
    "execute_tool_action": execute_tool_action,
    "compute_scores": compute_scores_node,
    "detect_anomalies": detect_anomalies_node,
    "retrieve_rag_context": retrieve_rag_context_node,
    "synthesize_evidence": synthesize_evidence_node,
    "emit_signals": emit_signals_node,
    "personalize_signals": personalize_signals_node,
    "check_user_alerts": check_user_alerts_node,
    "post_alerts": post_alerts_node,
    "post_candidates": post_candidates_node,
    "assemble_report_json": assemble_report_json_node,
    "assemble_markdown": assemble_markdown_node,
    "post_to_n8n": post_to_n8n_node,
    "persist_report": persist_report_node,
    "persist_snapshot": persist_snapshot_node,
}
