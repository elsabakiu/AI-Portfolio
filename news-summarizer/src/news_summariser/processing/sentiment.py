"""Sentiment prompt construction."""

from __future__ import annotations

SENTIMENT_PROMPT_TEMPLATE = """Analyse sentiment for the summary below.
Return overall sentiment (positive/neutral/negative), confidence (0-100), and short rationale.

Summary: {summary}
"""


def build_sentiment_prompt(summary: str) -> str:
    return SENTIMENT_PROMPT_TEMPLATE.format(summary=summary)
