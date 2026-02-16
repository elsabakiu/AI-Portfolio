# News Summariser

AI product-style CLI that reduces information overload by fetching current headlines, generating concise summaries, scoring sentiment, and reporting usage/cost metrics per run.


## Problem

Busy professionals (PMs, founders, operators) need a fast signal from high-volume news streams. Reading full article lists is slow and inconsistent.

## Target Users

- Product Managers tracking markets and competitor launches
- Founders monitoring trends and narratives
- Busy professionals who need briefings over deep reading

## MVP Capabilities

- Multi-source ingest (`newsapi`, `gdelt`, or `all`)
- LLM summary + sentiment analysis with provider fallback
- Sync and async execution modes
- Structured logs with `run_id` correlation
- Retry + rate-limit resilience
- Token usage and estimated cost reporting by provider
- Console and JSON outputs

## Quickstart

```bash
cd news-summarizer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set keys in `.env` (`OPENAI_API_KEY`, `COHERE_API_KEY`, `NEWS_API_KEY`) and run:

```bash
PYTHONPATH=src python -m news_summariser --source all --category technology --limit 5 --output console --mode sync
```

Launch Gradio UI:

```bash
PYTHONPATH=src python -m news_summariser.gradio_app
```

Or use the script after editable install:

```bash
pip install -e .
news-summariser --source newsapi --query "AI agents" --limit 5 --output json --out-file examples/latest_run.json
```

## CLI Usage

```bash
python -m news_summariser [options]
```

Options:

- `--source {all,newsapi,gdelt}`
- `--category <name>`
- `--query <text>`
- `--limit <int>`
- `--output {console,json}`
- `--out-file <path>`
- `--language <code>`
- `--mode {sync,async}`
- `--log-level {DEBUG,INFO,WARNING,ERROR}`

## Reliability and Observability

- Retries with exponential backoff + jitter on transient failures
- Fixed-interval provider rate limiting
- Typed domain errors with user-friendly CLI messages
- Debug stack traces in logs without leaking secrets
- Run metrics:
  - fetched/processed/succeeded/failed counts
  - average stage latency
  - token usage by provider
  - estimated cost by provider and total

## Architecture

- `src/news_summariser/config.py`: env-backed runtime settings + validation
- `src/news_summariser/logging_config.py`: structured logging and `run_id`
- `src/news_summariser/providers/`: external service wrappers
- `src/news_summariser/processing/`: pure transforms and prompt builders
- `src/news_summariser/pipeline/run.py`: orchestrator (`fetch -> summarise -> sentiment -> report`)
- `src/news_summariser/reporting/`: console + JSON report rendering
- `src/news_summariser/utils/`: retry, rate limit, time helpers

## Testing

```bash
PYTHONPATH=src pytest
```

Tests mock providers and never require network calls.

## Product Trade-offs

- Uses synchronous provider SDK calls even in async mode (`asyncio.to_thread`) for minimal dependency complexity.
- Keeps cost estimation heuristic/tokenizer-based; provider billing can differ slightly.
- Defaults to two LLM providers for resilience, increasing request volume vs single-provider mode.

## Roadmap

1. Add provider abstraction for additional sources (RSS/Reddit/financial APIs).
2. Add persistent storage and trend comparison across runs.
3. Introduce evaluation harness for summary quality and sentiment consistency.
4. Add container image + scheduled batch run examples.
