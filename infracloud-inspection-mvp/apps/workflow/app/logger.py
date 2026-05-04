from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .config import settings
from .redaction import redact_sensitive_data


def _serialize(value: Any) -> Any:
    if isinstance(value, Exception):
        return {
            "error_type": value.__class__.__name__,
            "error_message": str(value),
        }
    return value


def log(level: str, message: str, **fields: Any) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "service": "infracloud-langgraph-workflow",
        "environment": settings.app_env,
        "message": message,
    }
    payload.update(
        redact_sensitive_data(
            {key: _serialize(value) for key, value in fields.items() if value is not None}
        )
    )
    print(json.dumps(payload, ensure_ascii=False))


class WorkflowLogger:
    def info(self, message: str, **fields: Any) -> None:
        log("info", message, **fields)

    def warn(self, message: str, **fields: Any) -> None:
        log("warn", message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        log("error", message, **fields)


logger = WorkflowLogger()
