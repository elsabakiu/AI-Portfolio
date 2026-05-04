from __future__ import annotations

from typing import Any


SENSITIVE_KEYS = ("authorization", "api_key", "token", "secret", "password", "dsn", "base64")


def _is_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(fragment in lowered for fragment in SENSITIVE_KEYS)


def _redact_string(value: str) -> str:
    if len(value) <= 8:
        return "[REDACTED]"
    return f"{value[:4]}...[REDACTED]"


def redact_sensitive_data(value: Any, parent_key: str = "") -> Any:
    if value is None:
        return value

    if isinstance(value, list):
        return [redact_sensitive_data(item, parent_key) for item in value]

    if isinstance(value, dict):
        output = {}
        for key, nested in value.items():
            if _is_sensitive(key):
                output[key] = _redact_string(nested) if isinstance(nested, str) else "[REDACTED]"
            else:
                output[key] = redact_sensitive_data(nested, key)
        return output

    if isinstance(value, str) and _is_sensitive(parent_key):
        return _redact_string(value)

    return value
