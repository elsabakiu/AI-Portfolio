"""Backward-compatible OpenAI service API."""

from __future__ import annotations

from stock_market_rag.config import load_settings
from stock_market_rag.pipeline.errors import ConfigError
from stock_market_rag.providers.openai_client import OpenAIProvider


class OpenAIService:
    def __init__(self) -> None:
        settings = load_settings()
        try:
            settings.validate()
        except ConfigError as error:
            raise ValueError(str(error)) from error
        self.provider = OpenAIProvider(settings)
        self.embedding_model = settings.embedding_model
        self.chat_model = settings.chat_model

    def get_embeddings_batch(
        self,
        texts: list[str],
        model: str | None = None,
        batch_size: int = 100,
        log_progress: bool = True,
    ) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self.provider.embed_texts(texts, model=model, batch_size=batch_size)
        if log_progress:
            total = len(texts)
            for processed in range(min(batch_size, total), total + 1, batch_size):
                print(f"Processed {min(processed, total)}/{total} chunks")
        return embeddings

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.provider.embed_texts(texts, model=None, batch_size=100)

    def answer_with_context(self, question: str, context_chunks: list[str]) -> str:
        return self.provider.answer_with_context(question=question, context_chunks=context_chunks, model=None)
