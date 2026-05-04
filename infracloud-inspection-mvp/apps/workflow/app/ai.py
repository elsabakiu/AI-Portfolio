from __future__ import annotations

import json
import os
from io import BytesIO
from functools import lru_cache
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from .catalog import (
    VALID_CLASSES,
    VALID_DAMAGE_TYPES,
    VALID_MATERIALS,
    VALID_OPTIONAL_REMARKS,
    VALID_QUANTITIES,
    VALID_STATUSES,
)
from .config import settings
from .observability import add_breadcrumb, capture_exception, set_context_tags

try:
    from langsmith import traceable
    from langsmith.run_helpers import get_current_run_tree
    from langsmith.wrappers import wrap_openai
except ImportError:  # pragma: no cover - optional at runtime
    def traceable(*_args, **_kwargs):
        def decorator(func):
            return func

        return decorator

    def get_current_run_tree():
        return None

    def wrap_openai(client):
        return client


class ExtractionPayload(BaseModel):
    # Valid intent values: VALIDATE_DAMAGE | REJECT_DAMAGE | UPDATE_FIELD | CREATE_NEW | UNSURE
    intent: str = "UPDATE_FIELD"
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    confidence: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


TRANSCRIPTION_PROMPT = (
    "Transcribe this civil-infrastructure inspection voice memo accurately. "
    "The inspector may speak German, English, or a mix of both. "
    "Keep measurements, condition details, and negations exactly as spoken."
)


EXTRACTION_SYSTEM_PROMPT = f"""
You are extracting structured fields from civil-infrastructure inspection voice notes.
The inspector may speak German, English, or a mix of both — extract field values regardless of language.

Return valid JSON only with this shape:
{{
  "intent": "UPDATE_FIELD" | "VALIDATE_DAMAGE" | "REJECT_DAMAGE" | "CREATE_NEW" | "UNSURE",
  "extracted_fields": {{
    "Status": string | null,
    "Material": string | null,
    "Damage Type": string | null,
    "Class": string | null,
    "Length": number | null,
    "Width": number | null,
    "Depth": number | null,
    "Quantity": string | null,
    "Damage description": string | null,
    "Optional remark": string | null,
    "Danger to life and health": boolean | null,
    "Immediate measures": string | null,
    "Old Damage": boolean | null,
    "Note": string | null,
    "Text": string | null,
    "Long Location": string | null,
    "Cross Location": string | null,
    "Height Location": string | null
  }},
  "confidence": {{
    "<field name>": number between 0 and 1
  }},
  "warnings": [string]
}}

Intent rules:
- VALIDATE_DAMAGE: inspector confirms the damage exists and provides or confirms field values.
- REJECT_DAMAGE: inspector says there is no damage on site. Set Status to "Incorrectly detected".
- UPDATE_FIELD: inspector corrects one or more field values that differ from the existing record.
- CREATE_NEW: inspector describes a new damage where all existing damage fields are null. Set Status to "Damage".
- UNSURE: intent cannot be determined, or the inspector describes multiple distinct damages.

Field rules:
- Use only these Status values: {", ".join(VALID_STATUSES)}
- Use only these Material values when known: {", ".join(VALID_MATERIALS)}
- Use only these Damage Type values when known: {", ".join(VALID_DAMAGE_TYPES)}
- Use only these Quantity values when known: {", ".join(VALID_QUANTITIES)}
- Use only these Class values when known: {", ".join(VALID_CLASSES)}
- Use only these Optional remark values when known: {", ".join(VALID_OPTIONAL_REMARKS)}
- All dimension fields (Length, Width, Depth) are plain numbers in centimetres without units.
  Convert: mm → divide by 10, m → multiply by 100. If no unit is stated, assume cm.
- "Danger to life and health": true if the inspector uses words like gefährlich, akut, lebensgefährlich, life-threatening.
- "Old Damage": true if the inspector says schon bekannt, schon länger da, Altschaden, existing damage.
- "Long Location": extract the verbal longitudinal position (e.g. links, rechts, Mitte, left, right).
- "Cross Location": extract the verbal cross-section position reference.
- "Height Location": extract the verbal height position reference.
- "Damage description" should be short and factual.
- Prefer null over guessing.
- Confidence values should be provided only for fields that were actually inferred.
""".strip()


def _coerce_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text_value = item.get("text")
                if text_value:
                    parts.append(str(text_value))
            else:
                text_value = getattr(item, "text", None)
                if text_value:
                    parts.append(str(text_value))
        return "\n".join(parts).strip()

    return str(content or "").strip()


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured for the workflow service.")

    client = OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.openai_timeout_seconds,
    )
    if settings.langsmith_tracing and settings.langsmith_api_key:
        return wrap_openai(client)
    return client


def get_langsmith_run_id() -> str | None:
    run_tree = get_current_run_tree()
    if not run_tree:
        return None
    return str(getattr(run_tree, "id", None) or "")


@traceable(name="workflow.transcribe_audio", run_type="llm")
def transcribe_audio_with_openai(
    *,
    audio_bytes: bytes,
    filename: str,
    content_type: str,
) -> tuple[str, str | None]:
    """Return (transcript, detected_language). detected_language may be None if not available."""
    client = get_openai_client()
    add_breadcrumb(
        "Calling OpenAI transcription model",
        "openai",
        model=settings.openai_transcription_model,
        filename=filename,
    )
    set_context_tags(model=settings.openai_transcription_model)
    response = client.audio.transcriptions.create(
        model=settings.openai_transcription_model,
        file=(filename, BytesIO(audio_bytes), content_type),
        response_format="verbose_json",
        prompt=TRANSCRIPTION_PROMPT,
    )
    transcript = getattr(response, "text", None) or getattr(response, "transcript", None)
    detected_language = getattr(response, "language", None)
    if transcript:
        return transcript.strip(), detected_language
    error = RuntimeError("OpenAI transcription returned an empty transcript.")
    capture_exception(error, stage="transcribe_audio", model=settings.openai_transcription_model)
    raise error


def _sanitize_existing_record(record: dict[str, Any]) -> dict[str, Any]:
    """Truncate long strings and strip newlines to prevent prompt injection via existing_record."""
    sanitized: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, str):
            value = value.replace("\n", " ").replace("\r", " ")[:200]
        sanitized[key] = value
    return sanitized


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
@traceable(name="workflow.extract_fields", run_type="llm")
def extract_fields_with_openai(
    *,
    suspicion_id: str,
    transcript: str,
    existing_record: dict[str, Any],
) -> ExtractionPayload:
    client = get_openai_client()
    add_breadcrumb(
        "Calling OpenAI extraction model",
        "openai",
        model=settings.openai_model,
        suspicion_id=suspicion_id,
    )
    set_context_tags(model=settings.openai_model, suspicion_id=suspicion_id)
    user_prompt = json.dumps(
        {
            "suspicion_id": suspicion_id,
            "transcript": transcript,
            "existing_record": _sanitize_existing_record(existing_record),
        },
        ensure_ascii=False,
        indent=2,
    )
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = _coerce_content_to_text(response.choices[0].message.content)
    if not content:
        error = RuntimeError("OpenAI extraction returned an empty response.")
        capture_exception(error, stage="extract_fields", model=settings.openai_model)
        raise error

    return ExtractionPayload.model_validate_json(content)


def bootstrap_tracing_environment() -> None:
    if settings.langsmith_api_key:
        os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)

    os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)
    os.environ.setdefault(
        "LANGSMITH_TRACING",
        "true" if settings.langsmith_tracing else "false",
    )
