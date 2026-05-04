from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    openai_transcription_model: str = os.getenv(
        "OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"
    )
    openai_timeout_seconds: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
    langsmith_api_key: str | None = os.getenv("LANGSMITH_API_KEY")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "infracloud-langgraph")
    langsmith_tracing: bool = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
    sentry_dsn: str | None = os.getenv("WORKFLOW_SENTRY_DSN")
    sentry_environment: str = os.getenv("WORKFLOW_SENTRY_ENVIRONMENT", app_env)
    sentry_release: str = os.getenv(
        "WORKFLOW_SENTRY_RELEASE", "infracloud-langgraph-service@dev"
    )
    sentry_traces_sample_rate: float = float(
        os.getenv("WORKFLOW_SENTRY_TRACES_SAMPLE_RATE", "0.2")
    )
    workflow_version: str = os.getenv("WORKFLOW_VERSION", "2026-03-23")


settings = Settings()
