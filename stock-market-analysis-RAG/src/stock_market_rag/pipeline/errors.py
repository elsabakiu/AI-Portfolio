"""Typed domain exceptions."""

from __future__ import annotations


class StockRagError(Exception):
    """Base error for stock market RAG."""


class ConfigError(StockRagError):
    """Missing or invalid config."""


class ProviderAuthError(StockRagError):
    """Provider authentication failure."""


class ProviderRateLimitError(StockRagError):
    """Provider rate-limit failure."""


class ProviderTimeoutError(StockRagError):
    """Provider timeout failure."""


class EmbeddingError(StockRagError):
    """Embedding generation failed."""


class RetrievalError(StockRagError):
    """Retrieval failed."""


class ResponseFormatError(StockRagError):
    """Model response format invalid."""


class UpstreamDataError(StockRagError):
    """Input document/data malformed or unreadable."""
