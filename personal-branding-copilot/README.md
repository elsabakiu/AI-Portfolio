# Personal Branding Copilot

An AI product MVP built to solve a practical product problem: how to create consistent, differentiated, high-quality LinkedIn content without falling into generic AI output.

The focus is on turning a real user pain point into a working system with measurable quality controls, retrieval-driven context, and human feedback loops.

## Why This Project Exists

Professionals and founders want to build audience trust through content, but they face three recurring constraints:
- Limited time to write strategic posts.
- Difficulty staying consistent with a clear voice.
- Generic output quality from one-shot prompting.

The MVP addresses this by combining retrieval, structured prompt orchestration, model-based evaluation, refinement, and human-in-the-loop decisions.

## Product Vision

Build an AI copilot that helps users publish content that is:
- **On-brand**: aligned with voice, positioning, and audience.
- **Useful**: practical, specific, and outcome-oriented.
- **Differentiated**: avoids "AI-Slop" and generic phrasing.

## MVP Scope (What Is Implemented)

- Post generation for three formats: `thought_leadership`, `educational`, `trend_commentary`.
- RAG context from two knowledge bases.
- Multi-angle candidate generation.
- Candidate ranking via evaluator model.
- Brand consistency scoring.
- Feedback-driven refinement pass.
- Asset generation (hashtags + image).
- Human-in-the-loop accept/reject workflow with memory.
- Content pillar generation + caching.

## Knowledge Base Design

The retrieval layer is intentionally split into two sources:
- `primary` knowledge base:
  profile-specific inputs (bio, methodology, testimonials, case studies, audience).
- `secondary` knowledge base:
  market context (industry trends, reports, competitor and ecosystem signals).

This structure enables content that is both personalized and market-aware.

## Human-in-the-Loop System

This is not a fully automated content bot. The user remains the final decision-maker.

- Users can `Accept` or `Reject` outputs in the UI.
- Rejections include optional notes.
- Feedback is persisted in `data/user_feedback.jsonl`.
- Previous feedback is injected into future generations to reinforce preferences and avoid repeated weak patterns.

## End-to-End Workflow

1. User selects topic, format, and target persona.
2. System retrieves relevant context from both knowledge bases.
3. Multiple draft angles are generated.
4. Evaluator selects the strongest candidate.
5. Draft is refined and brand-checked.
6. Feedback-driven refinement is applied.
7. Final post, hashtags, and image are generated.
8. User accepts/rejects and feedback is stored for future runs.

## Product Interface

The Gradio app includes:
- `Dashboard` for generation and validation.
- `Content Pillars` for strategic topic planning.

Outputs are shown directly as:
- `Final Post`
- `Hashtags`
- `Generated Image`

## Product and AI Approach

- Product thinking from problem framing to MVP execution.
- Prompt and evaluation design beyond single-prompt generation.
- Applied RAG for context quality and differentiation.
- Human-in-the-loop decision architecture.
- Iteration mindset: quality measurement, feedback memory, and roadmap-driven expansion.

## Success Metrics

- Draft-to-acceptance rate.
- Time to publishable draft.
- Weekly publishing consistency.
- Brand score trend over time.
- Content pillar reuse rate.

## Tech Stack

- Python
- Gradio
- OpenAI API
- Cohere API
- Markdown knowledge bases for retrieval

## Project Structure

```text
personal-branding/
├── personal_branding/
│   ├── apps/
│   │   └── gradio_app.py
│   ├── pipeline/
│   │   ├── generate_post.py
│   │   ├── brand_checker.py
│   │   ├── refiner.py
│   │   ├── post_assets.py
│   │   └── feedback_loop.py
│   └── services/
│       ├── llm_client.py
│       └── cohere_evaluator.py
├── prompts/
├── src/knowledge_base/
└── data/
```

## Setup

### Prerequisites
- Python 3.10+
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

## Run

From `personal-branding/`:
```bash
python personal_branding/apps/gradio_app.py
```

Default URL: `http://127.0.0.1:7860`

## Roadmap (Next Iterations)

1. `Content Planner MVP`
- Weekly calendar, pillar balancing, and scheduling reminders.

2. `Distribution MVP`
- One-click export/publishing to LinkedIn drafts, Notion, and Buffer/Hootsuite.

3. `Experimentation MVP`
- A/B testing for hooks, CTAs, post formats, and model/prompt variants.

4. `Performance Analytics MVP`
- Post outcome tracking (impressions, saves, comments) mapped back to content patterns.

5. `Audience Personalization MVP`
- Dynamic, profile-aware knowledge base to support personalized generation for multiple professional profiles.

## Notes

This project is intentionally structured as an iterative product system: clear scope, traceable quality signals, and extensible roadmap tracks for planning, distribution, experimentation, analytics, and personalization.
