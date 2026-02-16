# Stock Market RAG

AI product-style research assistant for analyzing company filings/transcripts with grounded answers from local source documents.

## Product Pitch

Convert dense earnings/filing documents into fast, evidence-backed answers for PMs, founders, and analysts who need decision-ready insights.

## Problem Statement

Financial documents are long, fragmented, and hard to query quickly. Manual synthesis slows investment and strategy decisions.

## Target Users

- Product Managers tracking AI/semiconductor competitive moves
- Founders monitoring market narratives and risk signals
- Analysts who need explainable, source-grounded summaries

## MVP Capabilities

- Multi-document indexing over local market datasets
- Chunking + embedding + similarity retrieval pipeline
- Grounded Q&A constrained to retrieved evidence
- Structured logs with `run_id` correlation
- Robust retry and typed error handling
- Console and JSON run reports with observability metrics

## Quickstart

```bash
cd stock-market-analysis-RAG
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add `OPENAI_API_KEY` to `.env`, then run:

```bash
PYTHONPATH=src python -m stock_market_rag --output console
```

Or after editable install:

```bash
pip install -e .
stock-market-rag --output json --out-file outputs/latest_run.json
```

## CLI Usage

```bash
python -m stock_market_rag [options]
```

Options:

- `--dataset-root <path>`: custom dataset folder
- `--top-k <int>`: retrieved chunks per question
- `--question <text>`: repeatable custom question flag
- `--output {console,json}`
- `--out-file <path>`
- `--log-level {DEBUG,INFO,WARNING,ERROR}`

Legacy compatibility command still works:

```bash
PYTHONPATH=src python -m lab2_rag_openai.main
```

## Reliability Design

- Retry with backoff+jitter for transient OpenAI failures
- Typed exceptions for config/auth/rate-limit/timeout/data issues
- Per-document failure isolation (bad docs are skipped, run continues)
- Non-zero exit codes for runtime/config failures

## Observability

Logs include `run_id` and stage metadata.

Run metrics include:

- `docs_indexed`, `chunks_indexed`
- `embedding_calls`, `chat_calls`, `retrieval_requests`
- `failed_docs`
- average stage latency

## Architecture

- `src/stock_market_rag/config.py`: settings + validation
- `src/stock_market_rag/logging_config.py`: structured logs
- `src/stock_market_rag/providers/openai_client.py`: OpenAI interactions + retry/error mapping
- `src/stock_market_rag/indexing/`: document loading and chunking
- `src/stock_market_rag/retrieval/vector_store.py`: in-memory similarity search
- `src/stock_market_rag/pipeline/run.py`: orchestration
- `src/stock_market_rag/reporting/`: console/json output

## PM Trade-offs

- In-memory vector store keeps setup simple but is not persistent/scalable.
- OpenAI-only provider keeps quality consistent but limits resilience/diversification.
- Retrieval quality depends on chunking defaults; domain-tuned chunking can improve precision.

## Roadmap

1. Persistent vector backend (FAISS/pgvector) for faster iterative querying.
2. Evaluation harness for retrieval relevance and answer faithfulness.
3. Multi-provider support for embeddings/chat fallback.
4. Scheduled report generation and comparative trend snapshots.

## Tests

```bash
PYTHONPATH=src pytest
```

Tests are network-free and use fakes/mocks.
