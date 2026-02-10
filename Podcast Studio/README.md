# 🎙️ Podcast Studio – AI Podcast Episode Generator

Podcast Studio is an AI-powered Python application that transforms long-form online articles into narrated podcast episodes.  
It combines article extraction, LLM-based script generation, and text-to-speech into a single end-to-end content pipeline with a simple web interface.

This project was built to explore how LLMs can be turned into reliable, user-facing products, going beyond text demos to deliver complete, usable audio experiences.

---

## At a glance

- What it is: AI-powered article-to-podcast generator  
- Who it’s for: Users who prefer audio-first content and accessibility-friendly formats  
- What it demonstrates: End-to-end AI product thinking, prompt design, and production-aware system constraints  

---

## What this product does

Podcast Studio allows users to:

- Paste one or more article URLs
- Define a target episode length in minutes
- Select a text-to-speech voice
- Generate both a podcast-style script and a narrated MP3 episode

The system is designed around:

- Predictable output length
- Clean narrative structure
- Reliability for long-form content
- Transparency over black-box automation

---

## Problem this project addresses

High-quality written content is widely available, but:

- Many users prefer listening over reading
- Converting articles into podcasts is time-consuming
- Most AI tools stop at summaries and do not produce usable audio

Creating podcasts usually involves multiple steps:

- Summarizing
- Scripting
- Recording
- Editing
- Exporting

This project explores how AI can automate that workflow while keeping user control, explainability, and clear quality boundaries.

---

## How the product works end to end

Podcast Studio automates the full content-to-audio pipeline:

- Fetch and clean article content
- Generate an original, spoken-style script using an LLM
- Split long scripts into safe chunks
- Convert text chunks into speech
- Merge audio into a single podcast episode

End-to-end flow:

Sources -> LLM script -> chunking -> TTS per chunk -> final MP3

The result is a usable MVP that delivers a complete audio artifact, not just generated text.

---

## User flow

User input:
- Paste article URLs one per line
- Set target podcast length in minutes
- Select TTS model and voice
- Adjust chunk size in characters

System processing:
- Parse and normalize articles
- Generate a structured podcast script
- Chunk text for TTS safety
- Generate and merge audio

Output:
- Script preview
- Playable and downloadable MP3 episode

---

## Key AI and system design decisions

### Article processing
- Articles are fetched and parsed using newspaper.Article
- Output format is {url, text}
- Non-content elements are removed to keep prompts focused

Why: Clean input improves LLM reliability and narrative quality.

---

### Script generation with LLMs
- All sources are combined into a single prompt
- Prompt enforces:
  - Original narration
  - Simple, spoken language
  - Explicit structure:
    - Hook
    - Background
    - Three to five key points
    - Recap
    - Reflective closing

Script length is guided by a user-defined minutes parameter.

Why: Structure and length constraints reduce variability and improve usability.

---

### Why chunking is required
- Generated scripts are normalized before audio generation
- Chunking strategy:
  - Paragraph-first
  - Sentence-aware
  - Hard cuts only as a fallback

Why:
TTS APIs have hard input limits and fail unpredictably on long text.
Chunking preserves narrative flow while ensuring reliability and recoverability.

---

### Text-to-speech and audio assembly
- Each chunk is converted to audio using OpenAI TTS
- Chunking enables:
  - Reliable long-form audio generation
  - Safe API limit handling
  - Partial failure recovery
- Audio chunks are merged into a single MP3 using ffmpeg

---

## User interface

The UI is built with Gradio to enable fast iteration and experimentation:

- URL input one per line
- Target length, voice, and chunk-size controls
- Generated script preview
- Audio player with download option

The interface intentionally prioritizes clarity and speed over visual complexity.

---

## Repository structure

```
podcast-studio/
README.md
requirements.txt
.env
src/
  data_processor.py
  llm_processor.py
  tts_generator.py
  main.py
screenshots/
podcast_output/
  chunks/
  concat_list.txt
  podcast_episode_final.mp3
templates/
Podcast_Generator.ipynb
```

---

## Setup

Create and activate a virtual environment:

```
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Create a .env file in the project root:

```
OPENAI_API_KEY=your_api_key_here
```

---

## Usage

Run the Gradio app:

```
python src/main.py
```

Steps:
- Paste article URLs
- Set target podcast length
- Choose TTS model and voice
- Click Generate episode

The final audio file is saved as:

```
podcast_output/podcast_episode_final.mp3
```

---

## Trade-offs and intentional limitations

- Episode length is approximate to keep the UX simple
- No automated factual verification beyond source grounding
- Audio tone is limited to predefined voices
- Very long or poorly structured articles may reduce narrative quality

These constraints were intentionally accepted to keep the MVP focused, transparent, and explainable.

---

## Production-ready next steps

Planned improvements:

- Improved URL input UX and validation
- Script correction and feedback loop
- Dynamic model and voice previews
- Subtitle generation in SRT format
- Performance optimizations
- Dynamic prompt adaptation based on content type
