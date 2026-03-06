# Investora-AI Golden Path Checklist

Purpose: freeze current behavior during refactor and run after each vertical slice.

## End-to-End Checklist

- Register a new user
  - Expected: account created, auth token/session available, redirect to onboarding or dashboard.
- Login with existing user
  - Expected: successful auth and profile state restored.
- Onboarding completion
  - Expected: profile saved via `PUT /user/{id}/profile`, readiness flags set.
- Run analysis
  - Trigger `POST /run-analysis` or `POST /run-analysis-stream` in mock mode and real mode.
  - Expected: successful completion, no API schema regressions, no fatal node errors.
- Dashboard load
  - Call `GET /user/{id}/dashboard`.
  - Expected: latest bundle returns with watchlist/discovery sections.
- Profile save/edit
  - Update profile fields and save.
  - Expected: persisted and reflected in subsequent dashboard/personalization calls.
- Alerts create/edit/delete
  - Use alert endpoints (`GET/POST/PATCH/DELETE /user/{id}/alerts...`).
  - Expected: state transitions valid and alert list consistent.

## API Contract Checks

- `POST /run-analysis-stream`
  - Response media type remains `text/event-stream`.
  - Emits `node_complete` and terminal `done` or normalized `error` event.
- `GET /user/{id}/dashboard`
  - Returns latest bundle shape used by frontend.
- `GET /user/{id}/personalized-signals`
  - Returns `{ watchlist_signals, discovery_signals }`.

## Deterministic Mock Test Mode

- `USE_MOCK_DATA=true`
- fixed fixture bundle and stream-node events under `langgraph/tests/fixtures/`
- run tests after each refactor slice.
