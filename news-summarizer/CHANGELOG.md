# Changelog

## v0.1.0 - 2026-02-16

- Refactored project into modular package architecture under `src/news_summariser`.
- Added structured logging with run correlation id (`run_id`).
- Added typed domain exceptions and improved CLI-facing error messages.
- Added provider wrappers with retry, rate limiting, and fallback behavior.
- Added run metrics for counts, latency, token usage, and cost estimates.
- Added console/JSON reporting and output file support.
- Added PM-oriented docs and portfolio framing.
- Added network-free pytest suite and GitHub Actions CI workflow.
