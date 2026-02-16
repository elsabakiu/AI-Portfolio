"""Unit tests for retry utility."""

from __future__ import annotations

import pytest

from news_summariser.utils.retry import RetryExhaustedError, retry_call


class TempError(RuntimeError):
    pass


class FatalError(RuntimeError):
    pass


def test_retry_succeeds_after_transient_failures() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise TempError("temporary")
        return "ok"

    result = retry_call(
        flaky,
        is_retryable=lambda error: isinstance(error, TempError),
        max_retries=3,
        operation="unit_test",
        sleep_fn=lambda _x: None,
    )

    assert result == "ok"
    assert calls["n"] == 3


def test_retry_raises_for_non_retryable_error() -> None:
    def fail_fast() -> str:
        raise FatalError("fatal")

    with pytest.raises(RetryExhaustedError):
        retry_call(
            fail_fast,
            is_retryable=lambda error: isinstance(error, TempError),
            max_retries=3,
            operation="unit_test",
            sleep_fn=lambda _x: None,
        )
