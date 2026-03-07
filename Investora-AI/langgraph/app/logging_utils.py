from __future__ import annotations

import logging
import re
from typing import Any

_SENSITIVE_KEY_PATTERN = re.compile(r"(api[_-]?key|token|secret|authorization|password)", re.IGNORECASE)
_BEARER_PATTERN = re.compile(r"(?i)bearer\s+[a-z0-9._\-]+")
_KEY_VALUE_PATTERN = re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[=:]\s*[^\s,;]+")



def redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for k, v in value.items():
            key = str(k)
            if _SENSITIVE_KEY_PATTERN.search(key):
                redacted[k] = "***REDACTED***"
            else:
                redacted[k] = redact_value(v)
        return redacted

    if isinstance(value, list):
        return [redact_value(v) for v in value]

    if isinstance(value, tuple):
        return tuple(redact_value(v) for v in value)

    if isinstance(value, str):
        out = _BEARER_PATTERN.sub("Bearer ***REDACTED***", value)
        out = _KEY_VALUE_PATTERN.sub(lambda m: f"{m.group(1)}=***REDACTED***", out)
        return out

    return value


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_value(record.msg)
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(redact_value(a) for a in record.args)
            else:
                record.args = redact_value(record.args)

        for key, value in list(record.__dict__.items()):
            if key in {"msg", "args", "name", "levelname", "levelno", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process", "message", "asctime"}:
                continue
            if _SENSITIVE_KEY_PATTERN.search(key):
                record.__dict__[key] = "***REDACTED***"
            else:
                record.__dict__[key] = redact_value(value)
        return True



def install_redaction_filter() -> None:
    root = logging.getLogger()
    already = any(isinstance(f, RedactionFilter) for f in root.filters)
    if not already:
        root.addFilter(RedactionFilter())
