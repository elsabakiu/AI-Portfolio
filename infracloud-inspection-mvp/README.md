# InfraCloud Inspection Pipeline

LangGraph-based inspection review system for German field audio.

## Stack

- `web`: React + TypeScript + Vite
- `api`: Node.js + Express + Postgres
- `workflow`: Python + FastAPI + LangGraph
- `ai`: OpenAI transcription and structured extraction
- `observability`: Sentry, LangSmith, JSON logs, Prometheus-style metrics

## What the app does

- loads sample inspection cases
- accepts field audio plus an existing InfraCloud record
- runs transcription and extraction through the LangGraph workflow service
- shows transcript, warnings, diagnostics, conflicts, and the proposed update
- supports reviewer/approver workflows for draft save and mock submission
- persists workflow runs, drafts, submissions, and audit events in Postgres

## Local development

### Prerequisites

- Node.js 20+
- Python 3.11+
- Postgres 14+
- `OPENAI_API_KEY`
- `LANGSMITH_API_KEY` if tracing is enabled

### Environment

Copy `.env.example` into a local env file and populate the required values.

Important settings:

- `DATABASE_URL`
- `LANGGRAPH_SERVICE_URL`
- `OPENAI_API_KEY`
- `AUTH_MODE`
- `AUTH_TOKENS_JSON`
- `SENTRY_DSN`
- `VITE_SENTRY_DSN`
- `WORKFLOW_SENTRY_DSN`

For local development, the default auth mode is header-based:

- `x-user-id`
- `x-user-role`

Supported roles:

- `reviewer`
- `approver`
- `admin`

### Run locally

```bash
npm install
npm run dev
npm run dev:workflow
```

Services:

- web: `http://localhost:5173`
- api: `http://127.0.0.1:8787`
- workflow: `http://127.0.0.1:8001`

## Architecture

- [src](./src): React frontend
- [apps/api](./apps/api): API, persistence, auth, audit, metrics
- [apps/workflow](./apps/workflow): LangGraph workflow service
- [apps/web](./apps/web): React review application
- [apps/web/public/samples](./apps/web/public/samples): sample audio files
- [apps/web/public/records](./apps/web/public/records): sample existing-record payloads
- [infra/migrations](./infra/migrations): Postgres schema migrations
- [docs/security-and-release.md](./docs/security-and-release.md): security, release, rollback guidance

## API flow

1. The web app sends extraction requests to the Node API.
2. The Node API validates input, records audit metadata, and calls the LangGraph service.
3. The LangGraph service transcribes audio, extracts structured fields, validates catalog data, detects conflicts, and returns a review payload.
4. The Node API persists the workflow result and returns it to the UI.

## Test the extraction flow

Run the local API and workflow service, then call:

```bash
curl -X POST "http://127.0.0.1:8787/api/extract" \
  -H "x-user-id: reviewer-1" \
  -H "x-user-role: reviewer" \
  -F "audio_file=@apps/web/public/samples/test1.wav" \
  -F "suspicion_id=14401" \
  -F "existing_record=$(cat apps/web/public/records/test1_existing_record.json)"
```

## Generate sample WAV files

Use the helper script:

```bash
python apps/workflow/scripts/generate_test_audio.py
```

It uses OpenAI TTS to regenerate the three sample German narration files.

## Quality gates

Run the full local verification suite:

```bash
npm run ci
```

This covers:

- lint
- typecheck
- frontend/backend tests
- workflow tests
- build
- migration checks

## Security and operations

See [docs/security-and-release.md](./docs/security-and-release.md) for:

- secret management
- retention cleanup
- auth mode guidance
- staging deployment
- release versioning
- rollback planning

## Deployment assets

- [Dockerfile.web](./infra/docker/Dockerfile.web)
- [Dockerfile.api](./infra/docker/Dockerfile.api)
- [Dockerfile.workflow](./infra/docker/Dockerfile.workflow)
- [docker-compose.staging.yml](./infra/deployment/docker-compose.staging.yml)
