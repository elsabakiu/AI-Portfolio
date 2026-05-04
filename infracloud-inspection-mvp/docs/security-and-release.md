# Security and Release Readiness

## Secret management

- Store `OPENAI_API_KEY`, `LANGSMITH_API_KEY`, `SENTRY_DSN`, `WORKFLOW_SENTRY_DSN`, `POSTGRES_PASSWORD`, and `AUTH_TOKENS_JSON` in a secret manager or environment injection system.
- Never commit populated `.env*` files.
- Rotate any previously exposed LangSmith or OpenAI credentials immediately.
- Use distinct secrets per environment: development, staging, production.

## Auth and authorization

- `reviewer`
  - can read drafts
  - can run extraction
  - can inspect workflow runs
- `approver`
  - reviewer permissions
  - can save approved drafts
  - can send records to InfraCloud
- `admin`
  - all permissions
  - operational and incident response access

Production recommendation:
- set `AUTH_MODE=bearer`
- provide `AUTH_TOKENS_JSON` through your secret manager
- rotate bearer tokens on a fixed schedule or when staff access changes

## Data handling

- Current retention default: `DATA_RETENTION_DAYS=90`
- Apply retention cleanup with:

```bash
npm run retention:apply
```

- Logs and Sentry contexts redact:
  - authorization headers
  - API keys
  - bearer tokens
  - DSNs
  - password-like fields
  - base64 audio payloads

## Deployment hygiene

- Use the pinned Python dependencies in `apps/workflow/requirements.txt`
- Use `package-lock.json` for deterministic Node installs
- Build immutable images:
  - `infra/docker/Dockerfile.web`
  - `infra/docker/Dockerfile.api`
  - `infra/docker/Dockerfile.workflow`
- Use `infra/deployment/docker-compose.staging.yml` for staging validation before production rollout

## Release versioning

- Set:
  - `SENTRY_RELEASE`
  - `VITE_SENTRY_RELEASE`
  - `WORKFLOW_SENTRY_RELEASE`
- Recommended format:
  - `infracloud-inspection-mvp@YYYY.MM.DD+gitsha`

## Rollback plan

1. Keep the previous image tag available in the registry.
2. Roll back web, api, and workflow independently if needed.
3. Do not roll back database schema blindly.
4. For schema-sensitive releases:
   - deploy migrations first in staging
   - ensure app code is backward compatible with the previous schema during rollout
5. Confirm health after rollback:
   - `GET /api/health`
   - `GET /api/ready`
   - `GET /health` on workflow
   - `GET /ready` on workflow

## Immediate manual actions

1. Rotate any previously exposed keys.
2. Move all production secrets into a secret manager.
3. Set `AUTH_MODE=bearer` for staging and production.
4. Create separate staging and production Sentry projects and releases.
