# -----------------------------
# Imports
# -----------------------------
import os
import gradio as gr  # Gradio for web UI
from pathlib import Path  # Path handling for files

# Import custom modules from src
from data_processor import fetch_articles  # Fetch and parse article text
from llm_processor import generate_podcast_script  # Generate podcast script from articles
from tts_generator import chunk_text, tts_to_mp3, concat_mp3, MAX_CHARS_PER_CHUNK  # TTS helpers

# -----------------------------
# Output directories
# -----------------------------
OUTPUT_DIR = Path("podcast_output")  # Main folder for outputs
CHUNKS_DIR = OUTPUT_DIR / "chunks"  # Temporary folder for TTS chunks

# Default articles if user doesn't provide URLs
DEFAULT_URLS = [
    "https://www.nationalgeographic.com/history/article/fall-of-ancient-roman-empire",
    "https://www.bbc.co.uk/history/ancient/romans/fallofrome_article_01.shtml",
]

# -----------------------------
# Pipeline function
# -----------------------------
def run_pipeline(urls_text, minutes, tts_model, tts_voice, max_chars):
    """
    Complete pipeline:
      1. Split URLs text into list
      2. Fetch articles
      3. Generate podcast script using LLM
      4. Chunk script for TTS
      5. Convert each chunk to MP3
      6. Concatenate MP3s into final audio
    Returns:
      - script: full podcast text
      - final_audio_path: Path to generated MP3
    """
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    articles = fetch_articles(urls)

    script = generate_podcast_script(articles, minutes)

    chunks = chunk_text(script, max_chars=max_chars)

    mp3_files = []
    for i, chunk in enumerate(chunks, start=1):
        mp3_path = CHUNKS_DIR / f"chunk_{i:02d}.mp3"
        tts_to_mp3(chunk, mp3_path, tts_model, tts_voice)
        mp3_files.append(mp3_path)

    final_audio_path = OUTPUT_DIR / "podcast_episode_final.mp3"
    concat_mp3(mp3_files, final_audio_path)

    return script, final_audio_path

# -----------------------------
# Gradio UI
# -----------------------------
with gr.Blocks(title="Fall of Rome Podcast Generator") as demo:
    # Inputs
    urls_text = gr.Textbox(label="Article URLs", value="\n".join(DEFAULT_URLS), lines=3)
    minutes = gr.Number(label="Target length (minutes)", value=10)
    tts_model = gr.Textbox(label="TTS model", value="tts-1")
    tts_voice = gr.Dropdown(label="Voice", choices=["alloy", "onyx", "sage"], value="onyx")
    max_chars = gr.Slider(label="Chunk size", minimum=1200, maximum=4500, step=100, value=MAX_CHARS_PER_CHUNK)

    # Outputs
    script_out = gr.Textbox(label="Script", lines=7)
    audio_out = gr.Audio(label="Audio", type="filepath")

    # Button to run pipeline
    generate_btn = gr.Button("Generate episode")
    generate_btn.click(
        fn=run_pipeline,
        inputs=[urls_text, minutes, tts_model, tts_voice, max_chars],
        outputs=[script_out, audio_out]
    )

# Launch the app
demo.launch()

