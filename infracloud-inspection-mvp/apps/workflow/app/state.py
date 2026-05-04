from __future__ import annotations

from typing import Any, TypedDict


class WorkflowState(TypedDict, total=False):
    run_id: str
    suspicion_id: str
    existing_record: dict[str, Any]
    audio_base64: str
    audio_filename: str
    audio_content_type: str
    transcript_override: str | None
    transcript: str | None
    detected_language: str | None
    audio_quality_flag: str | None
    rerecord_suggestion: str | None
    word_count: int
    intent: str | None
    extracted_fields: dict[str, Any]
    confidence: dict[str, float | str]
    catalog_validation: dict[str, Any]
    conflicts: list[dict[str, Any]]
    simulated_infracloud_payload: dict[str, Any]
    warnings: list[dict[str, Any]]
    diagnostics: dict[str, Any]
    langsmith_run_id: str | None
    provider: str
    workflow_version: str
    error: dict[str, Any] | None
