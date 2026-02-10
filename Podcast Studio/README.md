🎙️ Podcast Studio – AI Podcast Episode Generator

Podcast Studio is an AI-powered Python application that transforms long-form online articles into narrated podcast episodes.
It combines article extraction, LLM-based script generation, and text-to-speech into a single, end-to-end content pipeline with a simple web interface.
The project is designed as a practical exploration of AI-driven content adaptation, audio-first UX, and production-aware LLM pipelines.

1. Product overview

   Podcast Studio allows users to:

   - paste one or more article URLs
   - define a target episode length (in minutes)
   - select a text-to-speech voice
   - generate both a podcast-style script and a narrated MP3 episode

   The system emphasizes:

   - predictable output length
   - clean narrative structure
   - reliability for long-form content
   - transparency over black-box automation

2. Problem statement

   High-quality written content is widely available, but:
   - many users prefer audio over reading
   - converting articles into podcasts is time-consuming
   - most AI tools stop at summaries and do not produce usable audio

   Podcast creation usually involves multiple steps: summarizing, scripting, recording, editing, and exporting.
   This project explores how AI can automate that workflow while keeping user control, explainability, and quality constraints.

3. Solution

   Podcast Studio automates the full content-to-audio pipeline:

   - Fetch and clean article content
   - Generate an original, spoken-style script using an LLM
   - Split long scripts into safe chunks
   - Convert text chunks into speech
   - Merge audio into a single podcast episode
   - The result is a usable MVP that goes beyond text generation and delivers a complete audio artifact.

4. User flow

   - User pastes article URLs (one per line)
   - User configures:
      - target podcast length (minutes)
      - TTS model and voice
      - chunk size (characters)

   - System processes the content:
      - parses articles
      - generates a structured script
      - chunks text for TTS
      - generates and merges audio

   - User receives:
      - generated script (preview)
      - playable and downloadable MP3 episode

5. AI & system design

   - Source processing
      - Articles are fetched and parsed using newspaper.Article
         -Output format: {url, text}
      - Non-content elements are removed to keep prompts clean and focused

   - Script generation (LLM)
      - All sources are combined into a single prompt
      - Prompt enforces:
         - original narration (no copying from sources)
         - simple, spoken language
         - clear structure:
            - hook
            - background
            - 3–5 key causes or points
            - recap
            - reflective closing
      - Script length is guided by a user-defined minutes parameter (approximate)

   - Text preparation & chunking
      - Generated script is normalized
      - Chunking strategy:
         - paragraph-first
         - sentence-aware
         - hard cuts only as fallback
         - This avoids mid-sentence breaks and stays within TTS limits

   - Text-to-speech (TTS)
      - Each chunk is converted to audio using OpenAI TTS
      - Chunking improves:
         - reliability for long scripts
         - API limit handling
         - partial failure recovery
      - Audio assembly
         - All audio chunks are merged into a single MP3 using ffmpeg

   End-to-end system flow
   Sources → LLM script → chunking → TTS per chunk → final MP3

6. User interface

   The UI is built with Gradio to support fast iteration and experimentation:

      - URL input (one per line)
      - target length, voice, and chunk-size controls
      - generated script preview
      - audio player with download option

   The UI intentionally prioritizes clarity and speed over visual complexity.

7. Repository structure
   podcast-studio/
   ├── README.md
   ├── requirements.txt
   ├── .env                # API keys (not committed)
   │
   ├── src/
   │   ├── data_processor.py    # Fetch and process articles
   │   ├── llm_processor.py     # Script generation with OpenAI
   │   ├── tts_generator.py     # TTS + audio handling
   │   └── main.py              # Gradio application
   │
   ├── screenshots/             # UI screenshots
   │
   ├── podcast_output/          # Generated audio & intermediate files
   │   ├── chunks/
   │   ├── concat_list.txt
   │   └── podcast_episode_final.mp3
   │
   ├── templates/               # Optional Gradio templates
   └── Podcast_Generator.ipynb  # Early experimentation notebook

8. Setup
   1. Create and activate a virtual environment
      python -m venv venv
      source venv/bin/activate   # macOS / Linux
      venv\Scripts\activate      # Windows

   2. Install dependencies
      pip install -r requirements.txt

   3. Configure environment variables
      Create a .env file in the project root:
      OPENAI_API_KEY=your_api_key_here

9. Usage

   Run the Gradio app:
     - python src/main.py

   Steps:
   - Paste article URLs (one per line)
   - Set target podcast length (minutes)
   - Choose TTS model and voice
   - Click Generate episode

   The final audio file is saved as: podcast_output/podcast_episode_final.mp3

10. Trade-offs & limitations

   - Episode length is approximate and based on average speaking speed
   - No automatic factual verification beyond source grounding
   - Audio tone is limited to predefined voices
   - Very long or poorly structured articles may reduce narrative quality
   - These trade-offs were accepted to keep the MVP simple, transparent, and explainable.

11. Production-ready next steps

      Planned improvements:
         - improved URL input UX and validation
         - script correction and feedback loop
         - dynamic model and voice previews
         - subtitle (SRT) generation
         - performance optimizations
         - dynamic prompt adaptation based on content type




