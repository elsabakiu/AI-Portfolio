from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class DomainError(Exception):
    message: str
    code: str = "domain_error"
    details: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return self.message


@dataclass
class ProviderError(DomainError):
    code: str = "provider_error"


@dataclass
class ValidationError(DomainError):
    code: str = "validation_error"


@dataclass
class TransientError(DomainError):
    code: str = "transient_error"


def error_payload(
    *,
    code: str,
    message: str,
    run_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if run_id:
        payload["error"]["run_id"] = run_id
    if user_id:
        payload["error"]["user_id"] = user_id
    if details:
        payload["error"]["details"] = details
    return payload
