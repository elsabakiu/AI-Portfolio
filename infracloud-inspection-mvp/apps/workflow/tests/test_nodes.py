from apps.workflow.app.ai import ExtractionPayload
from apps.workflow.app.models import ExtractionRequest
from apps.workflow.app import nodes
from apps.workflow.app.nodes import (
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


def _base_request(transcript_override: str | None = None):
    return ExtractionRequest(
        suspicion_id="14401",
        existing_record={
            "ID": 14401,
            "Status": "Suspicion",
            "Material": "Beton | Stahlbeton",
            "Damage Type": None,
        },
        transcript_override=transcript_override,
    )


def test_ingest_request_creates_base_state():
    state = ingest_request(_base_request("Hallo"))
    assert state["suspicion_id"] == "14401"
    assert state["diagnostics"]["stages"]["extract_fields"] == "pending"


def test_transcribe_audio_prefers_override():
    state = ingest_request(_base_request("override transcript"))
    result = transcribe_audio(state)
    assert result["transcript"] == "override transcript"


def test_transcribe_audio_uses_openai_when_audio_is_present(monkeypatch):
    state = ingest_request(_base_request())
    state["audio_base64"] = "aGVsbG8="
    state["audio_filename"] = "sample.wav"
    state["audio_content_type"] = "audio/wav"

    monkeypatch.setattr(
        nodes,
        "transcribe_audio_with_openai",
        lambda **_kwargs: ("Vor Ort wurde ein trockener Laengsriss bestaetigt.", "de"),
    )

    result = transcribe_audio(state)
    assert result["transcript"] == "Vor Ort wurde ein trockener Laengsriss bestaetigt."
    assert result["diagnostics"]["stages"]["transcribe_audio"] == "ok"


def test_check_audio_quality_warns_on_short_transcript():
    state = ingest_request(_base_request("hi"))
    state = transcribe_audio(state)
    result = check_audio_quality(state)
    assert result["audio_quality_flag"] == "low_confidence"
    assert result["warnings"]


def test_extract_fields_for_validation_case():
    state = ingest_request(_base_request("Schaden bestätigt. Längsriss trocken."))
    state["transcript"] = "Schaden bestätigt. Längsriss trocken."
    result = extract_fields(state)
    assert result["intent"] == "VALIDATE_DAMAGE"
    assert result["extracted_fields"]["Damage Type"] == "Risse | Längsriss (trocken)"


def test_extract_fields_uses_openai_payload(monkeypatch):
    state = ingest_request(_base_request())
    state["transcript"] = "Das Material ist unlegierter Stahl mit deutlicher Korrosion."

    monkeypatch.setattr(
        nodes,
        "extract_fields_with_openai",
        lambda **_kwargs: ExtractionPayload(
            intent="UPDATE_FIELD",
            extracted_fields={
                "Status": "Damage",
                "Material": "Metall | unlegierten Stahl",
                "Damage Type": "Stahl | Verrostet",
            },
            confidence={"Status": 0.98, "Material": 0.95, "Damage Type": 0.95},
            warnings=[],
        ),
    )

    result = extract_fields(state)
    assert result["intent"] == "UPDATE_FIELD"
    assert result["extracted_fields"]["Material"] == "Metall | unlegierten Stahl"
    assert result["diagnostics"]["stages"]["extract_fields"] == "ok"


def test_validate_catalog_marks_known_values():
    state = ingest_request(_base_request())
    state["extracted_fields"] = {
        "Status": "Damage",
        "Damage Type": "Risse | Längsriss (trocken)",
    }
    result = validate_catalog(state)
    assert result["catalog_validation"]["Status"]["catalog_match"] is True


def test_detect_updates_builds_conflicts():
    state = ingest_request(_base_request())
    state["extracted_fields"] = {"Status": "Damage"}
    result = detect_updates(state)
    assert result["conflicts"][0]["field"] == "Status"


def test_merge_with_existing_record_updates_payload():
    state = ingest_request(_base_request())
    state["extracted_fields"] = {"Status": "Damage", "Length": 30}
    result = merge_with_existing_record(state)
    assert result["simulated_infracloud_payload"]["Status"] == "Damage"
    assert result["simulated_infracloud_payload"]["Length"] == 30


def test_build_review_payload_marks_stage_complete():
    state = ingest_request(_base_request())
    result = build_review_payload(state)
    assert result["diagnostics"]["stages"]["build_review_payload"] == "ok"


def test_persist_run_metadata_marks_stage_complete():
    state = ingest_request(_base_request())
    result = persist_run_metadata(state)
    assert result["diagnostics"]["stages"]["persist_run_metadata"] == "ok"


def test_heuristic_sets_create_new_for_skeleton_record():
    """Heuristic should use CREATE_NEW when all damage fields in existing_record are null."""
    from apps.workflow.app.nodes import _heuristic_extraction

    skeleton = {
        "Suspicion ID": "TC039",
        "Asset": "Hafen Kiel",
        "Status": "Suspicion",
        "Material": None,
        "Damage Type": None,
        "Class": None,
        "Length": None,
        "Width": None,
        "Depth": None,
        "Quantity": None,
    }
    intent, extracted, _ = _heuristic_extraction("Neuer Riss gefunden. Klasse zwei.", skeleton)
    assert intent == "CREATE_NEW"


def test_heuristic_does_not_create_new_for_reject():
    """REJECT_DAMAGE should not be promoted to CREATE_NEW even on a skeleton record."""
    from apps.workflow.app.nodes import _heuristic_extraction

    skeleton = {"Material": None, "Damage Type": None, "Class": None,
                "Length": None, "Width": None, "Depth": None, "Quantity": None}
    intent, _, _ = _heuristic_extraction("Kein Schaden vorhanden.", skeleton)
    assert intent == "REJECT_DAMAGE"


def test_heuristic_no_create_new_when_record_has_material():
    """Existing record with a non-null damage field should not trigger CREATE_NEW."""
    from apps.workflow.app.nodes import _heuristic_extraction

    existing = {"Material": "Beton | Stahlbeton", "Damage Type": None, "Class": None,
                "Length": None, "Width": None, "Depth": None, "Quantity": None}
    intent, _, _ = _heuristic_extraction("Längsriss bestätigt.", existing)
    assert intent != "CREATE_NEW"


def test_to_response_model_returns_typed_payload():
    state = ingest_request(_base_request("Schaden bestätigt"))
    state = transcribe_audio(state)
    state = check_audio_quality(state)
    state = extract_fields(state)
    state = validate_catalog(state)
    state = detect_updates(state)
    state = merge_with_existing_record(state)
    state = build_review_payload(state)
    state = persist_run_metadata(state)
    response = to_response_model(state)
    assert response.suspicion_id == "14401"
    assert response.provider == "langgraph"
