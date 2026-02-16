# Architecture

```mermaid
flowchart LR
  CLI[CLI: news-summariser] --> CFG[config + logging]
  CFG --> PIPE[pipeline.run]
  PIPE --> FETCH[providers.newsapi/gdelt]
  PIPE --> SUMM[processing.summariser]
  PIPE --> SENT[processing.sentiment]
  SUMM --> LLM1[providers.openai_client]
  SENT --> LLM2[providers.cohere_client]
  PIPE --> METRICS[reporting.metrics]
  METRICS --> OUT1[reporting.console_report]
  METRICS --> OUT2[reporting.json_report]
```

## Key design choices

- Provider wrappers isolate upstream SDK and HTTP concerns.
- Processing modules remain pure and testable.
- Pipeline orchestrates control flow, failure isolation, and metrics.
- Reporting layer formats outputs without business logic.
