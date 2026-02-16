# API Keys Setup

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_API_KEY`.
3. Optionally adjust model/chunking/retry settings.

## Troubleshooting

- `Configuration error`: missing env vars or invalid chunk settings.
- `ProviderAuthError`: invalid API key.
- `ProviderRateLimitError`: request volume too high; retry later.
- `ProviderTimeoutError`: network/provider slow; increase `REQUEST_TIMEOUT`.
- `UpstreamDataError`: unreadable/malformed document.
