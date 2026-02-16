"""Backward-compatible config helpers."""

from __future__ import annotations

import os

from stock_market_rag.config import load_settings


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def get_embedding_model() -> str:
    return load_settings().embedding_model


def get_chat_model() -> str:
    return load_settings().chat_model
