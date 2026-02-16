"""Article deduplication."""

from __future__ import annotations

from news_summariser.pipeline.models import Article


def dedupe_articles(articles: list[Article]) -> list[Article]:
    seen: set[str] = set()
    output: list[Article] = []
    for article in articles:
        key = article.url.strip().lower() or f"{article.title.strip().lower()}::{article.source.strip().lower()}"
        if key in seen:
            continue
        seen.add(key)
        output.append(article)
    return output
