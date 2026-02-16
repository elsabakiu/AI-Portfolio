"""Simple fixed-interval rate limiter."""

from __future__ import annotations

import time


class FixedIntervalRateLimiter:
    def __init__(self, requests_per_minute: int, sleep_fn=time.sleep) -> None:
        self._interval = 60.0 / float(max(1, requests_per_minute))
        self._sleep = sleep_fn
        self._last_call = 0.0

    def wait(self) -> None:
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < self._interval:
            self._sleep(self._interval - elapsed)
        self._last_call = time.time()
