from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AudioPayload(BaseModel):
    filename: str
    content_type: str
    base64: str


class ExtractionRequest(BaseModel):
    suspicion_id: str
    existing_record: dict[str, Any]
    audio: AudioPayload | None = None
    transcript_override: str | None = None


class WorkflowWarning(BaseModel):
    type: str
    stage: str
    message: str
    node: str | None = None
    word_count: int | None = None


class Conflict(BaseModel):
    field: str
    existing_value: Any
    extracted_value: Any
    proposed_resolution: str


class WorkflowDiagnostics(BaseModel):
    stages: dict[str, str]
    start_time: str | None = None
    extraction_source: str | None = None  # "llm" | "heuristic" | "cached_existing_record"


class ExtractionResponse(BaseModel):
    run_id: str
    suspicion_id: str
    transcript: str | None = None
    audio_quality_flag: str | None = None
    rerecord_suggestion: str | None = None
    word_count: int | None = None
    intent: str | None = None
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    confidence: dict[str, float | str] = Field(default_factory=dict)
    catalog_validation: dict[str, Any] = Field(default_factory=dict)
    partial_catalog: bool = True
    conflicts: list[Conflict] = Field(default_factory=list)
    warnings: list[WorkflowWarning] = Field(default_factory=list)
    diagnostics: WorkflowDiagnostics
    langsmith_run_id: str | None = None
    simulated_infracloud_payload: dict[str, Any] = Field(default_factory=dict)
    provider: str = "langgraph"
    workflow_version: str
    created_at: datetime


class ExtractionEnvelope(BaseModel):
    ok: bool = True
    data: ExtractionResponse


class PersistedExtraction(BaseModel):
    run_id: str
    data: ExtractionResponse


class DraftCommand(BaseModel):
    suspicion_id: str
    proposal: dict[str, Any]


class SubmissionCommand(BaseModel):
    suspicion_id: str
    proposal: dict[str, Any]


class AckEnvelope(BaseModel):
    ok: bool = True
    message: str
