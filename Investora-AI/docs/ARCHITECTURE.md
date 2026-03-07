# Architecture

## High-Level System
- Frontend: React + TypeScript + React Query
- Backend API: FastAPI
- Analysis engine: LangGraph state machine
- Storage: SQLite (`langgraph/data/investora.db`)
- External providers: OpenAI, Finnhub, FMP, Marketstack, optional Pinecone
- Integrations: n8n webhooks for alerts/digests/report handoff

## Data Flow
1. Frontend triggers analysis (`/run-analysis` or `/run-analysis-stream`).
2. FastAPI invokes LangGraph with run context.
3. Graph nodes collect provider data, compute scores, detect anomalies.
4. Evidence/synthesis nodes enrich signals.
5. Personalization nodes build user bundles.
6. Delivery nodes post alerts/digests.
7. Persistence node stores run snapshots and bundles.
8. Frontend reads dashboard and personalized endpoints.

## LangGraph Node Modules
- `nodes/data_collection.py`
- `nodes/scoring.py`
- `nodes/anomalies.py`
- `nodes/evidence.py`
- `nodes/personalization.py`
- `nodes/delivery.py`
- `nodes/persistence.py`

Graph assembly and registry:
- `app/graph_builder.py`
- `app/node_registry.py`
- `app/graph.py`

## Reliability and Observability
- Deterministic mock mode (`USE_MOCK_DATA=true`)
- Contract + integration tests in `langgraph/tests/`
- Node timing metrics exposed at `/debug/metrics`
- Correlation ID middleware and redaction logging filter

## Key Interfaces
- `POST /run-analysis-stream`
- `GET /user/{id}/dashboard`
- `GET /user/{id}/personalized-signals`
- `GET /market/ai-view/{ticker}`

## Folder Layout
- `docs/` product + architecture + ops
- `langgraph/` backend and tests
- `src/` frontend app
- `tests/` portfolio-level test index/entry
