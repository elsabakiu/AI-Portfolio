from __future__ import annotations

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from .config import settings
from .redaction import redact_sensitive_data


def init_sentry() -> None:
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=settings.sentry_release,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
        integrations=[FastApiIntegration()],
    )


def capture_exception(error: Exception, **extras) -> None:
    if not settings.sentry_dsn:
        return

    with sentry_sdk.push_scope() as scope:
        scope.set_tag("service", "workflow")
        for key, value in extras.items():
            if value is None:
                continue
            if key in {"stage", "suspicion_id", "run_id", "workflow_version", "model"}:
                scope.set_tag(key, str(value))
            else:
                scope.set_extra(key, redact_sensitive_data(value))
        sentry_sdk.capture_exception(error)


def add_breadcrumb(message: str, category: str, level: str = "info", **data) -> None:
    if not settings.sentry_dsn:
        return

    sentry_sdk.add_breadcrumb(
        category=category,
        message=message,
        level=level,
        data={key: value for key, value in data.items() if value is not None},
    )


def set_context_tags(**tags) -> None:
    if not settings.sentry_dsn:
        return

    for key, value in tags.items():
        if value is not None:
            sentry_sdk.set_tag(key, str(value))
