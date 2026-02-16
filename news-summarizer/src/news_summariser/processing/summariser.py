"""Summary prompt construction."""

from __future__ import annotations

from news_summariser.pipeline.models import Article


SUMMARY_PROMPT_TEMPLATE = """Summarise this news article in 2-3 sentences.
Include key facts and avoid speculation.

Title: {title}
Description: {description}
Content: {content}
"""


def build_summary_prompt(article: Article) -> str:
    return SUMMARY_PROMPT_TEMPLATE.format(
        title=article.title,
        description=article.description,
        content=article.content[:1000],
    )
