# Personal Branding Copilot

Welcome to the second main project.

This AI Content Creator system serves as the interface between companies (or you as a consultant) and their next customers. The objective is to build a strong brand identity and advance business goals through intelligent, unique content generation.

Unlike generic AI content that often becomes homogenized ("AI-Slop"), this system is built to produce authentic, contextually relevant outputs by combining:
- two distinct knowledge bases (`src/knowledge_base/primary` and `src/knowledge_base/secondary`)
- advanced prompt engineering across multiple generation and evaluation stages

The project integrates multiple AI capabilities in one workflow: document processing, LLM API orchestration, and a full content creation pipeline with quality controls. A key requirement is that outputs should be demonstrably distinct from generic ChatGPT-style responses.

## 1) Product Brief 

### Problem
Professionals building a personal brand on LinkedIn struggle to publish consistently because writing high-quality, differentiated posts takes too much time and mental effort.

### Target User
- Primary user: Product Manager / consultant / operator focused on SME AI adoption.
- Audience: SME decision-makers and business operators.

### Value Proposition
Generate publish-ready LinkedIn drafts in minutes while preserving brand voice, practical business relevance, and content quality controls.

### MVP Hypothesis
If users get a guided workflow that combines:
- multi-angle draft generation,
- automated quality checks,
- fast refinement,
- post assets (hashtags + image),
- and feedback memory,

then they can publish more consistently with stronger brand alignment.

## 2) MVP Scope Implemented

### Core Capabilities
- Generate posts by type: `thought_leadership`, `educational`, `trend_commentary`.
- Use RAG context from local knowledge base (`src/knowledge_base`).
- Produce multiple draft angles and select the strongest one via evaluator.
- Run brand consistency scoring and feedback summary.
- Refine drafts based on quality feedback.
- Generate hashtags and post image.
- Capture accept/reject feedback to improve future outputs.
- Generate reusable content pillars and cache them.

### Product Interface
- Gradio app with:
  - Dashboard view for post generation and validation.
  - Outputs shown directly as `Final Post`, `Hashtags`, and `Generated Image` (no separate generation-steps panel).
  - Content Pillars view for strategic planning.

## 3) End-to-End Flow

1. User defines topic, post type, persona, and generation settings.
2. System retrieves brand/market context from the knowledge base.
3. Multiple candidate drafts are generated from different angles.
4. Evaluator selects the best draft.
5. Brand check scores alignment and provides improvement signal.
6. Refiner updates the draft.
7. Hashtags and image are generated.
8. User accepts/rejects output; feedback is stored in `data/user_feedback.jsonl`.

## 4) Success Metrics (PM)

- Draft-to-acceptance rate.
- Time to first publishable draft.
- Weekly publishing consistency.
- Brand score trend over time.
- Reuse rate of generated content pillars.

## 5) Current Tech Stack

- Python
- Gradio (product UI)
- OpenAI API (drafting, refinement, brand checks, assets)
- Cohere API (candidate evaluator)
- Local markdown knowledge base for RAG context

## 6) Project Structure

```text
personal-branding/
├── personal_branding/
│   ├── apps/
│   │   └── gradio_app.py      # main product UI
│   ├── pipeline/
│   │   ├── generate_post.py   # draft generation pipeline
│   │   ├── brand_checker.py   # post quality/brand scoring
│   │   ├── refiner.py         # post refinement
│   │   ├── post_assets.py     # hashtags + image
│   │   └── feedback_loop.py   # acceptance/rejection memory
│   └── services/
│       ├── llm_client.py
│       └── cohere_evaluator.py
├── prompts/                   # prompt templates
├── src/knowledge_base/        # primary + secondary context docs
└── data/                      # generated artifacts, feedback, cache
```

## 7) Setup and Run

### Prerequisites
- Python 3.10+
- API keys:
  - `OPENAI_API_KEY`
  - `COHERE_API_KEY`

### Install
```bash
pip install gradio openai python-dotenv
```

### Environment
Create `personal-branding/.env`:
```bash
OPENAI_API_KEY=your_openai_key
COHERE_API_KEY=your_cohere_key
```

### Launch app
From `personal-branding/`:
```bash
python personal_branding/apps/gradio_app.py
```

Default URL: `http://127.0.0.1:7860` (or next available local port).

## 8) Product Roadmap (Next Iteration)

- Add analytics dashboard for metric tracking.
- Add experiment framework (prompt/model A/B tests).
- Add ICP-specific tone presets and CTA variants.
- Add one-click export to LinkedIn publishing workflow.
