"""NewsAPI provider client."""

from __future__ import annotations

import logging
from dataclasses import asdict

import requests

from news_summariser.config import Settings
from news_summariser.pipeline.errors import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    UpstreamDataError,
)
from news_summariser.pipeline.models import Article
from news_summariser.utils.rate_limit import FixedIntervalRateLimiter
from news_summariser.utils.retry import retry_call

logger = logging.getLogger(__name__)


class NewsApiClient:
    def __init__(self, settings: Settings, session: requests.Session | None = None) -> None:
        self._settings = settings
        self._session = session or requests.Session()
        self._limiter = FixedIntervalRateLimiter(settings.news_api_rpm)
        self._base_url = "https://newsapi.org/v2"

    def fetch_articles(
        self,
        *,
        category: str | None,
        query: str | None,
        limit: int,
        language: str = "en",
    ) -> list[Article]:
        self._limiter.wait()

        endpoint = "/everything" if query else "/top-headlines"
        params = {
            "apiKey": self._settings.news_api_key,
            "language": language,
            "pageSize": limit,
            "sortBy": "publishedAt",
        }
        if query:
            params["q"] = query
        else:
            params["category"] = category or self._settings.default_category
            params["country"] = "us"
            params.pop("sortBy", None)

        logger.info("Requesting NewsAPI", extra={"event": "provider_request", "provider": "newsapi"})

        def _call() -> requests.Response:
            response = self._session.get(
                f"{self._base_url}{endpoint}",
                params=params,
                timeout=self._settings.request_timeout,
            )
            response.raise_for_status()
            return response

        try:
            response = retry_call(
                _call,
                is_retryable=_is_retryable_request_error,
                max_retries=self._settings.max_retries,
                operation="newsapi_fetch",
            )
        except Exception as error:  # noqa: BLE001
            raise _map_request_error(error) from error

        data = response.json()
        if data.get("status") == "error":
            code = str(data.get("code", "")).lower()
            message = data.get("message", "NewsAPI returned an unknown error")
            if "apikey" in code:
                raise ProviderAuthError(message)
            if "rate" in code:
                raise ProviderRateLimitError(message)
            raise UpstreamDataError(message)

        raw_articles = data.get("articles")
        if not isinstance(raw_articles, list):
            raise UpstreamDataError("NewsAPI response missing 'articles' list")

        normalized: list[Article] = []
        for row in raw_articles:
            normalized.append(
                Article(
                    title=str((row.get("title") or "")).strip(),
                    description=str((row.get("description") or "")).strip(),
                    content=str((row.get("content") or "")).strip(),
                    url=str((row.get("url") or "")).strip(),
                    source=str((row.get("source") or {}).get("name", "NewsAPI")).strip(),
                    published_at=str((row.get("publishedAt") or "")).strip(),
                )
            )
        return normalized

    @staticmethod
    def as_dicts(articles: list[Article]) -> list[dict]:
        return [asdict(article) for article in articles]


def _is_retryable_request_error(error: Exception) -> bool:
    if isinstance(error, requests.Timeout):
        return True
    if isinstance(error, requests.ConnectionError):
        return True
    if isinstance(error, requests.HTTPError):
        response = error.response
        return bool(response is not None and response.status_code in {429, 500, 502, 503, 504})
    return False


def _map_request_error(error: Exception) -> Exception:
    if isinstance(error, requests.Timeout):
        return ProviderTimeoutError("NewsAPI request timed out")
    if isinstance(error, requests.HTTPError):
        response = error.response
        status = response.status_code if response is not None else "unknown"
        if status == 401:
            return ProviderAuthError("NewsAPI authentication failed. Check NEWS_API_KEY.")
        if status == 429:
            return ProviderRateLimitError("NewsAPI rate limit reached")
        return UpstreamDataError(f"NewsAPI request failed with status {status}")
    if isinstance(error, requests.RequestException):
        return UpstreamDataError(f"NewsAPI request failed: {error}")
    return error
