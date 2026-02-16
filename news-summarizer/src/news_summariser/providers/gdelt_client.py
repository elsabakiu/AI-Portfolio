"""GDELT provider client."""

from __future__ import annotations

import logging
import re

import requests

from news_summariser.config import Settings
from news_summariser.pipeline.errors import ProviderRateLimitError, ProviderTimeoutError, UpstreamDataError
from news_summariser.pipeline.models import Article
from news_summariser.utils.rate_limit import FixedIntervalRateLimiter
from news_summariser.utils.retry import retry_call

logger = logging.getLogger(__name__)


class GdeltClient:
    def __init__(self, settings: Settings, session: requests.Session | None = None) -> None:
        self._settings = settings
        self._session = session or requests.Session()
        self._limiter = FixedIntervalRateLimiter(settings.gdelt_rpm)
        self._base_url = "https://api.gdeltproject.org/api/v2/doc/doc"

    def fetch_articles(
        self,
        *,
        category: str | None,
        query: str | None,
        limit: int,
        language: str = "en",
    ) -> list[Article]:
        self._limiter.wait()
        _ = language
        q = (query or category or self._settings.default_category).strip()

        params = {
            "query": q,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": limit,
        }
        logger.info("Requesting GDELT", extra={"event": "provider_request", "provider": "gdelt"})

        def _call() -> requests.Response:
            response = self._session.get(self._base_url, params=params, timeout=self._settings.request_timeout)
            response.raise_for_status()
            return response

        try:
            response = retry_call(
                _call,
                is_retryable=_is_retryable_request_error,
                max_retries=self._settings.max_retries,
                operation="gdelt_fetch",
            )
        except Exception as error:  # noqa: BLE001
            raise _map_request_error(error) from error

        data = response.json()
        raw_articles = data.get("articles")
        if not isinstance(raw_articles, list):
            raise UpstreamDataError("GDELT response missing 'articles' list")

        return [
            Article(
                title=str((row.get("title") or "")).strip(),
                description=str((row.get("snippet") or "")).strip(),
                content=str((row.get("snippet") or "")).strip(),
                url=str((row.get("url") or "")).strip(),
                source=_gdelt_source(row),
                published_at=_normalize_seendate(str(row.get("seendate") or "")),
            )
            for row in raw_articles
        ]


def _gdelt_source(row: dict) -> str:
    domain = str(row.get("domain") or "").strip()
    return f"GDELT ({domain})" if domain else "GDELT"


def _normalize_seendate(value: str) -> str:
    match = re.fullmatch(r"(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z", value.strip())
    if not match:
        return value
    y, m, d, hh, mm, ss = match.groups()
    return f"{y}-{m}-{d}T{hh}:{mm}:{ss}Z"


def _is_retryable_request_error(error: Exception) -> bool:
    if isinstance(error, (requests.Timeout, requests.ConnectionError)):
        return True
    if isinstance(error, requests.HTTPError):
        response = error.response
        return bool(response is not None and response.status_code in {429, 500, 502, 503, 504})
    return False


def _map_request_error(error: Exception) -> Exception:
    if isinstance(error, requests.Timeout):
        return ProviderTimeoutError("GDELT request timed out")
    if isinstance(error, requests.HTTPError):
        response = error.response
        status = response.status_code if response is not None else "unknown"
        if status == 429:
            return ProviderRateLimitError("GDELT rate limit reached")
        return UpstreamDataError(f"GDELT request failed with status {status}")
    if isinstance(error, requests.RequestException):
        return UpstreamDataError(f"GDELT request failed: {error}")
    return error
