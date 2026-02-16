"""Cohere wrapper with token/cost tracking and error mapping."""

from __future__ import annotations

from dataclasses import dataclass

import cohere

from news_summariser.config import Settings
from news_summariser.pipeline.errors import LLMResponseError, ProviderAuthError, ProviderRateLimitError, ProviderTimeoutError
from news_summariser.providers.openai_client import count_tokens
from news_summariser.utils.rate_limit import FixedIntervalRateLimiter
from news_summariser.utils.retry import retry_call


PRICING_PER_MILLION = {
    "command-a-03-2025": {"input": 2.50, "output": 10.00},
    "command-r": {"input": 0.50, "output": 1.50},
    "command-r-plus": {"input": 3.00, "output": 15.00},
}


@dataclass
class LLMUsageEvent:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float


class CohereClient:
    def __init__(self, settings: Settings, client: cohere.ClientV2 | None = None) -> None:
        self._settings = settings
        self._client = client or cohere.ClientV2(api_key=settings.cohere_api_key)
        self._limiter = FixedIntervalRateLimiter(settings.cohere_rpm)

    def generate(self, prompt: str, *, model: str | None = None) -> tuple[str, LLMUsageEvent]:
        selected_model = model or self._settings.cohere_model
        self._limiter.wait()

        def _call():
            return self._client.chat(
                model=selected_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
            )

        try:
            response = retry_call(
                _call,
                is_retryable=_is_retryable_error,
                max_retries=self._settings.max_retries,
                operation="cohere_generate",
            )
        except Exception as error:  # noqa: BLE001
            raise _map_error(error) from error

        text = _extract_text(response)
        if not text.strip():
            raise LLMResponseError("Cohere returned an empty response")

        input_tokens = count_tokens(prompt, selected_model)
        output_tokens = count_tokens(text, selected_model)
        event = LLMUsageEvent(
            provider="cohere",
            model=selected_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=_estimate_cost(selected_model, input_tokens, output_tokens),
        )
        return text, event


def _extract_text(response: object) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text

    message = getattr(response, "message", None)
    content = getattr(message, "content", None) if message is not None else None
    if isinstance(content, list):
        out: list[str] = []
        for row in content:
            value = getattr(row, "text", None)
            if isinstance(value, str):
                out.append(value)
            elif isinstance(row, dict) and isinstance(row.get("text"), str):
                out.append(row["text"])
        return "\n".join(out)

    raise LLMResponseError("Unable to extract text from Cohere response")


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
        return ProviderAuthError("Cohere authentication failed. Check COHERE_API_KEY.")
    if "rate" in text:
        return ProviderRateLimitError("Cohere rate limit reached")
    if "timeout" in text:
        return ProviderTimeoutError("Cohere request timed out")
    return error
