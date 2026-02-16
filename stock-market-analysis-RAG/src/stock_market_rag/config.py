"""Runtime configuration loader."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from stock_market_rag.pipeline.errors import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)


def _int_env(name: str, default: int, minimum: int = 0) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, value)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    embedding_model: str
    chat_model: str
    embedding_batch_size: int
    request_timeout: int
    max_retries: int
    chunk_size: int
    chunk_overlap: int
    top_k: int
    log_json: bool
    dataset_root: Path

    @classmethod
    def from_env(cls) -> "Settings":
        dataset_default = PROJECT_ROOT / "data" / "raw" / "investment_research_assistant"
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            embedding_batch_size=_int_env("EMBEDDING_BATCH_SIZE", 100, minimum=1),
            request_timeout=_int_env("REQUEST_TIMEOUT", 60, minimum=1),
            max_retries=_int_env("MAX_RETRIES", 6, minimum=0),
            chunk_size=_int_env("CHUNK_SIZE", 1000, minimum=100),
            chunk_overlap=_int_env("CHUNK_OVERLAP", 120, minimum=0),
            top_k=_int_env("TOP_K", 4, minimum=1),
            log_json=os.getenv("LOG_JSON", "1") in {"1", "true", "True", "yes", "YES"},
            dataset_root=Path(os.getenv("DATASET_ROOT", str(dataset_default))).resolve(),
        )

    def validate(self) -> None:
        if not self.openai_api_key:
            raise ConfigError(
                "Missing OPENAI_API_KEY. Add it to .env. See docs/api_keys_setup.md for setup."
            )
        if self.chunk_overlap >= self.chunk_size:
            raise ConfigError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")


def load_settings() -> Settings:
    return Settings.from_env()
