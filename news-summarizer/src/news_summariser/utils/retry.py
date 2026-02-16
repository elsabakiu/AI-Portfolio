"""Retry utility with exponential backoff and jitter."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


class RetryExhaustedError(RuntimeError):
    """Raised when retryable operation exhausts all attempts."""


def retry_call(
    func: Callable[[], object],
    is_retryable: Callable[[Exception], bool],
    *,
    max_retries: int,
    operation: str,
    sleep_fn=time.sleep,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
) -> object:
    attempts = max(0, max_retries) + 1
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return func()
        except Exception as error:  # noqa: BLE001
            last_error = error
            if attempt == attempts or not is_retryable(error):
                break
            delay = min(max_delay, base_delay * (2 ** (attempt - 1))) * random.uniform(0.5, 1.0)
            logger.warning(
                "Retrying operation after failure",
                extra={"event": "retry", "stage": operation, "attempt": attempt, "latency_ms": int(delay * 1000)},
            )
            sleep_fn(delay)

    raise RetryExhaustedError(f"Operation '{operation}' failed after {attempts} attempts") from last_error
