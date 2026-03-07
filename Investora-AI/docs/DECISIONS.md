# Decision Log

## 1) Incremental Refactor Over Rewrite
Decision:
- Refactor in vertical slices while preserving behavior.

Why:
- Reduced delivery risk and regression exposure.
- Allowed ongoing feature support during cleanup.

Tradeoff:
- Temporary duplicate patterns during transition.

## 2) Modular LangGraph Node Extraction
Decision:
- Split node logic into domain modules and use a registry-driven graph builder.

Why:
- Better traceability and ownership boundaries.
- Lower cognitive load for future changes.

Tradeoff:
- More files and imports to manage.

## 3) Typed Settings and Config Domains
Decision:
- Centralized settings object with grouped domains and validation warnings.

Why:
- Avoided scattered env usage and startup surprises.

Tradeoff:
- Requires keeping config schema current.

## 4) Repository + Service Layer
Decision:
- Added repositories over event store and services over route orchestration.

Why:
- Improves reuse across API/cron/CLI paths.
- Makes business logic easier to test.

Tradeoff:
- Added abstraction in a small codebase.

## 5) Safety Net Before Deep Changes
Decision:
- Added contract tests for critical endpoints and deterministic fixtures.

Why:
- Enabled safe refactor velocity.

Tradeoff:
- Upfront test-writing cost.

## 6) Logging Redaction + Metrics Endpoint
Decision:
- Added redaction filter and debug metrics snapshot endpoint.

Why:
- Reduced secret leakage risk and improved operational debugging.

Tradeoff:
- In-memory metrics are not persistent across restarts.
