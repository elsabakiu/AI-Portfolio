"""
Generate the three test WAV files for the InfraCloud Inspection Pipeline PoC.

Uses OpenAI TTS (tts-1, voice: onyx) to synthesise German field inspection audio.
Output files are saved in the current working directory.

Usage:
    python generate_test_audio.py
"""

import os
import sys
import json
import ssl
import urllib.error
import urllib.request


def load_local_env(env_path: str = ".env") -> None:
    """Load simple KEY=VALUE pairs from a local .env file."""
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if (
                len(value) >= 2
                and value[0] == value[-1]
                and value[0] in {'"', "'"}
            ):
                value = value[1:-1]

            os.environ.setdefault(key, value)


load_local_env()

try:
    import certifi
except ImportError:
    certifi = None

API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    print("ERROR: OPENAI_API_KEY is not set.")
    print("  Option 1: copy .env.example to .env and add your key")
    print("  Option 2: export OPENAI_API_KEY=sk-...")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def build_ssl_context() -> ssl.SSLContext | None:
    """Prefer certifi's CA bundle when available for pyenv/macOS setups."""
    if certifi is None:
        return None
    return ssl.create_default_context(cafile=certifi.where())

# Test scripts — German field inspection narrations
SCRIPTS = {
    "test1.wav": (
        "Schaden bestätigt. Längsriss, trocken. "
        "Rissbreite eineinhalb Millimeter, also Klasse zwei. "
        "Länge dreißig Zentimeter, Breite zwei Zentimeter. "
        "Der Riss ist trocken, keine Feuchtigkeit sichtbar. "
        "Menge: vereinzelt."
    ),
    "test2.wav": (
        "Das ist kein Schaden. "
        "Wurde vom Büro als Verdacht eingetragen, aber vor Ort nichts zu sehen. "
        "Bitte als fehlerhaft erkannt markieren."
    ),
    "test3.wav": (
        "Achtung, das ist eigentlich Stahlkorrosion, kein Betonschaden. "
        "Das Material ist unlegierten Stahl, nicht Beton. "
        "Klasse drei. "
        "Ungefähr fünfzehn Zentimeter lang. "
        "Oberfläche feucht und fortschreitend. "
        "Externen Gutachter einschalten."
    ),
}

# Expected pipeline outputs (for reference)
EXPECTED = {
    "test1.wav": "intent=VALIDATE_DAMAGE | Status=Damage | DamageType=Risse | Längsriss (trocken) | Class=2",
    "test2.wav": "intent=REJECT_DAMAGE | Status=Incorrectly detected | all measurements null",
    "test3.wav": "intent=UPDATE_FIELD | Material=Metall | unlegierten Stahl | DamageType=Stahl | Verrostet | conflicts=[Material, DamageType]",
}


def generate_wav(filename: str, text: str) -> None:
    print(f"Generating {filename}...")
    payload = json.dumps(
        {
            "model": "tts-1",
            "input": text,
            "voice": "onyx",
            "response_format": "wav",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=payload,
        headers=HEADERS,
        method="POST",
    )
    ssl_context = build_ssl_context()
    try:
        with urllib.request.urlopen(request, timeout=60, context=ssl_context) as resp:
            audio_bytes = resp.read()
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"ERROR: OpenAI API request failed with HTTP {exc.code}.")
        print(error_body)
        sys.exit(1)
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLCertVerificationError):
            print("ERROR: TLS certificate verification failed for api.openai.com.")
            print("  This Python installation does not trust a valid CA bundle.")
            print("  Try one of these fixes:")
            print("  1. Ensure certifi is installed in this interpreter: pip install certifi")
            print("  2. Re-run this script after updating your Python certificates")
            sys.exit(1)
        print(f"ERROR: Could not reach OpenAI API: {exc.reason}")
        sys.exit(1)

    with open(filename, "wb") as f:
        f.write(audio_bytes)
    size_kb = len(audio_bytes) / 1024
    print(f"  Saved {filename} ({size_kb:.1f} KB)")
    print(f"  Expected pipeline output: {EXPECTED[filename]}")


def main() -> None:
    print("InfraCloud Inspection — Test WAV Generator")
    print("=" * 50)
    for filename, text in SCRIPTS.items():
        generate_wav(filename, text)
    print()
    print("Done. 3 WAV files ready.")
    print()
    print("Next: test the local LangGraph-backed API with:")
    print('  curl -X POST "http://127.0.0.1:8787/api/extract" \\')
    print('    -H "x-user-id: reviewer-1" \\')
    print('    -H "x-user-role: reviewer" \\')
    print('    -F "audio_file=@test1.wav" \\')
    print('    -F "suspicion_id=14401" \\')
    print('    -F "existing_record=$(cat apps/web/public/records/test1_existing_record.json)"')


if __name__ == "__main__":
    main()
