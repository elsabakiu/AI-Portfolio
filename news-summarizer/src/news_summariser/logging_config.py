"""Structured logging setup with run-level correlation."""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

RUN_ID: ContextVar[str] = ContextVar("run_id", default="-")


class RunContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = RUN_ID.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "run_id": getattr(record, "run_id", "-"),
            "msg": record.getMessage(),
        }
        for key in ("event", "provider", "stage", "article_url", "attempt", "latency_ms"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


class KeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(timezone.utc).isoformat()
        base = (
            f"ts={ts} level={record.levelname} logger={record.name} "
            f"run_id={getattr(record, 'run_id', '-')} msg={record.getMessage()}"
        )
        if record.exc_info:
            base = f"{base} exc={self.formatException(record.exc_info)}"
        return base


def configure_logging(level: str = "INFO", json_logs: bool = True) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RunContextFilter())
    handler.setFormatter(JsonFormatter() if json_logs else KeyValueFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def set_run_id(run_id: str) -> None:
    RUN_ID.set(run_id)
