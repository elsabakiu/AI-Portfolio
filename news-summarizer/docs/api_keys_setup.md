# API Keys Setup

1. Copy `.env.example` to `.env`.
2. Add:
   - `OPENAI_API_KEY`
   - `COHERE_API_KEY`
   - `NEWS_API_KEY` (required for `--source newsapi` or `--source all`)
3. Keep `.env` out of source control.

## Troubleshooting

- `Configuration error`: missing env variables; verify `.env` exists and values are non-empty.
- `ProviderAuthError`: key is invalid or revoked.
- `ProviderRateLimitError`: reduce throughput or wait before retrying.
- `ProviderTimeoutError`: increase `REQUEST_TIMEOUT`.
