"""Application configuration loading and validation."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from news_summariser.pipeline.errors import ConfigError

load_dotenv()


def _int_env(name: str, default: int, minimum: int = 0) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, value)


def _float_env(name: str, default: float, minimum: float = 0.0) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, value)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    cohere_api_key: str | None
    news_api_key: str | None
    openai_model: str
    cohere_model: str
    request_timeout: int
    max_retries: int
    openai_rpm: int
    cohere_rpm: int
    news_api_rpm: int
    gdelt_rpm: int
    daily_budget: float
    default_category: str
    default_limit: int
    max_limit: int
    async_max_concurrent: int
    llm_primary: str
    log_json: bool
    debug_log_article_text: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            cohere_api_key=os.getenv("COHERE_API_KEY"),
            news_api_key=os.getenv("NEWS_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            cohere_model=os.getenv("COHERE_MODEL", "command-a-03-2025"),
            request_timeout=_int_env("REQUEST_TIMEOUT", 30, minimum=1),
            max_retries=_int_env("MAX_RETRIES", 3, minimum=0),
            openai_rpm=_int_env("OPENAI_RPM", 500, minimum=1),
            cohere_rpm=_int_env("COHERE_RPM", 50, minimum=1),
            news_api_rpm=_int_env("NEWS_API_RPM", 100, minimum=1),
            gdelt_rpm=_int_env("GDELT_RPM", 120, minimum=1),
            daily_budget=_float_env("DAILY_BUDGET", 5.0, minimum=0.0),
            default_category=os.getenv("DEFAULT_CATEGORY", "technology"),
            default_limit=_int_env("DEFAULT_LIMIT", 5, minimum=1),
            max_limit=_int_env("MAX_LIMIT", 20, minimum=1),
            async_max_concurrent=_int_env("ASYNC_MAX_CONCURRENT", 4, minimum=1),
            llm_primary=os.getenv("LLM_PRIMARY", "openai").strip().lower(),
            log_json=os.getenv("LOG_JSON", "1") in {"1", "true", "True", "yes", "YES"},
            debug_log_article_text=os.getenv("DEBUG_LOG_ARTICLE_TEXT", "0")
            in {"1", "true", "True", "yes", "YES"},
        )

    def validate_runtime(self, source: str) -> None:
        missing: list[str] = []
        if source in {"newsapi", "all"} and not self.news_api_key:
            missing.append("NEWS_API_KEY")
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.cohere_api_key:
            missing.append("COHERE_API_KEY")

        if missing:
            joined = ", ".join(sorted(set(missing)))
            raise ConfigError(
                "Missing required configuration: "
                f"{joined}. Add these keys to your environment or .env file. "
                "See docs/api_keys_setup.md for setup guidance."
            )


def load_settings() -> Settings:
    return Settings.from_env()
