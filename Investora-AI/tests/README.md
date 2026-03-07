# Tests Index

This project uses a split test strategy:

- Backend tests: `langgraph/tests/`
  - unit, API contract, and graph integration coverage
- Frontend tests:
  - feature and component tests colocated under `src/**` as `*.test.ts(x)`

Run all key checks:

```bash
cd investora-ai/langgraph && python -m pytest -q tests
cd ../.. && cd investora-ai && npm run test
cd investora-ai && npm run build
```
