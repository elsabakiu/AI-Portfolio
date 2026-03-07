# Runbook

## Local Start
1. Frontend deps: `npm install`
2. Backend deps: `python -m pip install -r langgraph/requirements.txt`
3. Configure env files from examples.
4. Start backend: `cd langgraph && python -m uvicorn app.api:app --reload --port 8000`
5. Start frontend: `cd .. && npm run dev`

## Core Health Checks
- API up: `GET /latest-report` (or any health-relevant endpoint)
- Metrics: `GET /debug/metrics`
- Stream run: `POST /run-analysis-stream`

## Common Issues
### 1) AI View returns unavailable/error
- Verify `OPENAI_API_KEY` is set in backend env.
- Restart backend after env changes.

### 2) Run queue errors (429)
- Tune `MAX_CONCURRENT_RUNS`, `MAX_QUEUED_RUNS`, `RUN_QUEUE_WAIT_SECONDS`.

### 3) Provider failures/rate limits
- Check provider key availability and rate limits.
- Use mock mode for deterministic fallback (`USE_MOCK_DATA=true`).

### 4) Empty dashboard for user
- Ensure profile saved and at least one analysis run completed.

## Monitor/Triage Checklist
- Check recent run history and error counts.
- Inspect node timings in `/debug/metrics`.
- Review redacted logs for repeated node/provider failures.

## Deploy Notes
- Ensure env vars are configured in deployment target.
- Keep cron-protected endpoints behind `CRON_SECRET`.
- Validate CORS origins for frontend host.
