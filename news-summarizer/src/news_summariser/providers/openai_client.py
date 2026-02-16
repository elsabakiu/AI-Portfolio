"""OpenAI wrapper with token/cost tracking and error mapping."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import tiktoken
from openai import OpenAI

from news_summariser.config import Settings
from news_summariser.pipeline.errors import LLMResponseError, ProviderAuthError, ProviderRateLimitError, ProviderTimeoutError
from news_summariser.utils.rate_limit import FixedIntervalRateLimiter
from news_summariser.utils.retry import retry_call

logger = logging.getLogger(__name__)


PRICING_PER_MILLION = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}


@dataclass
class LLMUsageEvent:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float


class OpenAIClient:
    def __init__(self, settings: Settings, client: OpenAI | None = None) -> None:
        self._settings = settings
        self._client = client or OpenAI(api_key=settings.openai_api_key)
        self._limiter = FixedIntervalRateLimiter(settings.openai_rpm)

    def generate(self, prompt: str, *, model: str | None = None) -> tuple[str, LLMUsageEvent]:
        selected_model = model or self._settings.openai_model
        self._limiter.wait()

        def _call():
            return self._client.chat.completions.create(
                model=selected_model,
                messages=[{"role": "user", "content": prompt}],
            )

        try:
            response = retry_call(
                _call,
                is_retryable=_is_retryable_error,
                max_retries=self._settings.max_retries,
                operation="openai_generate",
            )
        except Exception as error:  # noqa: BLE001
            raise _map_error(error) from error

        try:
            text = response.choices[0].message.content or ""
        except Exception as error:  # noqa: BLE001
            raise LLMResponseError("OpenAI response did not contain message content") from error

        if not text.strip():
            raise LLMResponseError("OpenAI returned an empty response")

        input_tokens = count_tokens(prompt, selected_model)
        output_tokens = count_tokens(text, selected_model)
        event = LLMUsageEvent(
            provider="openai",
            model=selected_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=_estimate_cost(selected_model, input_tokens, output_tokens),
        )
        return text, event


def count_tokens(text: str, model: str) -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        return max(1, len(text) // 4)


def _estimate_cost(model: str, in_tokens: int, out_tokens: int) -> float:
    prices = PRICING_PER_MILLION.get(model, {"input": 3.0, "output": 15.0})
    return ((in_tokens / 1_000_000.0) * prices["input"]) + ((out_tokens / 1_000_000.0) * prices["output"])


def _is_retryable_error(error: Exception) -> bool:
    name = type(error).__name__.lower()
    text = str(error).lower()
    return any(tag in name or tag in text for tag in ("timeout", "connection", "rate"))


def _map_error(error: Exception) -> Exception:
    text = str(error).lower()
    if "api key" in text or "auth" in text:
        return ProviderAuthError("OpenAI authentication failed. Check OPENAI_API_KEY.")
    if "rate" in text:
        return ProviderRateLimitError("OpenAI rate limit reached")
    if "timeout" in text:
        return ProviderTimeoutError("OpenAI request timed out")
    return error
