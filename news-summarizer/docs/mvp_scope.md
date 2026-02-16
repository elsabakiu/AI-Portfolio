# MVP Scope

## In scope

- Fetch from NewsAPI and GDELT
- Summarise + sentiment for each article
- Retry/rate-limit/fallback reliability controls
- Console and JSON reporting
- Cost and token observability

## Out of scope (v0.1.0)

- Web frontend
- Persistent database
- Human feedback loop for model quality
- Real-time streaming

## Success criteria

- Pipeline completes under normal provider conditions
- Failure in one article does not fail entire run
- Logs and metrics explain what happened in the run
