# Security and Privacy

## Secrets Handling
- Secrets must be injected via environment variables.
- Do not commit `.env` files.
- Use `.env.example` templates for onboarding only.

## Logging Safety
- Redaction filter masks sensitive fields (`api_key`, `token`, `secret`, `authorization`, `password`).
- Avoid logging full third-party payloads that may contain user-identifiable or sensitive data.

## Data Storage
- SQLite stores run snapshots, user bundles, profiles, and alerts.
- Runtime DB (`langgraph/data/investora.db`) should not be committed.
- Cache artifacts should remain untracked.

## External Integrations
- n8n webhooks should use secure transport and restricted access.
- Provider keys must be rotated and scoped where possible.

## Access Control
- Run endpoints can be protected with `CRON_SECRET` bearer validation.
- CORS should be restricted to trusted frontend origins in production.

## Privacy Considerations
- Product is designed for signal support; avoid storing unnecessary personal data.
- Include explicit user-facing disclaimers for financial content.

## Minimum Pre-Release Security Checklist
- [ ] Secret scan on tracked files
- [ ] `.env` files ignored
- [ ] Runtime artifacts ignored (DB/cache/logs/dist)
- [ ] CORS and cron secret configured for target environment
