# Architecture

```mermaid
flowchart LR
  CLI[CLI: stock-market-rag] --> CFG[config + logging]
  CFG --> PIPE[pipeline.run]
  PIPE --> DISC[discover documents]
  DISC --> IO[indexing.io_utils]
  IO --> CHUNK[indexing.chunking]
  CHUNK --> EMB[providers.openai_client embeddings]
  EMB --> STORE[retrieval.vector_store]
  PIPE --> RETRIEVE[similarity retrieval]
  RETRIEVE --> CHAT[providers.openai_client chat]
  PIPE --> REPORT[reporting console/json]
```

## Design rationale

- Clear module boundaries simplify testing and future provider swaps.
- Typed exceptions map external failures into user-actionable messages.
- Structured logging provides run-level traceability for debugging and demos.
