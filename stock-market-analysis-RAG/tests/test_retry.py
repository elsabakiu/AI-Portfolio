"""Retry utility tests."""

from __future__ import annotations

import pytest

from stock_market_rag.utils.retry import RetryExhaustedError, retry_call


class TempError(RuntimeError):
    pass


class FatalError(RuntimeError):
    pass


def test_retry_eventual_success() -> None:
    state = {"n": 0}

    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise TempError("temporary")
        return "ok"

    value = retry_call(
        flaky,
        is_retryable=lambda error: isinstance(error, TempError),
        max_retries=3,
        operation="test",
        sleep_fn=lambda _seconds: None,
    )

    assert value == "ok"
    assert state["n"] == 3


def test_retry_exhausted_for_fatal() -> None:
    def fail() -> None:
        raise FatalError("fatal")

    with pytest.raises(RetryExhaustedError):
        retry_call(
            fail,
            is_retryable=lambda error: isinstance(error, TempError),
            max_retries=2,
            operation="test",
            sleep_fn=lambda _seconds: None,
        )
