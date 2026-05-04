"""
generate_dataset_audio.py
=========================
Generates TTS audio for evaluation dataset cases and mixes in noise at target SNR.

Workflow per case:
  1. Read TC*.json from dataset/cases/
  2. Generate clean TTS via OpenAI TTS API (model=tts-1, voice=onyx)
  3. Save clean audio as dataset/audio/<case_id>_clean.wav
  4. Load noise sample from dataset/noise_samples/<noise_profile>.wav
  5. Mix at target snr_db using pydub
  6. Save mixed audio as dataset/audio/<case_id>.wav

Special SNR handling:
  - snr_db == 999  → clean; no noise mixing, just copy clean to final
  - snr_db < 999   → mix at the given SNR in dB

Usage examples:
  python generate_dataset_audio.py
  python generate_dataset_audio.py --force
  python generate_dataset_audio.py --cases TC039,TC040
  python generate_dataset_audio.py --profile wind_heavy
  python generate_dataset_audio.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Resolve paths relative to this script so it works from any cwd
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parents[2]
_DATASET_DIR = _SCRIPT_DIR / "data" / "dataset"
_CASES_DIR = _DATASET_DIR / "cases"
_AUDIO_DIR = _DATASET_DIR / "audio"
_NOISE_DIR = _DATASET_DIR / "noise_samples"
_ENV_PATH = _REPO_ROOT / ".env"

# OpenAI TTS settings
_TTS_MODEL = "tts-1"
_TTS_VOICE = "onyx"
_TTS_PRICE_PER_1K_CHARS = 0.015  # USD as of 2024


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_local_env() -> None:
    """Load the repo root .env for direct script execution."""
    if not _ENV_PATH.exists():
        return

    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(_ENV_PATH, override=False)


def load_case(path: Path) -> dict:
    """Load and return a case JSON file."""
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def discover_cases(
    cases_dir: Path,
    case_filter: Optional[list[str]] = None,
    profile_filter: Optional[str] = None,
) -> list[dict]:
    """
    Discover all TC*.json case files and return a filtered list of case dicts.

    Args:
        cases_dir: Directory containing case JSON files.
        case_filter: If provided, only include cases whose case_id is in this list.
        profile_filter: If provided, only include cases with this noise_profile.

    Returns:
        List of case dicts sorted by case_id.
    """
    case_paths = sorted(cases_dir.glob("TC*.json"))
    cases = []
    for path in case_paths:
        try:
            case = load_case(path)
        except json.JSONDecodeError as exc:
            print(f"  WARNING: Could not parse {path.name}: {exc}", file=sys.stderr)
            continue

        if case_filter and case.get("case_id") not in case_filter:
            continue
        if profile_filter and case.get("audio", {}).get("noise_profile") != profile_filter:
            continue
        cases.append(case)

    return cases


def mix_at_snr(speech: "AudioSegment", noise: "AudioSegment", target_snr_db: float) -> "AudioSegment":
    """
    Mix speech with noise at the given target SNR (in dB).

    The noise is looped if it is shorter than the speech, then trimmed to
    match the speech duration exactly.

    Args:
        speech: Clean speech AudioSegment.
        noise: Noise AudioSegment (will be looped/trimmed to match speech length).
        target_snr_db: Desired signal-to-noise ratio in dB.

    Returns:
        Mixed AudioSegment.
    """
    from pydub import AudioSegment  # local import so module is importable without pydub

    speech_dbfs = speech.dBFS

    # Loop noise to cover the full speech duration
    speech_ms = len(speech)
    looped_noise = noise
    while len(looped_noise) < speech_ms:
        looped_noise = looped_noise + noise
    looped_noise = looped_noise[:speech_ms]

    noise_dbfs = looped_noise.dBFS

    # Compute required noise gain to achieve target SNR
    # SNR = speech_dBFS - (noise_dBFS + gain)  →  gain = speech_dBFS - noise_dBFS - target_snr_db
    if noise_dbfs == float("-inf"):
        # Silent noise track — return speech unchanged
        return speech

    gain_db = speech_dbfs - noise_dbfs - target_snr_db
    adjusted_noise = looped_noise.apply_gain(gain_db)

    return speech.overlay(adjusted_noise)


def generate_tts(text: str, output_path: Path, dry_run: bool = False) -> int:
    """
    Generate TTS audio using OpenAI API and save to output_path as WAV.

    Args:
        text: The text to synthesise.
        output_path: Destination path for the WAV file.
        dry_run: If True, print what would happen without calling the API.

    Returns:
        Number of characters in text (used for cost estimation).
    """
    if dry_run:
        print(f"    [dry-run] Would generate TTS for {len(text)} chars → {output_path}")
        return len(text)

    try:
        import openai
    except ImportError:
        print("  ERROR: openai package not installed. Run: pip install openai", file=sys.stderr)
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print(
            "  ERROR: OPENAI_API_KEY is not set. Add it to the repo root .env or export it before running this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = openai.OpenAI()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = client.audio.speech.create(
        model=_TTS_MODEL,
        voice=_TTS_VOICE,
        input=text,
        response_format="wav",
    )
    response.stream_to_file(str(output_path))
    return len(text)


def process_case(
    case: dict,
    force: bool = False,
    dry_run: bool = False,
) -> int:
    """
    Process a single case: generate clean TTS and mix with noise.

    Args:
        case: Case dict loaded from JSON.
        force: If True, regenerate even if output files already exist.
        dry_run: If True, print actions without executing them.

    Returns:
        Character count of the transcript (for cost estimation).
    """
    case_id: str = case["case_id"]
    transcript: str = case["input"]["transcript"]
    noise_profile: str = case["audio"]["noise_profile"]
    snr_db: float = case["audio"]["snr_db"]

    clean_path = _AUDIO_DIR / f"{case_id}_clean.wav"
    final_path = _AUDIO_DIR / f"{case_id}.wav"

    print(f"Processing {case_id}  (noise={noise_profile}, snr={snr_db})")

    # --- Step 1: clean TTS ---
    if not force and clean_path.exists():
        print(f"  Skipping TTS (clean file exists): {clean_path.name}")
        char_count = len(transcript)
    else:
        print(f"  Generating TTS → {clean_path.name}")
        char_count = generate_tts(transcript, clean_path, dry_run=dry_run)

    # --- Step 2: mix or copy ---
    if not force and final_path.exists():
        print(f"  Skipping mix (final file exists): {final_path.name}")
        return char_count

    if snr_db == 999:
        # Clean audio — no mixing needed
        if dry_run:
            print(f"    [dry-run] Would copy {clean_path.name} → {final_path.name}")
        else:
            import shutil
            _AUDIO_DIR.mkdir(parents=True, exist_ok=True)
            if clean_path.exists():
                shutil.copy2(clean_path, final_path)
                print(f"  Copied clean audio → {final_path.name}")
            else:
                print(f"  WARNING: Clean file not found, skipping copy: {clean_path}", file=sys.stderr)
        return char_count

    # Noise mixing
    noise_path = _NOISE_DIR / f"{noise_profile}.wav"
    if dry_run:
        print(f"    [dry-run] Would mix {clean_path.name} + {noise_path.name} at SNR={snr_db} dB → {final_path.name}")
        return char_count

    try:
        from pydub import AudioSegment
    except ImportError:
        print("  ERROR: pydub package not installed. Run: pip install pydub", file=sys.stderr)
        sys.exit(1)

    if not clean_path.exists():
        print(f"  WARNING: Clean audio not found, skipping mix: {clean_path}", file=sys.stderr)
        return char_count

    if not noise_path.exists():
        print(f"  WARNING: Noise sample not found for profile '{noise_profile}': {noise_path}", file=sys.stderr)
        return char_count

    speech = AudioSegment.from_wav(str(clean_path))
    noise = AudioSegment.from_wav(str(noise_path))

    mixed = mix_at_snr(speech, noise, snr_db)

    _AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    mixed.export(str(final_path), format="wav")
    print(f"  Mixed audio saved → {final_path.name}")

    return char_count


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate TTS audio for InfraCloud Inspection evaluation dataset.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate all audio files even if they already exist.",
    )
    parser.add_argument(
        "--cases",
        type=str,
        default=None,
        help="Comma-separated list of case IDs to process, e.g. TC001,TC002.",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        dest="profile",
        metavar="NOISE_PROFILE",
        help="Only process cases with this noise profile, e.g. wind_heavy.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without generating any audio.",
    )
    return parser


def main() -> None:
    """Entry point: parse CLI args, discover cases, process each, print cost estimate."""
    load_local_env()

    parser = build_parser()
    args = parser.parse_args()

    case_filter: Optional[list[str]] = (
        [c.strip() for c in args.cases.split(",") if c.strip()]
        if args.cases
        else None
    )

    cases = discover_cases(_CASES_DIR, case_filter=case_filter, profile_filter=args.profile)

    if not cases:
        print("No cases matched the given filters. Exiting.")
        sys.exit(0)

    print(f"Found {len(cases)} case(s) to process.\n")

    total_chars = 0
    for case in cases:
        try:
            chars = process_case(case, force=args.force, dry_run=args.dry_run)
            total_chars += chars
        except Exception as exc:  # pylint: disable=broad-except
            print(f"  ERROR processing {case.get('case_id', '?')}: {exc}", file=sys.stderr)

    # Cost estimate
    estimated_cost_usd = (total_chars / 1000) * _TTS_PRICE_PER_1K_CHARS
    print(f"\n--- Cost estimate ---")
    print(f"Total characters : {total_chars:,}")
    print(f"TTS model        : {_TTS_MODEL} ({_TTS_VOICE})")
    print(f"Rate             : ${_TTS_PRICE_PER_1K_CHARS:.4f} per 1k chars")
    print(f"Estimated cost   : ${estimated_cost_usd:.4f} USD")

    if args.dry_run:
        print("\n[dry-run mode — no files were written]")


if __name__ == "__main__":
    main()
