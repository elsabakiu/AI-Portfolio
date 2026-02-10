# -----------------------------
# Imports
# -----------------------------
import re  # Regular expressions for text splitting and cleaning
from pathlib import Path  # File path handling
from openai import OpenAI  # OpenAI client for TTS
import shutil  # Check for ffmpeg in PATH
import subprocess  # Run ffmpeg commands

# Initialize OpenAI client with API key from environment variables
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Default maximum characters per TTS chunk
MAX_CHARS_PER_CHUNK = 3500

# -----------------------------
# Text chunking helpers
# -----------------------------
def normalize_whitespace(text):
    """
    Normalize whitespace in text:
    - Convert all newlines to \n
    - Collapse multiple spaces/tabs into one
    - Collapse multiple blank lines into two
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def chunk_text(text, max_chars=MAX_CHARS_PER_CHUNK):
    """
    Split text into chunks for TTS:
    - Prefer splitting by paragraph
    - Split long paragraphs by sentence
    - Hard split if needed
    Returns a list of strings (chunks)
    """
    text = normalize_whitespace(text)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    def flush():
        """Save current buffer to chunks and reset"""
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = ""

    # Regex to split sentences
    sentence_split = re.compile(r"(?<=[.!?])\s+")

    for p in paragraphs:
        parts = [p] if len(p) <= max_chars else sentence_split.split(p)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            candidate = part if not current else current + "\n\n" + part
            if len(candidate) <= max_chars:
                current = candidate
            else:
                flush()
                if len(part) > max_chars:
                    # Hard split if part is still too long
                    for i in range(0, len(part), max_chars):
                        piece = part[i:i+max_chars].strip()
                        if piece:
                            chunks.append(piece)
                else:
                    current = part
    flush()
    return chunks

# -----------------------------
# TTS helper
# -----------------------------
def tts_to_mp3(text, out_path: Path, tts_model="tts-1", tts_voice="alloy"):
    """
    Convert text to speech using OpenAI TTS.
    - text: string to speak
    - out_path: Path where MP3 will be saved
    - tts_model / tts_voice: parameters for TTS model
    """
    speech = client.audio.speech.create(
        model=tts_model,
        voice=tts_voice,
        input=text,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(speech.read())

# -----------------------------
# Audio concatenation
# -----------------------------
def ffmpeg_available():
    """Check if ffmpeg executable is available in PATH"""
    return shutil.which("ffmpeg") is not None

def concat_mp3(mp3_files, out_file: Path):
    """
    Concatenate MP3 chunks into a single file.
    - Uses ffmpeg if available for fast concat
    - Otherwise falls back to pydub for re-encoding
    """
    if ffmpeg_available():
        list_file = out_file.parent / "concat_list.txt"
        # Create a temporary file listing all chunks
        with open(list_file, "w", encoding="utf-8") as f:
            for p in mp3_files:
                f.write(f"file '{p.resolve().as_posix()}'\n")
        # Run ffmpeg concat
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(out_file),
        ], check=True)
    else:
        # Fallback: use pydub to combine
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for p in mp3_files:
            combined += AudioSegment.from_file(p, format="mp3")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        combined.export(out_file, format="mp3")

