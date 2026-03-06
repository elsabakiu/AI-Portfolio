from __future__ import annotations

import os
import time
import threading
from typing import Literal

AcquireStatus = Literal["acquired", "queue_full", "timeout"]


class RunLimiter:
    """In-memory admission control for analysis runs."""

    def __init__(self, max_active: int, max_queued: int) -> None:
        self.max_active = max(1, max_active)
        self.max_queued = max(0, max_queued)
        self._active = 0
        self._queued = 0
        self._cv = threading.Condition()

    def acquire(self, timeout_s: float) -> AcquireStatus:
        with self._cv:
            if self._active < self.max_active:
                self._active += 1
                return "acquired"

            if self._queued >= self.max_queued:
                return "queue_full"

            self._queued += 1
            deadline = time.monotonic() + max(0.0, timeout_s)
            try:
                while self._active >= self.max_active:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return "timeout"
                    self._cv.wait(timeout=remaining)
                self._active += 1
                return "acquired"
            finally:
                self._queued -= 1

    def release(self) -> None:
        with self._cv:
            if self._active > 0:
                self._active -= 1
            self._cv.notify()

    def stats(self) -> dict[str, int]:
        with self._cv:
            return {
                "active": self._active,
                "queued": self._queued,
                "max_active": self.max_active,
                "max_queued": self.max_queued,
            }


run_limiter = RunLimiter(
    max_active=int(os.environ.get("MAX_CONCURRENT_RUNS", "2")),
    max_queued=int(os.environ.get("MAX_QUEUED_RUNS", "8")),
)

