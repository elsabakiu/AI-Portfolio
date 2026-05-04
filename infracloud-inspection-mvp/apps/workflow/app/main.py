from __future__ import annotations

from time import perf_counter

from fastapi import FastAPI, HTTPException, Response

from .graph import run_graph
from .logger import logger
from .metrics import metrics
from .models import (
    AckEnvelope,
    DraftCommand,
    ExtractionEnvelope,
    ExtractionRequest,
    SubmissionCommand,
)
from .observability import capture_exception, init_sentry

app = FastAPI(title="InfraCloud LangGraph Workflow Service", version="0.1.0")
init_sentry()
metrics.set_gauge("workflow_readiness", 1)


@app.get("/health")
def health():
    return {"ok": True, "service": "workflow", "provider": "langgraph"}


@app.get("/ready")
def ready():
    return {
        "ok": True,
        "ready": True,
        "service": "workflow",
        "provider": "langgraph",
    }


@app.get("/metrics")
def metrics_endpoint():
    return Response(metrics.render(), media_type="text/plain; version=0.0.4")


@app.post("/v1/extractions", response_model=ExtractionEnvelope)
def create_extraction(request: ExtractionRequest):
    started_at = perf_counter()
    try:
        response = run_graph(request)
        metrics.observe(
            "workflow_request_latency_ms",
            round((perf_counter() - started_at) * 1000, 2),
            {"route": "/v1/extractions", "status": "succeeded"},
        )
        return ExtractionEnvelope(data=response)
    except Exception as exc:
        metrics.increment("workflow_request_failures", {"route": "/v1/extractions"})
        metrics.observe(
            "workflow_request_latency_ms",
            round((perf_counter() - started_at) * 1000, 2),
            {"route": "/v1/extractions", "status": "failed"},
        )
        capture_exception(
            exc,
            stage="workflow_request",
            suspicion_id=request.suspicion_id,
        )
        logger.error(
            "Workflow extraction request failed",
            stage="workflow_request",
            suspicion_id=request.suspicion_id,
            error=exc,
        )
        raise


@app.get("/v1/extractions/{run_id}")
def get_extraction(run_id: str):
    raise HTTPException(
        status_code=501,
        detail=(
            "Workflow results are persisted by the Node API service. "
            "Use the API extraction lookup endpoint instead."
        ),
    )


@app.post("/v1/drafts", response_model=AckEnvelope)
def create_draft(command: DraftCommand):
    return AckEnvelope(
        message=(
            f"Draft command accepted for suspicion {command.suspicion_id}. "
            "Persistence is owned by the API service."
        )
    )


@app.post("/v1/submissions", response_model=AckEnvelope)
def create_submission(command: SubmissionCommand):
    return AckEnvelope(
        message=(
            f"Submission command accepted for suspicion {command.suspicion_id}. "
            "Persistence is owned by the API service."
        )
    )
