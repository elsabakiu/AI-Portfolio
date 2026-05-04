"""
evaluate_dataset.py
===================
Evaluates the InfraCloud Inspection pipeline against the labelled evaluation dataset.

Two modes
---------
transcript   Uses case["input"]["transcript"] as transcript_override, bypasses Whisper.
audio        Sends the pre-generated .wav file through the full pipeline (including Whisper).

Scoring
-------
Intent          Exact string match (case-insensitive).
Fields          Enum / string fields: exact match.
                Width / Depth:  absolute tolerance ±0.5 (cm).
                Length:         max(±10% relative, ±2 cm) absolute tolerance.
                Class:          exact match.
Catalog valid   Exact boolean match.
Conflicts       Set match on field names only (order-independent).

Output
------
CSV  results/<timestamp>_results.csv
     columns: case_id, scenario, difficulty, noise_profile, split,
              intent_correct, field_name, field_correct, is_critical,
              source_type, stage_failed

TXT  results/<timestamp>_summary.txt
     Intent accuracy overall + by scenario
     Critical field accuracy, optional field accuracy
     Catalog valid accuracy
     Conflict precision/recall
     Pass rate by difficulty
     Pass rate by noise profile
     WER per noise profile (audio mode only)
     Reviewer burden metrics

Usage
-----
  python evaluate_dataset.py --mode transcript
  python evaluate_dataset.py --mode audio --split test
  python evaluate_dataset.py --mode transcript --cases TC039,TC040
  python evaluate_dataset.py --mode transcript --difficulty hard
  python evaluate_dataset.py --mode audio --noise-profile wind_heavy --output results/
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import math
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Resolve paths relative to this script
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_DATASET_DIR = _SCRIPT_DIR / "data" / "dataset"
_CASES_DIR = _DATASET_DIR / "cases"
_AUDIO_DIR = _DATASET_DIR / "audio"
_DEFAULT_RESULTS_DIR = _SCRIPT_DIR / "results"

# Numeric tolerance constants
_WIDTH_DEPTH_TOL_ABS = 0.5   # cm
_LENGTH_TOL_REL = 0.10       # 10 %
_LENGTH_TOL_ABS_MIN = 2.0    # cm  (whichever is larger)


# ---------------------------------------------------------------------------
# Case loading helpers
# ---------------------------------------------------------------------------

def load_case(path: Path) -> dict:
    """Load and return a case dict from a JSON file."""
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def discover_cases(
    cases_dir: Path,
    case_filter: Optional[list[str]] = None,
    split_filter: Optional[str] = None,
    difficulty_filter: Optional[str] = None,
    noise_filter: Optional[str] = None,
) -> list[dict]:
    """
    Discover TC*.json case files and return a filtered, sorted list.

    Args:
        cases_dir: Directory containing case JSON files.
        case_filter: If set, include only these case IDs.
        split_filter: If set, include only cases in this split ('dev'|'test'|'all').
        difficulty_filter: If set, include only cases with this difficulty.
        noise_filter: If set, include only cases with this noise_profile.

    Returns:
        List of case dicts sorted by case_id.
    """
    paths = sorted(cases_dir.glob("TC*.json"))
    cases: list[dict] = []
    for path in paths:
        try:
            case = load_case(path)
        except json.JSONDecodeError as exc:
            print(f"  WARNING: Could not parse {path.name}: {exc}", file=sys.stderr)
            continue

        if case_filter and case.get("case_id") not in case_filter:
            continue
        if split_filter and split_filter != "all":
            if case.get("split") != split_filter:
                continue
        if difficulty_filter and case.get("difficulty") != difficulty_filter:
            continue
        if noise_filter and case.get("audio", {}).get("noise_profile") != noise_filter:
            continue
        cases.append(case)

    return cases


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def run_pipeline(
    case: dict,
    mode: str,
) -> dict:
    """
    Run the graph pipeline for a single case and return the output dict.

    In transcript mode the transcript is passed as transcript_override so
    Whisper is bypassed entirely.  In audio mode the .wav path is provided
    and the full pipeline (Whisper → nodes) is executed.

    Args:
        case: Full case dict including input and gold sections.
        mode: 'transcript' or 'audio'.

    Returns:
        Pipeline output dict.  On error the dict contains a special key
        '_pipeline_error' with the exception string.
    """
    try:
        # Dynamic import so the script can be used from any working directory
        sys.path.insert(0, str(_SCRIPT_DIR.parent.parent))  # repo root
        from apps.workflow.app.graph import run_graph  # type: ignore[import]
        from apps.workflow.app.models import AudioPayload, ExtractionRequest  # type: ignore[import]
    except ImportError as exc:
        return {"_pipeline_error": f"Could not import run_graph: {exc}"}

    suspicion_id: str = case["input"]["suspicion_id"]
    existing_record: dict = case["input"]["existing_record"]
    audio: Optional[AudioPayload] = None

    if mode == "transcript":
        transcript_override: Optional[str] = case["input"]["transcript"]
    else:
        transcript_override = None
        wav_path = _AUDIO_DIR / f"{suspicion_id}.wav"
        if not wav_path.exists():
            return {"_pipeline_error": f"Audio file not found: {wav_path}"}
        audio = AudioPayload(
            filename=wav_path.name,
            content_type="audio/wav",
            base64=base64.b64encode(wav_path.read_bytes()).decode(),
        )

    request = ExtractionRequest(
        suspicion_id=suspicion_id,
        existing_record=existing_record,
        transcript_override=transcript_override,
        audio=audio,
    )

    try:
        result = run_graph(request)
    except Exception:  # pylint: disable=broad-except
        return {"_pipeline_error": traceback.format_exc()}

    return result.model_dump()


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _numeric(value: Any) -> Optional[float]:
    """Convert a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        return None


_NOT_EXTRACTABLE = "not_extractable"
_NOT_APPLICABLE = "n/a"


def score_field(
    field_name: str,
    gold_value: Any,
    actual_value: Any,
) -> tuple[bool, bool]:
    """
    Compare a single field value using field-specific tolerance rules.

    Three-way gold value semantics:
      - null          : inspector said nothing about this field.
                        PASS iff actual is also null.
      - "not_extractable" : inspector attempted a value but it cannot be
                        reliably determined (noise, cutoff, ambiguity).
                        PASS iff actual is null (correct abstention).
                        If actual is non-null → hallucination_risk=True,
                        field_correct=False (soft, tracked separately).
      - "N/A"         : field is structurally inapplicable for this case.
                        PASS iff actual is null or "N/A".
      - any other     : exact or tolerance-based match.

    Args:
        field_name:  Name of the WSV field (e.g. 'Class', 'Length', 'Width').
        gold_value:  Expected value from the gold annotation.
        actual_value: Value produced by the pipeline.

    Returns:
        (field_correct, hallucination_risk)
        field_correct     – True if the values are considered a match.
        hallucination_risk – True when gold is "not_extractable" and the
                             model returned a non-null value (possible
                             hallucination; tracked separately from errors).
    """
    field_lower = field_name.lower()

    # --- Special sentinel handling ---

    # null: inspector said nothing
    if gold_value is None:
        correct = actual_value is None
        return correct, False

    gold_str = str(gold_value).strip().lower()

    # "not_extractable": inspector tried but value is unreliable
    if gold_str == _NOT_EXTRACTABLE:
        if actual_value is None:
            return True, False          # correct abstention
        return False, True              # model hallucinated a value

    # "N/A": field structurally inapplicable
    if gold_str == _NOT_APPLICABLE:
        if actual_value is None:
            return True, False
        actual_str = str(actual_value).strip().lower()
        return actual_str == _NOT_APPLICABLE, False

    # actual is null but gold is a real value → miss
    if actual_value is None:
        return False, False

    # --- Numeric fields with tolerance ---
    if field_lower in ("width", "depth"):
        gv = _numeric(gold_value)
        av = _numeric(actual_value)
        if gv is None or av is None:
            return str(gold_value).strip().lower() == str(actual_value).strip().lower(), False
        return abs(gv - av) <= _WIDTH_DEPTH_TOL_ABS, False

    if field_lower == "length":
        gv = _numeric(gold_value)
        av = _numeric(actual_value)
        if gv is None or av is None:
            return str(gold_value).strip().lower() == str(actual_value).strip().lower(), False
        tol = max(_LENGTH_TOL_REL * gv, _LENGTH_TOL_ABS_MIN)
        return abs(gv - av) <= tol, False

    # All other fields: exact string match (case-insensitive, stripped)
    return str(gold_value).strip().lower() == str(actual_value).strip().lower(), False


def score_intent(gold_intent: Optional[str], actual_intent: Optional[str]) -> bool:
    """Return True if intent strings match (case-insensitive, treating None == None)."""
    if gold_intent is None and actual_intent is None:
        return True
    if gold_intent is None or actual_intent is None:
        return False
    return gold_intent.strip().upper() == actual_intent.strip().upper()


def score_catalog_valid(gold: bool, actual: Any) -> bool:
    """Return True if catalog_valid values match."""
    if isinstance(actual, bool):
        return gold == actual
    if isinstance(actual, str):
        return gold == (actual.strip().lower() in ("true", "1", "yes"))
    return False


def score_conflicts(gold_conflicts: list[dict], actual_conflicts: list[dict]) -> tuple[float, float]:
    """
    Compute conflict precision and recall based on field names only.

    Args:
        gold_conflicts: List of gold conflict dicts (must have 'field' key).
        actual_conflicts: List of pipeline output conflict dicts (must have 'field' key).

    Returns:
        Tuple of (precision, recall) each in [0.0, 1.0].
    """
    gold_fields = {c["field"].strip().lower() for c in gold_conflicts if "field" in c}
    actual_fields = {c["field"].strip().lower() for c in (actual_conflicts or []) if "field" in c}

    if not actual_fields:
        precision = 1.0 if not gold_fields else 0.0
    else:
        precision = len(gold_fields & actual_fields) / len(actual_fields)

    if not gold_fields:
        recall = 1.0 if not actual_fields else 0.0
    else:
        recall = len(gold_fields & actual_fields) / len(gold_fields)

    return precision, recall


# ---------------------------------------------------------------------------
# WER helper (audio mode)
# ---------------------------------------------------------------------------

def word_error_rate(reference: str, hypothesis: str) -> float:
    """
    Compute word error rate between reference and hypothesis strings.

    Uses a simple dynamic programming Levenshtein distance on word lists.

    Args:
        reference: Gold transcript string.
        hypothesis: Whisper output transcript string.

    Returns:
        WER in [0.0, ...] (can exceed 1.0 if many insertions).
    """
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    n = len(ref_words)
    m = len(hyp_words)

    # DP table
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return dp[n][m] / n


# ---------------------------------------------------------------------------
# Evaluate a single case
# ---------------------------------------------------------------------------

def evaluate_case(
    case: dict,
    mode: str,
) -> list[dict]:
    """
    Evaluate a single case and return a list of row dicts for the CSV.

    Each row corresponds to one field evaluation result.  An extra row is
    emitted for the intent-level result (field_name='_intent').

    Args:
        case: Full case dict.
        mode: 'transcript' or 'audio'.

    Returns:
        List of row dicts with keys matching the CSV columns.
    """
    case_id = case["case_id"]
    scenario = case.get("scenario", "")
    difficulty = case.get("difficulty", "")
    noise_profile = case["audio"]["noise_profile"]
    split = case.get("split", "")
    gold = case["gold"]
    benchmark = case.get("benchmark", {})

    rows: list[dict] = []
    base = dict(
        case_id=case_id,
        scenario=scenario,
        difficulty=difficulty,
        noise_profile=noise_profile,
        split=split,
    )

    pipeline_output = run_pipeline(case, mode)

    stage_failed = ""
    if "_pipeline_error" in pipeline_output:
        stage_failed = "pipeline_error"
        error_msg = pipeline_output["_pipeline_error"]
        print(f"  PIPELINE ERROR [{case_id}]: {error_msg[:120]}", file=sys.stderr)

    # --- Intent ---
    actual_intent = pipeline_output.get("intent") if "_pipeline_error" not in pipeline_output else None
    intent_correct = score_intent(gold.get("intent"), actual_intent)
    rows.append({
        **base,
        "intent_correct": intent_correct,
        "field_name": "_intent",
        "field_correct": intent_correct,
        "is_critical": True,
        "source_type": "",
        "stage_failed": stage_failed,
    })

    # --- Fields ---
    gold_fields: dict = gold.get("fields", {})
    actual_fields: dict = pipeline_output.get("extracted_fields", {}) if "_pipeline_error" not in pipeline_output else {}

    for field_name, gold_entry in gold_fields.items():
        gold_value = gold_entry.get("value")
        source_type = gold_entry.get("source_type", "")
        is_critical = bool(gold_entry.get("is_critical", False))

        # Pipeline output field value — handle both nested dict and flat value
        actual_entry = actual_fields.get(field_name, {})
        if isinstance(actual_entry, dict):
            actual_value = actual_entry.get("value")
        else:
            actual_value = actual_entry

        field_correct, hallucination_risk = score_field(field_name, gold_value, actual_value)

        # Detect which stage failed if field is wrong
        field_stage_failed = stage_failed
        if not field_correct and not stage_failed:
            stages = (pipeline_output.get("diagnostics") or {}).get("stages", {})
            _STAGE_ORDER = [
                "transcribe_audio", "check_audio_quality", "extract_fields",
                "validate_catalog", "detect_updates", "merge_with_existing_record",
                "build_review_payload", "persist_run_metadata",
            ]
            errored = next(
                (s for s in _STAGE_ORDER if stages.get(s) not in ("ok", "pending", None)),
                None,
            )
            # If no stage errored, field inaccuracy most likely originates from extraction
            field_stage_failed = errored or "extract_fields"

        rows.append({
            **base,
            "intent_correct": intent_correct,
            "field_name": field_name,
            "field_correct": field_correct,
            "hallucination_risk": hallucination_risk,
            "is_critical": is_critical,
            "source_type": source_type,
            "stage_failed": field_stage_failed,
        })

    # --- Catalog valid ---
    gold_catalog_valid = gold.get("catalog_valid", True)
    if "_pipeline_error" not in pipeline_output:
        catalog_validation = pipeline_output.get("catalog_validation") or {}
        # Derive a single bool: True iff every validated field has catalog_match=True
        actual_catalog_valid: Optional[bool] = (
            all(v.get("catalog_match", True) for v in catalog_validation.values() if isinstance(v, dict))
            if catalog_validation
            else True  # nothing extracted → vacuously valid
        )
    else:
        actual_catalog_valid = None
    catalog_correct = score_catalog_valid(gold_catalog_valid, actual_catalog_valid)
    rows.append({
        **base,
        "intent_correct": intent_correct,
        "field_name": "_catalog_valid",
        "field_correct": catalog_correct,
        "is_critical": True,
        "source_type": "",
        "stage_failed": stage_failed,
    })

    # --- Conflicts ---
    gold_conflicts: list = gold.get("conflicts", [])
    actual_conflicts: list = pipeline_output.get("conflicts", []) if "_pipeline_error" not in pipeline_output else []
    conflict_precision, conflict_recall = score_conflicts(gold_conflicts, actual_conflicts)
    conflict_f1 = (
        2 * conflict_precision * conflict_recall / (conflict_precision + conflict_recall)
        if (conflict_precision + conflict_recall) > 0
        else 0.0
    )
    rows.append({
        **base,
        "intent_correct": intent_correct,
        "field_name": "_conflict_precision",
        "field_correct": conflict_precision >= 1.0,
        "is_critical": False,
        "source_type": f"prec={conflict_precision:.2f} rec={conflict_recall:.2f} f1={conflict_f1:.2f}",
        "stage_failed": stage_failed,
    })

    # --- WER (audio mode only) ---
    if mode == "audio" and "_pipeline_error" not in pipeline_output:
        gold_transcript = case["input"]["transcript"]
        actual_transcript = pipeline_output.get("transcript", "")
        if actual_transcript:
            wer = word_error_rate(gold_transcript, actual_transcript)
            rows.append({
                **base,
                "intent_correct": intent_correct,
                "field_name": "_wer",
                "field_correct": wer <= 0.2,  # pass threshold: WER ≤ 20%
                "is_critical": False,
                "source_type": f"wer={wer:.3f}",
                "stage_failed": stage_failed,
            })

    # --- Warning stages ---
    expected_stages: list = benchmark.get("expected_warning_stages", [])
    actual_stages: list = (
        [w["stage"] for w in pipeline_output.get("warnings", []) if isinstance(w, dict) and "stage" in w]
        if "_pipeline_error" not in pipeline_output
        else []
    )
    expected_set = {s.strip().lower() for s in expected_stages}
    actual_set = {s.strip().lower() for s in actual_stages}
    stages_match = expected_set == actual_set
    rows.append({
        **base,
        "intent_correct": intent_correct,
        "field_name": "_warning_stages",
        "field_correct": stages_match,
        "is_critical": False,
        "source_type": f"expected={sorted(expected_set)} actual={sorted(actual_set)}",
        "stage_failed": stage_failed,
    })

    return rows


# ---------------------------------------------------------------------------
# Summary report builder
# ---------------------------------------------------------------------------

def build_summary(rows: list[dict], mode: str, timestamp: str) -> str:
    """
    Build a human-readable summary report from all evaluation rows.

    Args:
        rows: All CSV row dicts collected across all evaluated cases.
        mode: 'transcript' or 'audio'.
        timestamp: Timestamp string used in the report header.

    Returns:
        Multi-line string containing the full summary report.
    """
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("InfraCloud Inspection — Evaluation Summary")
    lines.append(f"Mode      : {mode}")
    lines.append(f"Timestamp : {timestamp}")
    lines.append(f"Total rows: {len(rows)}")
    lines.append("=" * 72)

    # Helper: ratio formatter
    def pct(num: int, den: int) -> str:
        if den == 0:
            return "n/a"
        return f"{100*num/den:.1f}% ({num}/{den})"

    # --- Intent accuracy ---
    intent_rows = [r for r in rows if r["field_name"] == "_intent"]
    n_correct = sum(1 for r in intent_rows if r["field_correct"])
    lines.append(f"\nIntent Accuracy (overall): {pct(n_correct, len(intent_rows))}")

    # By scenario
    by_scenario: dict[str, list] = defaultdict(list)
    for r in intent_rows:
        by_scenario[r["scenario"]].append(r["field_correct"])
    lines.append("Intent Accuracy by scenario:")
    for scenario, vals in sorted(by_scenario.items()):
        nc = sum(vals)
        lines.append(f"  {scenario:<30} {pct(nc, len(vals))}")

    # --- Field accuracy ---
    field_rows = [r for r in rows if not r["field_name"].startswith("_")]
    critical_rows = [r for r in field_rows if r["is_critical"]]
    optional_rows = [r for r in field_rows if not r["is_critical"]]

    nc_crit = sum(1 for r in critical_rows if r["field_correct"])
    nc_opt = sum(1 for r in optional_rows if r["field_correct"])
    lines.append(f"\nCritical field accuracy : {pct(nc_crit, len(critical_rows))}")
    lines.append(f"Optional field accuracy : {pct(nc_opt, len(optional_rows))}")

    # Per-field breakdown
    by_field: dict[str, list] = defaultdict(list)
    for r in field_rows:
        by_field[r["field_name"]].append(r["field_correct"])
    lines.append("Field accuracy by name:")
    for fname, vals in sorted(by_field.items()):
        nc = sum(vals)
        lines.append(f"  {fname:<35} {pct(nc, len(vals))}")

    # --- Catalog valid ---
    cat_rows = [r for r in rows if r["field_name"] == "_catalog_valid"]
    nc_cat = sum(1 for r in cat_rows if r["field_correct"])
    lines.append(f"\nCatalog Valid accuracy : {pct(nc_cat, len(cat_rows))}")

    # --- Conflict precision/recall ---
    conf_rows = [r for r in rows if r["field_name"] == "_conflict_precision"]
    if conf_rows:
        lines.append(f"\nConflict detection (precision/recall/f1 per case):")
        for r in conf_rows:
            lines.append(f"  {r['case_id']:<10} {r['source_type']}")

    # --- Pass rate by difficulty ---
    # A case "passes" if all critical fields and intent are correct
    case_critical: dict[str, list[bool]] = defaultdict(list)
    case_difficulty: dict[str, str] = {}
    case_noise: dict[str, str] = {}
    for r in rows:
        if r["field_name"] == "_intent" or (not r["field_name"].startswith("_") and r["is_critical"]):
            case_critical[r["case_id"]].append(bool(r["field_correct"]))
        case_difficulty[r["case_id"]] = r["difficulty"]
        case_noise[r["case_id"]] = r["noise_profile"]

    case_pass: dict[str, bool] = {cid: all(vals) for cid, vals in case_critical.items()}

    by_diff: dict[str, list[bool]] = defaultdict(list)
    for cid, passed in case_pass.items():
        by_diff[case_difficulty[cid]].append(passed)

    lines.append(f"\nPass rate by difficulty:")
    for diff in ("easy", "medium", "hard"):
        vals = by_diff.get(diff, [])
        nc = sum(vals)
        lines.append(f"  {diff:<10} {pct(nc, len(vals))}")

    # --- Pass rate by noise profile ---
    by_noise: dict[str, list[bool]] = defaultdict(list)
    for cid, passed in case_pass.items():
        by_noise[case_noise[cid]].append(passed)

    lines.append(f"\nPass rate by noise profile:")
    for profile, vals in sorted(by_noise.items()):
        nc = sum(vals)
        lines.append(f"  {profile:<15} {pct(nc, len(vals))}")

    # --- WER per noise profile (audio mode only) ---
    if mode == "audio":
        wer_rows = [r for r in rows if r["field_name"] == "_wer"]
        if wer_rows:
            wer_by_profile: dict[str, list[float]] = defaultdict(list)
            for r in wer_rows:
                src = r["source_type"]
                try:
                    wer_val = float(src.split("wer=")[1])
                    wer_by_profile[r["noise_profile"]].append(wer_val)
                except (IndexError, ValueError):
                    pass
            lines.append(f"\nMean WER by noise profile (audio mode):")
            for profile, wers in sorted(wer_by_profile.items()):
                mean_wer = sum(wers) / len(wers)
                lines.append(f"  {profile:<15} {mean_wer:.3f}")

    # --- Reviewer burden ---
    # Count corrected fields per case = number of critical field rows that are NOT correct
    # Auto-accept rate = proportion of cases where all critical fields pass
    corrected_per_case: dict[str, int] = defaultdict(int)
    for r in field_rows:
        if r["is_critical"] and not r["field_correct"]:
            corrected_per_case[r["case_id"]] += 1

    all_case_ids = list(case_pass.keys())
    avg_corrections = (
        sum(corrected_per_case.values()) / len(all_case_ids) if all_case_ids else 0.0
    )
    auto_accept_count = sum(1 for cid in all_case_ids if case_pass.get(cid, False))
    auto_accept_rate = auto_accept_count / len(all_case_ids) if all_case_ids else 0.0

    lines.append(f"\nReviewer Burden:")
    lines.append(f"  Avg corrected critical fields per case : {avg_corrections:.2f}")
    lines.append(f"  Auto-accept rate (all critical pass)   : {100*auto_accept_rate:.1f}% ({auto_accept_count}/{len(all_case_ids)})")

    # --- Hallucination risk ---
    # Rows where gold="not_extractable" and model returned a non-null value
    hallucination_rows = [r for r in field_rows if r.get("hallucination_risk")]
    if hallucination_rows:
        lines.append(f"\nHallucination Risk (gold=not_extractable, model returned a value):")
        lines.append(f"  Total flagged fields : {len(hallucination_rows)}")
        by_case: dict[str, list[str]] = defaultdict(list)
        for r in hallucination_rows:
            by_case[r["case_id"]].append(r["field_name"])
        for cid in sorted(by_case):
            lines.append(f"  {cid}: {', '.join(by_case[cid])}")
    else:
        lines.append(f"\nHallucination Risk: none flagged")

    # --- Stage failure breakdown ---
    stage_counts: dict[str, int] = defaultdict(int)
    for r in rows:
        if r["stage_failed"]:
            stage_counts[r["stage_failed"]] += 1
    if stage_counts:
        lines.append(f"\nStage failure counts:")
        for stage, count in sorted(stage_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {stage:<35} {count}")

    lines.append("=" * 72)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------

_CSV_FIELDNAMES = [
    "case_id",
    "scenario",
    "difficulty",
    "noise_profile",
    "split",
    "intent_correct",
    "field_name",
    "field_correct",
    "hallucination_risk",
    "is_critical",
    "source_type",
    "stage_failed",
]


def write_csv(rows: list[dict], output_path: Path) -> None:
    """Write all evaluation rows to a CSV file.

    Args:
        rows: List of row dicts to write.
        output_path: Destination CSV path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Evaluate InfraCloud Inspection pipeline against the labelled dataset.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["transcript", "audio"],
        help="'transcript' bypasses Whisper; 'audio' uses the full pipeline.",
    )
    parser.add_argument(
        "--split",
        default="all",
        choices=["dev", "test", "all"],
        help="Which dataset split to evaluate (default: all).",
    )
    parser.add_argument(
        "--cases",
        default=None,
        type=str,
        help="Comma-separated list of specific case IDs, e.g. TC001,TC039.",
    )
    parser.add_argument(
        "--difficulty",
        default=None,
        choices=["easy", "medium", "hard"],
        help="Filter cases by difficulty level.",
    )
    parser.add_argument(
        "--noise-profile",
        default=None,
        dest="noise_profile",
        metavar="NOISE_PROFILE",
        help="Filter cases by noise profile, e.g. clean, wind_light.",
    )
    parser.add_argument(
        "--output",
        default=str(_DEFAULT_RESULTS_DIR),
        type=str,
        dest="output_dir",
        help="Directory for CSV and summary output (default: tests/results/).",
    )
    return parser


def main() -> None:
    """Entry point: discover cases, evaluate each, write CSV and summary."""
    parser = build_parser()
    args = parser.parse_args()

    case_filter: Optional[list[str]] = (
        [c.strip() for c in args.cases.split(",") if c.strip()]
        if args.cases
        else None
    )

    cases = discover_cases(
        _CASES_DIR,
        case_filter=case_filter,
        split_filter=args.split,
        difficulty_filter=args.difficulty,
        noise_filter=args.noise_profile,
    )

    if not cases:
        print("No cases matched the given filters. Exiting.")
        sys.exit(0)

    print(f"Evaluating {len(cases)} case(s) in '{args.mode}' mode...\n")

    all_rows: list[dict] = []
    for case in cases:
        print(f"  {case['case_id']}  ({case.get('scenario', '')}, {case.get('difficulty', '')})")
        rows = evaluate_case(case, mode=args.mode)
        all_rows.extend(rows)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir)

    csv_path = output_dir / f"{timestamp}_results.csv"
    summary_path = output_dir / f"{timestamp}_summary.txt"

    write_csv(all_rows, csv_path)
    print(f"\nCSV written     : {csv_path}")

    summary_text = build_summary(all_rows, mode=args.mode, timestamp=timestamp)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary_text, encoding="utf-8")
    print(f"Summary written : {summary_path}")

    print("\n" + summary_text)


if __name__ == "__main__":
    main()
