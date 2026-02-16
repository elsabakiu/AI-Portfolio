"""Retry helper."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


class RetryExhaustedError(RuntimeError):
    pass


def retry_call(
    func: Callable[[], object],
    *,
    is_retryable: Callable[[Exception], bool],
    max_retries: int,
    operation: str,
    sleep_fn=time.sleep,
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
            wait = min(10.0, 0.5 * (2 ** (attempt - 1))) + random.uniform(0, 0.25)
            logger.warning(
                "Retrying after transient failure",
                extra={"event": "retry", "stage": operation, "attempt": attempt},
            )
            sleep_fn(wait)

    raise RetryExhaustedError(f"Operation '{operation}' failed after {attempts} attempts") from last_error
