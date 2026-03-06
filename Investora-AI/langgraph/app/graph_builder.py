from __future__ import annotations

from functools import lru_cache
from typing import Callable

from langgraph.graph import END, StateGraph

from .node_registry import NODE_REGISTRY
from .state import GraphState


def compile_graph(
    *,
    timed_node: Callable[[str, Callable[[GraphState], GraphState]], Callable[[GraphState], GraphState]],
    planner_router: Callable[[GraphState], str],
):
    graph = StateGraph(GraphState)

    for node_name in (
        "init_state",
        "plan_next_action",
        "execute_tool_action",
        "compute_scores",
        "detect_anomalies",
        "retrieve_rag_context",
        "synthesize_evidence",
        "emit_signals",
        "personalize_signals",
        "check_user_alerts",
        "post_alerts",
        "post_candidates",
        "assemble_report_json",
        "assemble_markdown",
        "post_to_n8n",
        "persist_report",
        "persist_snapshot",
    ):
        graph.add_node(node_name, timed_node(node_name, NODE_REGISTRY[node_name]))

    graph.set_entry_point("init_state")
    graph.add_edge("init_state", "plan_next_action")

    graph.add_conditional_edges(
        "plan_next_action",
        planner_router,
        {
            "execute_tool_action": "execute_tool_action",
            "compute": "compute_scores",
        },
    )

    graph.add_edge("execute_tool_action", "plan_next_action")
    graph.add_edge("compute_scores", "detect_anomalies")
    graph.add_edge("detect_anomalies", "retrieve_rag_context")
    graph.add_edge("retrieve_rag_context", "synthesize_evidence")
    graph.add_edge("synthesize_evidence", "emit_signals")
    graph.add_edge("emit_signals", "personalize_signals")
    graph.add_edge("personalize_signals", "check_user_alerts")
    graph.add_edge("check_user_alerts", "post_alerts")
    graph.add_edge("post_alerts", "post_candidates")
    graph.add_edge("post_candidates", "assemble_report_json")
    graph.add_edge("assemble_report_json", "assemble_markdown")
    graph.add_edge("assemble_markdown", "post_to_n8n")
    graph.add_edge("post_to_n8n", "persist_report")
    graph.add_edge("persist_report", "persist_snapshot")
    graph.add_edge("persist_snapshot", END)

    return graph.compile()


@lru_cache(maxsize=1)
def compile_graph_singleton(
    timed_node: Callable[[str, Callable[[GraphState], GraphState]], Callable[[GraphState], GraphState]],
    planner_router: Callable[[GraphState], str],
):
    return compile_graph(timed_node=timed_node, planner_router=planner_router)
