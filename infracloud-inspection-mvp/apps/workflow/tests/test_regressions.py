from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from apps.workflow.app.graph import run_graph
from apps.workflow.app.models import ExtractionRequest
from apps.workflow.app.nodes import (
    check_audio_quality,
    extract_fields,
    ingest_request,
    validate_catalog,
)


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_fixture(name: str) -> ExtractionRequest:
    data = json.loads((FIXTURES_DIR / name).read_text())
    return ExtractionRequest.model_validate(data)


def test_golden_fixture_crack_validation():
    response = run_graph(load_fixture("test1_request.json"))

    assert response.intent == "VALIDATE_DAMAGE"
    assert response.simulated_infracloud_payload["Status"] == "Damage"
    assert response.simulated_infracloud_payload["Damage Type"] == "Risse | Längsriss (trocken)"
    assert response.simulated_infracloud_payload["Class"] == "2"


def test_golden_fixture_false_positive_rejection():
    response = run_graph(load_fixture("test2_request.json"))

    assert response.intent == "REJECT_DAMAGE"
    assert response.simulated_infracloud_payload["Status"] == "Incorrectly detected"


def test_golden_fixture_material_conflict():
    response = run_graph(load_fixture("test3_request.json"))

    assert response.intent == "UPDATE_FIELD"
    assert response.simulated_infracloud_payload["Material"] == "Metall | unlegierten Stahl"
    assert response.simulated_infracloud_payload["Damage Type"] == "Stahl | Verrostet"


def test_empty_transcript_marks_low_confidence_and_unsure():
    state = ingest_request(
        ExtractionRequest(
            suspicion_id="14499",
            existing_record={"ID": 14499, "Status": "Suspicion"},
            transcript_override="",
        )
    )
    state["transcript"] = ""
    state = check_audio_quality(state)
    state = extract_fields(state)

    assert state["audio_quality_flag"] == "low_confidence"
    assert state["intent"] == "UNSURE"


def test_malformed_existing_record_is_rejected():
    with pytest.raises(ValidationError):
        ExtractionRequest.model_validate(
            {
                "suspicion_id": "14401",
                "existing_record": ["not", "a", "record"],
            }
        )


def test_invalid_catalog_value_is_flagged():
    state = ingest_request(
        ExtractionRequest(
            suspicion_id="14401",
            existing_record={"ID": 14401, "Status": "Suspicion"},
        )
    )
    state["extracted_fields"] = {
        "Status": "Damage",
        "Damage Type": "Invalid damage value",
    }

    result = validate_catalog(state)

    assert result["catalog_validation"]["Damage Type"]["catalog_match"] is False


def test_conflicting_material_damage_type_marks_cascade_invalid():
    state = ingest_request(
        ExtractionRequest(
            suspicion_id="14403",
            existing_record={"ID": 14403, "Status": "Suspicion"},
        )
    )
    state["extracted_fields"] = {
        "Material": "Beton | Stahlbeton",
        "Damage Type": "Stahl | Verrostet",
    }

    result = validate_catalog(state)

    assert result["catalog_validation"]["Damage Type"]["catalog_match"] is True
    assert result["catalog_validation"]["Damage Type"]["cascade_valid"] is False


def test_create_new_skips_detect_updates_and_produces_draft():
    """CREATE_NEW cases: detect_updates stage should remain 'pending' (skipped), no conflicts."""
    skeleton_record = {
        "Suspicion ID": "TC039",
        "Asset": "Hafen Kiel",
        "Part": "Kaje",
        "Status": "Suspicion",
        "Material": None,
        "Damage Type": None,
        "Class": None,
        "Length": None,
        "Width": None,
        "Depth": None,
        "Quantity": None,
        "Location Longitudinal": None,
        "Location Cross Section": None,
        "Location Height": None,
        "Damage description": None,
        "Remark": None,
        "Note": None,
    }
    response = run_graph(
        ExtractionRequest(
            suspicion_id="TC039",
            existing_record=skeleton_record,
            transcript_override=(
                "Hier ist ein neuer Schaden. Betonriss, trocken. "
                "Klasse zwei. Länge dreißig Zentimeter."
            ),
        )
    )

    assert response.intent == "CREATE_NEW"
    assert response.conflicts == []
    assert response.diagnostics.stages["detect_updates"] == "pending"
    assert response.simulated_infracloud_payload.get("Status") == "Damage"
