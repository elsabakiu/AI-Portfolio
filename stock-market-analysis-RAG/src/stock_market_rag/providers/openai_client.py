"""OpenAI provider wrapper with retry and error mapping."""

from __future__ import annotations

import logging
import re

from openai import OpenAI, RateLimitError

from stock_market_rag.config import Settings
from stock_market_rag.pipeline.errors import (
    EmbeddingError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ResponseFormatError,
)
from stock_market_rag.utils.retry import retry_call

logger = logging.getLogger(__name__)


class OpenAIProvider:
    def __init__(self, settings: Settings, client: OpenAI | None = None) -> None:
        self.settings = settings
        self.client = client or OpenAI(api_key=settings.openai_api_key)

    @staticmethod
    def _extract_retry_seconds(error_message: str) -> float | None:
        ms_match = re.search(r"try again in\s+(\d+)ms", error_message, re.IGNORECASE)
        if ms_match:
            return max(0.1, int(ms_match.group(1)) / 1000.0)

        sec_match = re.search(r"try again in\s+(\d+(?:\.\d+)?)s", error_message, re.IGNORECASE)
        if sec_match:
            return max(0.1, float(sec_match.group(1)))
        return None

    def embed_texts(self, texts: list[str], *, model: str | None = None, batch_size: int = 100) -> list[list[float]]:
        if not texts:
            return []

        selected_model = model or self.settings.embedding_model
        max_estimated_tokens_per_request = 200_000
        embeddings: list[list[float]] = []

        def est_tokens(value: str) -> int:
            return max(1, len(value) // 4)

        for i in range(0, len(texts), max(1, batch_size)):
            batch = texts[i : i + max(1, batch_size)]
            request_batches: list[list[str]] = []
            safe_batch: list[str] = []
            safe_tokens = 0

            for text in batch:
                tokens = est_tokens(text)
                if safe_batch and safe_tokens + tokens > max_estimated_tokens_per_request:
                    request_batches.append(safe_batch)
                    safe_batch = []
                    safe_tokens = 0
                safe_batch.append(text)
                safe_tokens += tokens

            if safe_batch:
                request_batches.append(safe_batch)

            for request_batch in request_batches:
                response = self._embed_with_retry(model=selected_model, input_batch=request_batch)
                embeddings.extend(row.embedding for row in response.data)

        return embeddings

    def _embed_with_retry(self, *, model: str, input_batch: list[str]):
        def _call():
            return self.client.embeddings.create(model=model, input=input_batch)

        try:
            return retry_call(
                _call,
                is_retryable=self._is_retryable_error,
                max_retries=self.settings.max_retries,
                operation="openai_embeddings",
            )
        except Exception as error:  # noqa: BLE001
            raise self._map_error(error, stage="embedding") from error

    def answer_with_context(self, *, question: str, context_chunks: list[str], model: str | None = None) -> str:
        selected_model = model or self.settings.chat_model
        context = "\n\n".join(context_chunks)
        prompt = (
            "You are a helpful assistant. Use ONLY the provided context to answer. "
            "If the answer is not in context, say you don't have enough information.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}"
        )

        def _call():
            return self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You answer based on retrieved documents."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )

        try:
            response = retry_call(
                _call,
                is_retryable=self._is_retryable_error,
                max_retries=self.settings.max_retries,
                operation="openai_chat",
            )
        except Exception as error:  # noqa: BLE001
            raise self._map_error(error, stage="chat") from error

        try:
            text = response.choices[0].message.content or ""
        except Exception as error:  # noqa: BLE001
            raise ResponseFormatError("OpenAI chat response missing content") from error

        if not text.strip():
            raise ResponseFormatError("OpenAI chat returned empty response")
        return text

    @staticmethod
    def _is_retryable_error(error: Exception) -> bool:
        if isinstance(error, RateLimitError):
            return True
        text = str(error).lower()
        return any(key in text for key in ("rate", "timeout", "temporarily", "connection"))

    @staticmethod
    def _map_error(error: Exception, *, stage: str) -> Exception:
        text = str(error).lower()
        if "api key" in text or "auth" in text or "unauthorized" in text:
            return ProviderAuthError("OpenAI authentication failed. Check OPENAI_API_KEY.")
        if "rate" in text:
            return ProviderRateLimitError("OpenAI rate limit reached; retry later.")
        if "timeout" in text:
            return ProviderTimeoutError("OpenAI request timed out.")
        if stage == "embedding":
            return EmbeddingError(f"Embedding request failed: {error}")
        return ResponseFormatError(f"Chat request failed: {error}")
