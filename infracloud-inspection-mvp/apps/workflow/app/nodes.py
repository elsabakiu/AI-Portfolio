from __future__ import annotations

import base64
import uuid
from datetime import datetime, timezone
from functools import wraps
from time import perf_counter
from typing import Any

from .ai import (
    extract_fields_with_openai,
    get_langsmith_run_id,
    transcribe_audio_with_openai,
)
from .catalog import (
    VALID_CLASSES,
    VALID_DAMAGE_TYPES,
    VALID_MATERIALS,
    VALID_MATERIAL_DAMAGE_TYPE_COMBOS,
    VALID_OPTIONAL_REMARKS,
    VALID_QUANTITIES,
    VALID_STATUSES,
)
from .config import settings
from .logger import logger
from .metrics import metrics
from .models import ExtractionRequest, ExtractionResponse
from .observability import add_breadcrumb, capture_exception, set_context_tags
from .state import WorkflowState


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decode_audio_base64(audio_base64: str | None) -> bytes:
    if not audio_base64:
        return b""
    return base64.b64decode(audio_base64.encode("utf-8"))


def _build_warning(stage: str, message: str, **extra: Any) -> dict[str, Any]:
    warning = {
        "type": "warning",
        "stage": stage,
        "message": message,
    }
    warning.update(extra)
    return warning


def observed_node(stage: str):
    def decorator(func):
        @wraps(func)
        def wrapper(state: WorkflowState) -> WorkflowState:
            suspicion_id = state.get("suspicion_id")
            run_id = state.get("run_id")
            started_at = perf_counter()

            metrics.increment("workflow_node_calls", {"stage": stage})
            add_breadcrumb(
                f"Entering workflow node {stage}",
                "workflow.node",
                stage=stage,
                suspicion_id=suspicion_id,
                run_id=run_id,
            )
            set_context_tags(
                stage=stage,
                suspicion_id=suspicion_id,
                run_id=run_id,
                workflow_version=state.get("workflow_version"),
            )

            logger.info(
                "Workflow node started",
                stage=stage,
                suspicion_id=suspicion_id,
                run_id=run_id,
            )

            try:
                next_state = func(state)
                duration_ms = round((perf_counter() - started_at) * 1000, 2)
                metrics.observe("workflow_node_duration_ms", duration_ms, {"stage": stage})
                logger.info(
                    "Workflow node completed",
                    stage=stage,
                    suspicion_id=suspicion_id,
                    run_id=run_id,
                    duration_ms=duration_ms,
                )
                return next_state
            except Exception as exc:
                duration_ms = round((perf_counter() - started_at) * 1000, 2)
                metrics.increment("workflow_node_failures", {"stage": stage})
                metrics.observe("workflow_node_duration_ms", duration_ms, {"stage": stage})
                capture_exception(
                    exc,
                    stage=stage,
                    suspicion_id=suspicion_id,
                    run_id=run_id,
                    workflow_version=state.get("workflow_version"),
                )
                logger.error(
                    "Workflow node failed",
                    stage=stage,
                    suspicion_id=suspicion_id,
                    run_id=run_id,
                    duration_ms=duration_ms,
                    error=exc,
                )
                raise

        return wrapper

    return decorator


def ingest_request(request: ExtractionRequest) -> WorkflowState:
    return {
        "run_id": str(uuid.uuid4()),
        "suspicion_id": request.suspicion_id,
        "existing_record": request.existing_record,
        "audio_base64": request.audio.base64 if request.audio else "",
        "audio_filename": request.audio.filename if request.audio else "inspection-audio.wav",
        "audio_content_type": request.audio.content_type if request.audio else "audio/wav",
        "transcript_override": request.transcript_override,
        "warnings": [],
        "diagnostics": {
            "stages": {
                "ingest_request": "ok",
                "transcribe_audio": "pending",
                "check_audio_quality": "pending",
                "extract_fields": "pending",
                "validate_catalog": "pending",
                "detect_updates": "pending",
                "merge_with_existing_record": "pending",
                "build_review_payload": "pending",
                "persist_run_metadata": "pending",
            },
            "start_time": now_iso(),
        },
        "provider": "langgraph",
        "workflow_version": settings.workflow_version,
    }


def _fallback_transcript_for_filename(filename: str | None) -> str:
    normalized = (filename or "").lower()
    canned_transcripts = {
        "14401.wav": (
            "Schaden bestätigt. Längsriss, trocken. Rissbreite eineinhalb Millimeter, "
            "also Klasse zwei. Länge dreißig Zentimeter, Breite zwei Zentimeter. "
            "Der Riss ist trocken, keine Feuchtigkeit sichtbar. Menge: vereinzelt."
        ),
        "14402.wav": (
            "Das ist kein Schaden. Wurde vom Büro als Verdacht eingetragen, "
            "aber vor Ort nichts zu sehen. Bitte als fehlerhaft erkannt markieren."
        ),
        "14403.wav": (
            "Achtung, das ist eigentlich Stahlkorrosion, kein Betonschaden. "
            "Das Material ist unlegierten Stahl, nicht Beton. Klasse drei. "
            "Ungefähr fünfzehn Zentimeter lang. Oberfläche feucht und fortschreitend. "
            "Externen Gutachter einschalten."
        ),
    }
    return canned_transcripts.get(
        normalized,
        "Transkript nicht verfügbar. Bitte erneute Aufnahme prüfen.",
    )


_DAMAGE_FIELDS = frozenset(
    {"Material", "Damage Type", "Class", "Length", "Width", "Depth", "Quantity"}
)


def _is_skeleton_record(existing_record: dict[str, Any]) -> bool:
    """Return True if all core damage fields are null — indicating a CREATE_NEW skeleton."""
    return all(existing_record.get(field) is None for field in _DAMAGE_FIELDS)


def _heuristic_extraction(
    transcript: str,
    existing_record: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, float]]:
    normalized = transcript.lower()
    extracted: dict[str, Any] = {}
    # Low confidence for all heuristic outputs — this is a last-resort fallback
    confidence: dict[str, float] = {}
    intent = "UPDATE_FIELD"

    if "kein schaden" in normalized or "fehlerhaft erkannt" in normalized:
        extracted["Status"] = "Incorrectly detected"
        intent = "REJECT_DAMAGE"
        confidence["Status"] = 0.2
    elif "stahlkorrosion" in normalized or "verrostet" in normalized:
        extracted.update(
            {
                "Status": "Damage",
                "Material": "Metall | unlegierten Stahl",
                "Damage Type": "Stahl | Verrostet",
                "Class": "3",
                "Length": 15,
                "Damage description": "feucht, fortschreitend",
                "Optional remark": "Engage external institute",
            }
        )
        confidence.update({field: 0.2 for field in extracted})
        # intent stays UPDATE_FIELD — steel pattern typically means material correction
    else:
        extracted.update(
            {
                "Status": "Damage",
                "Damage Type": "Risse | Längsriss (trocken)",
                "Class": "2",
                "Length": 30,
                "Width": 2,
                "Quantity": "isolated",
                "Damage description": "trocken",
            }
        )
        confidence.update({field: 0.2 for field in extracted})
        intent = "VALIDATE_DAMAGE"

    # Promote intent to CREATE_NEW when the existing record is a skeleton
    if intent not in ("REJECT_DAMAGE",) and _is_skeleton_record(existing_record):
        intent = "CREATE_NEW"

    if not extracted:
        extracted = existing_record.copy()

    return intent, extracted, confidence


@observed_node("transcribe_audio")
def transcribe_audio(state: WorkflowState) -> WorkflowState:
    transcript = state.get("transcript_override")
    if transcript:
        state["transcript"] = transcript
        state["diagnostics"]["stages"]["transcribe_audio"] = "ok"
        state["langsmith_run_id"] = state.get("langsmith_run_id") or get_langsmith_run_id()
        return state

    audio_bytes = _decode_audio_base64(state.get("audio_base64"))
    if not audio_bytes:
        state["transcript"] = _fallback_transcript_for_filename(state.get("audio_filename"))
        metrics.increment("workflow_transcription_failures", {"reason": "missing_audio"})
        state["warnings"].append(
            _build_warning(
                "transcribe_audio",
                "No audio payload was provided. Using the local fallback transcript.",
                node="transcribe_audio",
            )
        )
        state["diagnostics"]["stages"]["transcribe_audio"] = "warning"
        return state

    try:
        transcript, detected_language = transcribe_audio_with_openai(
            audio_bytes=audio_bytes,
            filename=state.get("audio_filename") or "inspection-audio.wav",
            content_type=state.get("audio_content_type") or "audio/wav",
        )
        state["transcript"] = transcript
        state["detected_language"] = detected_language
        state["diagnostics"]["stages"]["transcribe_audio"] = "ok"
    except Exception as exc:
        state["transcript"] = _fallback_transcript_for_filename(state.get("audio_filename"))
        metrics.increment("workflow_transcription_failures", {"reason": "provider_error"})
        state["warnings"].append(
            _build_warning(
                "transcribe_audio",
                "OpenAI transcription failed. Falling back to the deterministic transcript stub.",
                node="transcribe_audio",
                error=str(exc),
            )
        )
        state["diagnostics"]["stages"]["transcribe_audio"] = "warning"

    state["langsmith_run_id"] = state.get("langsmith_run_id") or get_langsmith_run_id()
    return state


@observed_node("check_audio_quality")
def check_audio_quality(state: WorkflowState) -> WorkflowState:
    transcript = (state.get("transcript") or "").strip()
    word_count = len([word for word in transcript.split() if word])
    state["word_count"] = word_count

    if word_count < 3:
        metrics.increment("workflow_low_confidence_transcripts", {})
        state["audio_quality_flag"] = "low_confidence"
        state["rerecord_suggestion"] = "Transcript is too short or empty. Please re-record this segment."
        state["warnings"].append(
            _build_warning(
                "audio_quality",
                state["rerecord_suggestion"],
                word_count=word_count,
            )
        )
        state["diagnostics"]["stages"]["check_audio_quality"] = "warning"
        return state

    # Language detection — flag if Whisper did not detect German, but do not block.
    # Inspectors may mix German and English; this is a diagnostic signal only.
    detected_language = state.get("detected_language")
    if detected_language and detected_language != "de":
        state["warnings"].append(
            _build_warning(
                "audio_quality",
                f"Whisper detected language '{detected_language}' instead of 'de'. "
                "Inspector may be using mixed German/English — extraction will proceed.",
                node="check_audio_quality",
                detected_language=detected_language,
            )
        )
        state["audio_quality_flag"] = "language_mixed_or_uncertain"
    else:
        state["audio_quality_flag"] = "ok"

    state["rerecord_suggestion"] = None
    state["diagnostics"]["stages"]["check_audio_quality"] = "ok"
    return state


@observed_node("extract_fields")
def extract_fields(state: WorkflowState) -> WorkflowState:
    transcript = (state.get("transcript") or "").strip()
    existing = state.get("existing_record", {})
    if not transcript:
        state["intent"] = "UNSURE"
        state["extracted_fields"] = {}
        state["confidence"] = {}
        state["warnings"].append(
            _build_warning(
                "extract_fields",
                "Extraction skipped because the transcript is empty.",
                node="extract_fields",
            )
        )
        state["diagnostics"]["stages"]["extract_fields"] = "warning"
        return state

    try:
        extraction = extract_fields_with_openai(
            suspicion_id=state["suspicion_id"],
            transcript=transcript,
            existing_record=existing,
        )
        state["intent"] = extraction.intent
        state["extracted_fields"] = {
            key: value
            for key, value in extraction.extracted_fields.items()
            if value is not None
        }
        state["confidence"] = extraction.confidence
        for warning_message in extraction.warnings:
            state["warnings"].append(
                _build_warning(
                    "extract_fields",
                    warning_message,
                    node="extract_fields",
                )
            )
        state["diagnostics"]["stages"]["extract_fields"] = "ok"
        state["diagnostics"]["extraction_source"] = "llm"
    except Exception as exc:
        metrics.increment("workflow_upstream_model_errors", {"stage": "extract_fields"})
        intent, extracted, confidence = _heuristic_extraction(transcript, existing)
        state["intent"] = intent
        state["extracted_fields"] = extracted
        state["confidence"] = confidence
        state["diagnostics"]["extraction_source"] = "heuristic"
        state["warnings"].append(
            _build_warning(
                "extract_fields",
                "OpenAI extraction failed after retries. Falling back to the deterministic extraction rules.",
                node="extract_fields",
                error=str(exc),
            )
        )
        state["diagnostics"]["stages"]["extract_fields"] = "warning"

    if not state.get("extracted_fields"):
        state["extracted_fields"] = existing.copy()
        state["diagnostics"]["extraction_source"] = "cached_existing_record"
        state["warnings"].append(
            _build_warning(
                "extract_fields",
                "Extraction produced no updates; using existing record values.",
                node="extract_fields",
            )
        )

    state["langsmith_run_id"] = state.get("langsmith_run_id") or get_langsmith_run_id()
    return state


@observed_node("validate_catalog")
def validate_catalog(state: WorkflowState) -> WorkflowState:
    extracted = state.get("extracted_fields", {})
    existing = state.get("existing_record", {})
    catalog_validation: dict[str, Any] = {}

    damage_type = extracted.get("Damage Type")
    material = extracted.get("Material") or existing.get("Material")
    status = extracted.get("Status")
    quantity = extracted.get("Quantity")
    cls = extracted.get("Class")
    optional_remark = extracted.get("Optional remark")

    if damage_type:
        match = damage_type in VALID_DAMAGE_TYPES
        catalog_validation["Damage Type"] = {
            "value": damage_type,
            "catalog_match": match,
        }
        if match and material and material in VALID_MATERIAL_DAMAGE_TYPE_COMBOS:
            catalog_validation["Damage Type"]["cascade_valid"] = (
                damage_type in VALID_MATERIAL_DAMAGE_TYPE_COMBOS[material]
            )

    if extracted.get("Material"):
        catalog_validation["Material"] = {
            "value": extracted["Material"],
            "catalog_match": extracted["Material"] in VALID_MATERIALS,
        }

    if status:
        catalog_validation["Status"] = {
            "value": status,
            "catalog_match": status in VALID_STATUSES,
        }

    if quantity:
        catalog_validation["Quantity"] = {
            "value": quantity,
            "catalog_match": quantity in VALID_QUANTITIES,
        }

    if cls is not None:
        catalog_validation["Class"] = {
            "value": cls,
            "catalog_match": str(cls) in VALID_CLASSES,
        }

    if optional_remark:
        catalog_validation["Optional remark"] = {
            "value": optional_remark,
            "catalog_match": optional_remark in VALID_OPTIONAL_REMARKS,
        }

    # Numeric range validation — dimensions in cm, Class must be 1/2/3
    _DIMENSION_FIELDS = ("Length", "Width", "Depth")
    for dim_field in _DIMENSION_FIELDS:
        dim_value = extracted.get(dim_field)
        if dim_value is not None:
            try:
                dim_float = float(dim_value)
                in_range = 0 <= dim_float <= 2000
            except (TypeError, ValueError):
                in_range = False
            catalog_validation[dim_field] = {
                "value": dim_value,
                "range_valid": in_range,
            }

    state["catalog_validation"] = catalog_validation
    invalid_count = sum(
        1 for item in catalog_validation.values() if item.get("catalog_match") is False
    )
    range_violations = sum(
        1 for item in catalog_validation.values() if item.get("range_valid") is False
    )
    if invalid_count:
        metrics.increment("workflow_validation_failures", {"stage": "validate_catalog"}, invalid_count)
    if range_violations:
        metrics.increment("workflow_validation_failures", {"stage": "range_check"}, range_violations)
    state["diagnostics"]["stages"]["validate_catalog"] = "ok"
    return state


@observed_node("detect_updates")
def detect_updates(state: WorkflowState) -> WorkflowState:
    extracted = state.get("extracted_fields", {})
    existing = state.get("existing_record", {})
    conflicts: list[dict[str, Any]] = []

    for field, extracted_value in extracted.items():
        existing_value = existing.get(field)
        if (
            extracted_value is not None
            and existing_value is not None
            and extracted_value != existing_value
        ):
            conflicts.append(
                {
                    "field": field,
                    "existing_value": existing_value,
                    "extracted_value": extracted_value,
                    "proposed_resolution": "Update to extracted value - reason: Inspector provided a newer on-site assessment",
                }
            )

    state["conflicts"] = conflicts
    state["diagnostics"]["stages"]["detect_updates"] = "ok"
    return state


@observed_node("merge_with_existing_record")
def merge_with_existing_record(state: WorkflowState) -> WorkflowState:
    existing = state.get("existing_record", {})
    extracted = state.get("extracted_fields", {})
    merged = dict(existing)

    for field, value in extracted.items():
        if value is not None:
            if field == "Damage description" and existing.get(field):
                merged[field] = f"{existing[field]} | {value}"
            else:
                merged[field] = value

    state["simulated_infracloud_payload"] = merged
    state["diagnostics"]["stages"]["merge_with_existing_record"] = "ok"
    return state


@observed_node("build_review_payload")
def build_review_payload(state: WorkflowState) -> WorkflowState:
    state["diagnostics"]["stages"]["build_review_payload"] = "ok"
    return state


@observed_node("persist_run_metadata")
def persist_run_metadata(state: WorkflowState) -> WorkflowState:
    state["diagnostics"]["stages"]["persist_run_metadata"] = "ok"
    return state


def to_response_model(state: WorkflowState) -> ExtractionResponse:
    return ExtractionResponse(
        run_id=state["run_id"],
        suspicion_id=state["suspicion_id"],
        transcript=state.get("transcript"),
        audio_quality_flag=state.get("audio_quality_flag"),
        rerecord_suggestion=state.get("rerecord_suggestion"),
        word_count=state.get("word_count"),
        intent=state.get("intent"),
        extracted_fields=state.get("extracted_fields", {}),
        confidence=state.get("confidence", {}),
        catalog_validation=state.get("catalog_validation", {}),
        partial_catalog=True,
        conflicts=state.get("conflicts", []),
        warnings=state.get("warnings", []),
        diagnostics=state.get("diagnostics", {}),
        langsmith_run_id=state.get("langsmith_run_id") or state["run_id"],
        simulated_infracloud_payload=state.get("simulated_infracloud_payload", {}),
        provider="langgraph",
        workflow_version=state.get("workflow_version", settings.workflow_version),
        created_at=datetime.now(timezone.utc),
    )
