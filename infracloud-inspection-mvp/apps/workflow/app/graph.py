from __future__ import annotations

from langgraph.graph import END, StateGraph

from .ai import bootstrap_tracing_environment
from .logger import logger
from .metrics import metrics
from .nodes import (
    build_review_payload,
    check_audio_quality,
    detect_updates,
    extract_fields,
    ingest_request,
    merge_with_existing_record,
    persist_run_metadata,
    to_response_model,
    transcribe_audio,
    validate_catalog,
)
from .observability import add_breadcrumb, set_context_tags
from .state import WorkflowState


def _route_after_validate_catalog(state: WorkflowState) -> str:
    """Skip detect_updates for CREATE_NEW — no conflicts possible when all existing fields are null."""
    if state.get("intent") == "CREATE_NEW":
        return "merge_with_existing_record"
    return "detect_updates"


try:
    from langsmith import traceable
    from langsmith.run_helpers import get_current_run_tree
except ImportError:  # pragma: no cover - optional at runtime
    def traceable(*_args, **_kwargs):
        def decorator(func):
            return func

        return decorator

    def get_current_run_tree():
        return None


def build_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node("transcribe_audio", transcribe_audio)
    graph.add_node("check_audio_quality", check_audio_quality)
    graph.add_node("extract_fields", extract_fields)
    graph.add_node("validate_catalog", validate_catalog)
    graph.add_node("detect_updates", detect_updates)
    graph.add_node("merge_with_existing_record", merge_with_existing_record)
    graph.add_node("build_review_payload", build_review_payload)
    graph.add_node("persist_run_metadata", persist_run_metadata)

    graph.set_entry_point("transcribe_audio")
    graph.add_edge("transcribe_audio", "check_audio_quality")
    graph.add_edge("check_audio_quality", "extract_fields")
    graph.add_edge("extract_fields", "validate_catalog")
    graph.add_conditional_edges(
        "validate_catalog",
        _route_after_validate_catalog,
        {
            "detect_updates": "detect_updates",
            "merge_with_existing_record": "merge_with_existing_record",
        },
    )
    graph.add_edge("detect_updates", "merge_with_existing_record")
    graph.add_edge("merge_with_existing_record", "build_review_payload")
    graph.add_edge("build_review_payload", "persist_run_metadata")
    graph.add_edge("persist_run_metadata", END)

    return graph.compile()


compiled_graph = build_graph()


bootstrap_tracing_environment()


@traceable(name="workflow.run_extraction_graph", run_type="chain")
def run_graph(request):
    metrics.increment("workflow_runs_started", {})
    state = ingest_request(request)
    set_context_tags(
        suspicion_id=state.get("suspicion_id"),
        run_id=state.get("run_id"),
        workflow_version=state.get("workflow_version"),
    )
    add_breadcrumb(
        "Running LangGraph extraction workflow",
        "workflow.graph",
        suspicion_id=state.get("suspicion_id"),
        run_id=state.get("run_id"),
    )
    final_state = compiled_graph.invoke(state)
    run_tree = get_current_run_tree()
    if run_tree:
        final_state["langsmith_run_id"] = str(getattr(run_tree, "id", "") or "")
    logger.info(
        "Workflow graph completed",
        suspicion_id=final_state.get("suspicion_id"),
        run_id=final_state.get("run_id"),
        langsmith_run_id=final_state.get("langsmith_run_id"),
    )
    metrics.increment("workflow_runs_completed", {"status": "succeeded"})
    return to_response_model(final_state)
