"""Time helper utilities."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone


def monotonic_ms() -> float:
    return time.monotonic() * 1000.0


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]
