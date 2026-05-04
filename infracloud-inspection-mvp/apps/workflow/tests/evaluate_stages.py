"""
evaluate_stages.py
==================
Per-node (per-stage) evaluation of the InfraCloud Inspection pipeline.

Each graph node is evaluated in isolation by injecting gold-quality inputs
at that node's boundary. This isolates each node's error contribution
independent of upstream failures.

Stages evaluated
----------------
transcribe_audio  WER relative to gold transcript (audio mode only).
extract_fields    Intent + field accuracy using the gold transcript injected
                  directly. All errors here are pure extraction errors.
validate_catalog  Catalog validity agreement using gold extracted fields.
detect_updates    Conflict precision/recall using gold extracted fields.

The comparison between end-to-end accuracy (evaluate_dataset.py) and
per-stage accuracy pinpoints the error budget per stage:

  end-to-end field acc = 60%
  extract_fields acc   = 80%   ← gap: 20% lost to upstream transcription
  extract_fields acc   = 60%   ← problem is in the LLM, not in Whisper

Usage
-----
  python evaluate_stages.py --mode transcript
  python evaluate_stages.py --mode audio --split dev
  python evaluate_stages.py --mode transcript --cases TC001,TC039
  python evaluate_stages.py --mode transcript --stage extract_fields
  python evaluate_stages.py --mode transcript --stage validate_catalog
  python evaluate_stages.py --mode transcript --stage detect_updates

Output
------
TXT  results/<timestamp>_stage_report.txt
     Per-stage metrics table with field-level breakdown
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import traceback
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
_DATASET_DIR = _SCRIPT_DIR / "data" / "dataset"
_CASES_DIR = _DATASET_DIR / "cases"
_AUDIO_DIR = _DATASET_DIR / "audio"
_DEFAULT_RESULTS_DIR = _SCRIPT_DIR / "results"

# Re-use scoring and discovery helpers from evaluate_dataset.
sys.path.insert(0, str(_SCRIPT_DIR))
from evaluate_dataset import (  # noqa: E402
    discover_cases,
    score_conflicts,
    score_field,
    score_intent,
    word_error_rate,
)

_ALL_STAGES = ("transcribe_audio", "extract_fields", "validate_catalog", "detect_updates")

# Sentinel values in gold annotations that mean "no real value"
_NULL_SENTINELS = (None, "not_extractable", "n/a")


# ---------------------------------------------------------------------------
# Base state builder
# ---------------------------------------------------------------------------

def _make_base_state(case: dict) -> dict:
    """Minimal WorkflowState populated with the case's raw inputs."""
    return {
        "run_id": str(uuid.uuid4()),
        "suspicion_id": case["input"]["suspicion_id"],
        "existing_record": case["input"]["existing_record"],
        "audio_base64": "",
        "audio_filename": "inspection-audio.wav",
        "audio_content_type": "audio/wav",
        "transcript_override": None,
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
            "start_time": datetime.now(timezone.utc).isoformat(),
        },
        "provider": "langgraph",
        "workflow_version": "eval",
    }


def _gold_extracted_fields(case: dict) -> dict[str, Any]:
    """Return {field: value} from gold annotations, excluding null sentinels."""
    return {
        fname: entry["value"]
        for fname, entry in case["gold"].get("fields", {}).items()
        if entry.get("value") not in _NULL_SENTINELS
    }


# ---------------------------------------------------------------------------
# Stage evaluators
# ---------------------------------------------------------------------------

def eval_transcribe_audio(case: dict) -> dict:
    """
    Run Whisper on the wav file and compute WER against the gold transcript.
    Only valid in audio mode.
    """
    try:
        sys.path.insert(0, str(_SCRIPT_DIR.parent.parent))
        from apps.workflow.app.models import AudioPayload, ExtractionRequest  # type: ignore
        from apps.workflow.app.nodes import ingest_request, transcribe_audio  # type: ignore
    except ImportError as exc:
        return _error_result("transcribe_audio", case["case_id"], str(exc))

    wav_path = _AUDIO_DIR / f"{case['input']['suspicion_id']}.wav"
    if not wav_path.exists():
        return _error_result("transcribe_audio", case["case_id"], f"Audio file not found: {wav_path}")

    audio = AudioPayload(
        filename=wav_path.name,
        content_type="audio/wav",
        base64=base64.b64encode(wav_path.read_bytes()).decode(),
    )
    request = ExtractionRequest(
        suspicion_id=case["input"]["suspicion_id"],
        existing_record=case["input"]["existing_record"],
        audio=audio,
    )
    state = ingest_request(request)

    try:
        output = transcribe_audio(state)
    except Exception:
        return _error_result("transcribe_audio", case["case_id"], traceback.format_exc())

    gold_transcript: str = case["input"]["transcript"]
    actual_transcript: str = output.get("transcript") or ""
    wer = word_error_rate(gold_transcript, actual_transcript) if actual_transcript else 1.0

    return {
        "stage": "transcribe_audio",
        "case_id": case["case_id"],
        "wer": round(wer, 4),
        "passed": wer <= 0.20,
        "detected_language": output.get("detected_language"),
        "error": None,
    }


def eval_extract_fields(case: dict) -> dict:
    """
    Inject the gold transcript directly into extract_fields to measure pure
    extraction quality, bypassing Whisper.
    """
    try:
        sys.path.insert(0, str(_SCRIPT_DIR.parent.parent))
        from apps.workflow.app.nodes import extract_fields  # type: ignore
    except ImportError as exc:
        return _error_result("extract_fields", case["case_id"], str(exc))

    state = _make_base_state(case)
    state["transcript"] = case["input"]["transcript"]

    try:
        output = extract_fields(state)
    except Exception:
        return _error_result("extract_fields", case["case_id"], traceback.format_exc())

    gold = case["gold"]
    intent_correct = score_intent(gold.get("intent"), output.get("intent"))

    actual_fields: dict = output.get("extracted_fields", {})
    gold_fields: dict = gold.get("fields", {})

    field_results: list[dict] = []
    for field_name, gold_entry in gold_fields.items():
        gold_value = gold_entry.get("value")
        is_critical = bool(gold_entry.get("is_critical", False))

        actual_entry = actual_fields.get(field_name)
        actual_value = actual_entry.get("value") if isinstance(actual_entry, dict) else actual_entry

        correct, hallucination_risk = score_field(field_name, gold_value, actual_value)
        field_results.append({
            "field": field_name,
            "correct": correct,
            "hallucination_risk": hallucination_risk,
            "is_critical": is_critical,
            "gold": gold_value,
            "actual": actual_value,
        })

    return {
        "stage": "extract_fields",
        "case_id": case["case_id"],
        "intent_correct": intent_correct,
        "actual_intent": output.get("intent"),
        "gold_intent": gold.get("intent"),
        "field_results": field_results,
        "extraction_source": (output.get("diagnostics") or {}).get("extraction_source", "unknown"),
        "error": None,
    }


def eval_validate_catalog(case: dict) -> dict:
    """
    Inject gold extracted fields into validate_catalog and measure whether
    the node's catalog validity assessment matches the gold annotation.
    """
    try:
        sys.path.insert(0, str(_SCRIPT_DIR.parent.parent))
        from apps.workflow.app.nodes import validate_catalog  # type: ignore
    except ImportError as exc:
        return _error_result("validate_catalog", case["case_id"], str(exc))

    state = _make_base_state(case)
    state["extracted_fields"] = _gold_extracted_fields(case)
    state["intent"] = case["gold"].get("intent")

    try:
        output = validate_catalog(state)
    except Exception:
        return _error_result("validate_catalog", case["case_id"], traceback.format_exc())

    gold_catalog_valid: bool = case["gold"].get("catalog_valid", True)
    catalog_validation: dict = output.get("catalog_validation") or {}
    actual_catalog_valid = (
        all(v.get("catalog_match", True) for v in catalog_validation.values() if isinstance(v, dict))
        if catalog_validation
        else True
    )

    return {
        "stage": "validate_catalog",
        "case_id": case["case_id"],
        "catalog_correct": gold_catalog_valid == actual_catalog_valid,
        "gold_catalog_valid": gold_catalog_valid,
        "actual_catalog_valid": actual_catalog_valid,
        "invalid_fields": [
            k for k, v in catalog_validation.items()
            if isinstance(v, dict) and v.get("catalog_match") is False
        ],
        "error": None,
    }


def eval_detect_updates(case: dict) -> dict:
    """
    Inject gold extracted fields into detect_updates and measure conflict
    precision/recall against the gold conflict annotation.
    """
    try:
        sys.path.insert(0, str(_SCRIPT_DIR.parent.parent))
        from apps.workflow.app.nodes import detect_updates  # type: ignore
    except ImportError as exc:
        return _error_result("detect_updates", case["case_id"], str(exc))

    state = _make_base_state(case)
    state["extracted_fields"] = _gold_extracted_fields(case)
    state["intent"] = case["gold"].get("intent")

    try:
        output = detect_updates(state)
    except Exception:
        return _error_result("detect_updates", case["case_id"], traceback.format_exc())

    gold_conflicts: list = case["gold"].get("conflicts", [])
    actual_conflicts: list = output.get("conflicts", [])
    precision, recall = score_conflicts(gold_conflicts, actual_conflicts)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "stage": "detect_updates",
        "case_id": case["case_id"],
        "conflict_precision": round(precision, 4),
        "conflict_recall": round(recall, 4),
        "conflict_f1": round(f1, 4),
        "gold_conflict_fields": [c["field"] for c in gold_conflicts if "field" in c],
        "actual_conflict_fields": [c["field"] for c in actual_conflicts if "field" in c],
        "error": None,
    }


def _error_result(stage: str, case_id: str, error: str) -> dict:
    return {"stage": stage, "case_id": case_id, "error": error, "passed": False}


# ---------------------------------------------------------------------------
# Summary builder
# ---------------------------------------------------------------------------

def build_summary(results: dict[str, list[dict]], mode: str, timestamp: str) -> str:
    lines: list[str] = []

    def pct(num: int, den: int) -> str:
        return "n/a" if den == 0 else f"{100*num/den:.1f}% ({num}/{den})"

    def mean(vals: list[float]) -> str:
        return "n/a" if not vals else f"{sum(vals)/len(vals):.3f}"

    lines.append("=" * 72)
    lines.append("InfraCloud Inspection — Per-Stage Evaluation")
    lines.append(f"Mode      : {mode}")
    lines.append(f"Timestamp : {timestamp}")
    lines.append("=" * 72)

    # ── transcribe_audio ─────────────────────────────────────────────────────
    wer_results = results.get("transcribe_audio", [])
    if wer_results and mode == "audio":
        lines.append("\n[ transcribe_audio ]")
        errors = [r for r in wer_results if r.get("error")]
        valid = [r for r in wer_results if not r.get("error")]
        passed = [r for r in valid if r.get("passed")]
        wers = [r["wer"] for r in valid if "wer" in r]
        lines.append(f"  Cases         : {len(wer_results)}")
        lines.append(f"  WER pass (≤20%): {pct(len(passed), len(valid))}")
        lines.append(f"  Mean WER       : {mean(wers)}")
        if errors:
            lines.append(f"  Errors         : {len(errors)}")
        # Per-case WER
        lines.append("  Per-case WER:")
        for r in sorted(valid, key=lambda r: r["wer"], reverse=True):
            flag = " !" if not r["passed"] else ""
            lines.append(f"    {r['case_id']:<10} wer={r['wer']:.3f}{flag}")
    else:
        lines.append("\n[ transcribe_audio ] skipped (transcript mode)")

    # ── extract_fields ───────────────────────────────────────────────────────
    extract_results = results.get("extract_fields", [])
    if extract_results:
        lines.append("\n[ extract_fields  — gold transcript injected ]")
        errors = [r for r in extract_results if r.get("error")]
        valid = [r for r in extract_results if not r.get("error")]

        n_intent = sum(1 for r in valid if r.get("intent_correct"))
        lines.append(f"  Cases          : {len(extract_results)}")
        lines.append(f"  Intent accuracy: {pct(n_intent, len(valid))}")

        all_fr = [fr for r in valid for fr in r.get("field_results", [])]
        crit = [fr for fr in all_fr if fr["is_critical"]]
        opt = [fr for fr in all_fr if not fr["is_critical"]]
        nc_crit = sum(1 for fr in crit if fr["correct"])
        nc_opt = sum(1 for fr in opt if fr["correct"])
        lines.append(f"  Critical fields: {pct(nc_crit, len(crit))}")
        lines.append(f"  Optional fields: {pct(nc_opt, len(opt))}")

        by_field: dict[str, list[bool]] = defaultdict(list)
        for fr in all_fr:
            by_field[fr["field"]].append(fr["correct"])
        lines.append("  Per-field accuracy:")
        for fname in sorted(by_field):
            vals = by_field[fname]
            nc = sum(vals)
            lines.append(f"    {fname:<35} {pct(nc, len(vals))}")

        by_source: dict[str, int] = defaultdict(int)
        for r in valid:
            by_source[r.get("extraction_source", "unknown")] += 1
        lines.append("  Extraction source:")
        for src, count in sorted(by_source.items()):
            lines.append(f"    {src:<30} {count}")

        hall = [(r["case_id"], fr["field"]) for r in valid for fr in r.get("field_results", []) if fr.get("hallucination_risk")]
        lines.append(f"  Hallucination risk fields: {len(hall)}")
        for cid, field in hall:
            lines.append(f"    {cid}: {field}")

        if errors:
            lines.append(f"  Errors: {len(errors)}")

    # ── validate_catalog ─────────────────────────────────────────────────────
    cat_results = results.get("validate_catalog", [])
    if cat_results:
        lines.append("\n[ validate_catalog  — gold fields injected ]")
        errors = [r for r in cat_results if r.get("error")]
        valid = [r for r in cat_results if not r.get("error")]
        n_correct = sum(1 for r in valid if r.get("catalog_correct"))
        lines.append(f"  Cases          : {len(cat_results)}")
        lines.append(f"  Catalog agreement: {pct(n_correct, len(valid))}")
        mismatches = [r for r in valid if not r.get("catalog_correct")]
        if mismatches:
            lines.append("  Mismatches:")
            for r in mismatches:
                lines.append(f"    {r['case_id']:<10} gold={r['gold_catalog_valid']} actual={r['actual_catalog_valid']} invalid_fields={r.get('invalid_fields')}")
        if errors:
            lines.append(f"  Errors: {len(errors)}")

    # ── detect_updates ───────────────────────────────────────────────────────
    conflict_results = results.get("detect_updates", [])
    if conflict_results:
        lines.append("\n[ detect_updates  — gold fields injected ]")
        errors = [r for r in conflict_results if r.get("error")]
        valid = [r for r in conflict_results if not r.get("error")]
        prec = [r["conflict_precision"] for r in valid]
        rec = [r["conflict_recall"] for r in valid]
        f1s = [r["conflict_f1"] for r in valid]
        lines.append(f"  Cases          : {len(conflict_results)}")
        lines.append(f"  Mean precision : {mean(prec)}")
        lines.append(f"  Mean recall    : {mean(rec)}")
        lines.append(f"  Mean F1        : {mean(f1s)}")
        lines.append("  Per-case F1:")
        for r in sorted(valid, key=lambda r: r["conflict_f1"]):
            flag = " !" if r["conflict_f1"] < 0.5 else ""
            lines.append(f"    {r['case_id']:<10} f1={r['conflict_f1']:.3f}  gold={r.get('gold_conflict_fields')} actual={r.get('actual_conflict_fields')}{flag}")
        if errors:
            lines.append(f"  Errors: {len(errors)}")

    lines.append("=" * 72)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Per-stage evaluation of the InfraCloud Inspection pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode", required=True, choices=["transcript", "audio"],
        help="'transcript' injects gold transcript; 'audio' runs Whisper.",
    )
    parser.add_argument(
        "--split", default="all", choices=["dev", "test", "all"],
        help="Dataset split to evaluate (default: all).",
    )
    parser.add_argument(
        "--cases", default=None, type=str,
        help="Comma-separated case IDs, e.g. TC001,TC039.",
    )
    parser.add_argument(
        "--difficulty", default=None, choices=["easy", "medium", "hard"],
        help="Filter cases by difficulty.",
    )
    parser.add_argument(
        "--stage", default=None, choices=list(_ALL_STAGES),
        help="Evaluate a single stage only (default: all stages).",
    )
    parser.add_argument(
        "--output", default=str(_DEFAULT_RESULTS_DIR), dest="output_dir",
        help="Output directory for the report (default: tests/results/).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    case_filter = (
        [c.strip() for c in args.cases.split(",") if c.strip()]
        if args.cases else None
    )
    cases = discover_cases(
        _CASES_DIR,
        case_filter=case_filter,
        split_filter=args.split,
        difficulty_filter=args.difficulty,
    )
    if not cases:
        print("No cases matched the given filters. Exiting.")
        sys.exit(0)

    stages_to_run = (args.stage,) if args.stage else _ALL_STAGES
    print(f"Evaluating {len(cases)} case(s) | mode={args.mode} | stages={stages_to_run}\n")

    results: dict[str, list[dict]] = {s: [] for s in stages_to_run}

    _EVALUATORS = {
        "transcribe_audio": eval_transcribe_audio,
        "extract_fields": eval_extract_fields,
        "validate_catalog": eval_validate_catalog,
        "detect_updates": eval_detect_updates,
    }

    for case in cases:
        cid = case["case_id"]
        scenario = case.get("scenario", "")
        difficulty = case.get("difficulty", "")
        print(f"  {cid}  ({scenario}, {difficulty})")

        for stage in stages_to_run:
            if stage == "transcribe_audio" and args.mode == "transcript":
                continue  # Whisper bypass — nothing to measure
            evaluator = _EVALUATORS[stage]
            result = evaluator(case)
            if result.get("error"):
                print(f"    [{stage}] ERROR: {result['error'][:80]}", file=sys.stderr)
            results[stage].append(result)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / f"{timestamp}_stage_report.txt"
    summary = build_summary(results, mode=args.mode, timestamp=timestamp)
    report_path.write_text(summary, encoding="utf-8")
    print(f"\nReport written: {report_path}")
    print("\n" + summary)


if __name__ == "__main__":
    main()
