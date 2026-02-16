"""Domain exceptions for pipeline and provider layers."""

from __future__ import annotations


class NewsSummariserError(Exception):
    """Base exception for the application."""


class ConfigError(NewsSummariserError):
    """Invalid or missing runtime configuration."""


class ProviderAuthError(NewsSummariserError):
    """Authentication failed for upstream provider."""


class ProviderRateLimitError(NewsSummariserError):
    """Upstream provider rejected due to rate limiting."""


class ProviderTimeoutError(NewsSummariserError):
    """Upstream provider timed out."""


class LLMResponseError(NewsSummariserError):
    """LLM returned invalid or unusable response."""


class UpstreamDataError(NewsSummariserError):
    """Upstream payload was missing required fields."""
