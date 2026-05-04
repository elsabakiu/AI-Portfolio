"""
Generate synthetic noise sample .wav files for the InfraCloud Inspection dataset.

These loops are used by generate_dataset_audio.py to mix background noise
into clean TTS speech at a specified SNR level.

Each file is ~15 seconds at 16kHz mono (matching Whisper's expected input format).

Usage:
    python generate_noise_samples.py
    python generate_noise_samples.py --output path/to/noise_samples/
    python generate_noise_samples.py --sample-rate 44100 --duration 30
"""

from __future__ import annotations

import argparse
import struct
import wave
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_SAMPLE_RATE = 16_000   # Hz — matches Whisper preferred input
DEFAULT_DURATION = 15           # seconds per loop
DEFAULT_OUTPUT = Path(__file__).parent / "data" / "dataset" / "noise_samples"


# ---------------------------------------------------------------------------
# Core noise generators
# ---------------------------------------------------------------------------

def pink_noise(n_samples: int, rng: np.random.Generator) -> np.ndarray:
    """Generate pink (1/f) noise using the Voss-McCartney algorithm."""
    n_rows = 16
    array = rng.random((n_rows, n_samples))
    array = np.cumsum(array - 0.5, axis=1)
    array = np.sum(array, axis=0)
    # Normalize to [-1, 1]
    peak = np.max(np.abs(array))
    if peak > 0:
        array /= peak
    return array.astype(np.float32)


def white_noise(n_samples: int, rng: np.random.Generator) -> np.ndarray:
    """Generate white noise."""
    return rng.standard_normal(n_samples).astype(np.float32)


def amplitude_modulate(signal: np.ndarray, sample_rate: int,
                       freq_hz: float, depth: float = 0.5) -> np.ndarray:
    """Apply sinusoidal amplitude modulation."""
    t = np.linspace(0, len(signal) / sample_rate, len(signal))
    modulator = 1.0 - depth + depth * np.sin(2 * np.pi * freq_hz * t)
    return (signal * modulator).astype(np.float32)


def bandpass_filter(signal: np.ndarray, sample_rate: int,
                    low_hz: float, high_hz: float) -> np.ndarray:
    """Simple band-pass filter using cumulative sum (approximate)."""
    from scipy.signal import butter, sosfilt  # lazy import
    sos = butter(4, [low_hz, high_hz], btype="bandpass",
                 fs=sample_rate, output="sos")
    filtered = sosfilt(sos, signal)
    peak = np.max(np.abs(filtered))
    if peak > 0:
        filtered /= peak
    return filtered.astype(np.float32)


def normalize(signal: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
    """Normalize signal to a target RMS level."""
    rms = np.sqrt(np.mean(signal ** 2))
    if rms > 0:
        signal = signal * (target_rms / rms)
    return np.clip(signal, -1.0, 1.0).astype(np.float32)


# ---------------------------------------------------------------------------
# Noise profile generators
# ---------------------------------------------------------------------------

def generate_wind_light(n_samples: int, sample_rate: int,
                        rng: np.random.Generator) -> np.ndarray:
    """
    Steady harbor wind: pink noise filtered 200–2000 Hz,
    slow amplitude modulation at 0.7 Hz.
    """
    noise = pink_noise(n_samples, rng)
    filtered = bandpass_filter(noise, sample_rate, 200.0, 2000.0)
    modulated = amplitude_modulate(filtered, sample_rate, freq_hz=0.7, depth=0.4)
    return normalize(modulated, target_rms=0.08)


def generate_wind_heavy(n_samples: int, sample_rate: int,
                        rng: np.random.Generator) -> np.ndarray:
    """
    Strong gusts: wind_light base + random burst peaks every 1–3 seconds.
    """
    base = generate_wind_light(n_samples, sample_rate, rng)

    # Add random gusts
    gust = np.zeros(n_samples, dtype=np.float32)
    t = 0
    while t < n_samples:
        gust_len = int(rng.uniform(0.1, 0.4) * sample_rate)
        gap = int(rng.uniform(1.0, 3.0) * sample_rate)
        if t + gust_len < n_samples:
            amp = rng.uniform(0.3, 0.7)
            gust_shape = np.hanning(gust_len).astype(np.float32)
            gust[t:t + gust_len] += amp * gust_shape
        t += gust_len + gap

    combined = base + gust * 0.5
    return normalize(combined, target_rms=0.12)


def generate_waves(n_samples: int, sample_rate: int,
                   rng: np.random.Generator) -> np.ndarray:
    """
    Water/wave sounds: band-pass filtered noise 50–500 Hz,
    very slow amplitude modulation at 0.15 Hz.
    """
    noise = pink_noise(n_samples, rng)
    filtered = bandpass_filter(noise, sample_rate, 50.0, 500.0)
    modulated = amplitude_modulate(filtered, sample_rate, freq_hz=0.15, depth=0.6)
    return normalize(modulated, target_rms=0.09)


def generate_crowd(n_samples: int, sample_rate: int,
                   rng: np.random.Generator) -> np.ndarray:
    """
    Distant workers/voices: speech-shaped noise (300–3400 Hz band,
    characteristic of human voice), layered 3 times at slight offsets.
    """
    result = np.zeros(n_samples, dtype=np.float32)
    for _ in range(3):
        base = white_noise(n_samples, rng)
        # Speech band
        speech_band = bandpass_filter(base, sample_rate, 300.0, 3400.0)
        # Random AM to simulate word-like patterns
        am_freq = rng.uniform(2.0, 5.0)
        am_depth = rng.uniform(0.3, 0.6)
        modulated = amplitude_modulate(speech_band, sample_rate,
                                       freq_hz=am_freq, depth=am_depth)
        # Random time offset to stagger voices
        offset = int(rng.uniform(0, 0.5) * sample_rate)
        result += np.roll(modulated, offset) * rng.uniform(0.3, 0.6)

    return normalize(result, target_rms=0.07)


def generate_mixed(n_samples: int, sample_rate: int,
                   rng: np.random.Generator) -> np.ndarray:
    """
    Combined: wind_light + waves + crowd at reduced individual volumes.
    """
    wind = generate_wind_light(n_samples, sample_rate, rng) * 0.5
    waves = generate_waves(n_samples, sample_rate, rng) * 0.4
    crowd = generate_crowd(n_samples, sample_rate, rng) * 0.35
    combined = wind + waves + crowd
    return normalize(combined, target_rms=0.10)


# ---------------------------------------------------------------------------
# WAV writer
# ---------------------------------------------------------------------------

def save_wav(path: Path, signal: np.ndarray, sample_rate: int) -> None:
    """Save a float32 numpy array as a 16-bit PCM WAV file."""
    pcm = (signal * 32767).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)       # mono
        wf.setsampwidth(2)       # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

PROFILES: dict[str, callable] = {
    "wind_light": generate_wind_light,
    "wind_heavy": generate_wind_heavy,
    "waves": generate_waves,
    "crowd": generate_crowd,
    "mixed": generate_mixed,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic noise sample WAV files for the dataset."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        help=f"Sample rate in Hz (default: {DEFAULT_SAMPLE_RATE})",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help=f"Duration of each loop in seconds (default: {DEFAULT_DURATION})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--profiles",
        nargs="+",
        choices=list(PROFILES.keys()),
        default=list(PROFILES.keys()),
        help="Which noise profiles to generate (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    n_samples = args.sample_rate * args.duration

    # Check scipy is available
    try:
        import scipy.signal  # noqa: F401
    except ImportError:
        print("ERROR: scipy is required. Install with: pip install scipy")
        raise SystemExit(1)

    print(f"Generating noise samples → {args.output}")
    print(f"  Sample rate : {args.sample_rate} Hz")
    print(f"  Duration    : {args.duration}s ({n_samples:,} samples)")
    print()

    for name in args.profiles:
        out_path = args.output / f"{name}.wav"
        if out_path.exists() and not args.force:
            print(f"  [skip]  {name}.wav  (already exists; use --force to overwrite)")
            continue

        print(f"  [gen]   {name}.wav ...", end=" ", flush=True)
        generator = PROFILES[name]
        signal = generator(n_samples, args.sample_rate, rng)
        save_wav(out_path, signal, args.sample_rate)
        duration_actual = len(signal) / args.sample_rate
        rms_db = 20 * np.log10(np.sqrt(np.mean(signal ** 2)) + 1e-9)
        print(f"done  ({duration_actual:.1f}s, RMS={rms_db:.1f} dBFS)")

    print()
    print(f"Done. {len(args.profiles)} file(s) written to {args.output}")
    print()
    print("Verify playback:")
    for name in args.profiles:
        print(f"  afplay {args.output / (name + '.wav')}  # macOS")


if __name__ == "__main__":
    main()
