"""Normalization helpers."""

from __future__ import annotations

from typing import Any

from news_summariser.pipeline.errors import UpstreamDataError
from news_summariser.pipeline.models import Article


def normalize_article(value: Any) -> Article:
    if isinstance(value, Article):
        return value

    if isinstance(value, dict):
        getter = value.get
    else:
        getter = lambda key, default="": getattr(value, key, default)

    title = str(getter("title", "") or "").strip()
    url = str(getter("url", "") or "").strip()
    if not title and not url:
        raise UpstreamDataError("Article missing both title and url")

    return Article(
        title=title,
        description=str(getter("description", "") or "").strip(),
        content=str(getter("content", "") or "").strip(),
        url=url,
        source=str(getter("source", "Unknown") or "Unknown").strip(),
        published_at=str(getter("published_at", "") or "").strip(),
    )
