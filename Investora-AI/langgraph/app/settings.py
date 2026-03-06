from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import List

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class RunBehaviorConfig(BaseModel):
    run_date: str = ""
    graph_recursion_limit: int = Field(default=120, ge=10, le=2000)
    run_queue_wait_seconds: float = Field(default=90.0, ge=1.0, le=3600.0)
    skip_n8n_post: bool = False
    use_mock_data: bool = True
    stock_universe: str = ""


class ProviderConfig(BaseModel):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    synthesis_model: str = "gpt-4o-mini"
    sentry_dsn: str = ""
    cron_secret: str = ""
    cors_origins: List[str] = Field(default_factory=list)


class ConcurrencyConfig(BaseModel):
    tool_parallelism: int = Field(default=8, ge=1, le=64)
    rag_parallelism: int = Field(default=6, ge=1, le=64)
    synthesis_parallelism: int = Field(default=4, ge=1, le=64)


class FeatureToggles(BaseModel):
    trigger_weekly_digest: bool = True
    enable_post_candidates: bool = True


class PipelineTuningConfig(BaseModel):
    quality_weight: float = Field(default=0.55, ge=0.0, le=1.0)
    momentum_weight: float = Field(default=0.45, ge=0.0, le=1.0)
    evidence_top_n: int = 25
    rag_lookback_days: int = Field(default=42, ge=1, le=3650)
    rag_top_k: int = Field(default=5, ge=1, le=50)


class AppSettings(BaseModel):
    run: RunBehaviorConfig
    providers: ProviderConfig
    concurrency: ConcurrencyConfig
    features: FeatureToggles
    pipeline: PipelineTuningConfig



def _as_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}



def _as_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Invalid float for %s=%r; using default=%s", name, raw, default)
        return default



def _as_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid int for %s=%r; using default=%s", name, raw, default)
        return default


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    cors = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]

    try:
        settings = AppSettings(
            run=RunBehaviorConfig(
                run_date=os.environ.get("RUN_DATE", ""),
                graph_recursion_limit=_as_int("GRAPH_RECURSION_LIMIT", 120),
                run_queue_wait_seconds=_as_float("RUN_QUEUE_WAIT_SECONDS", 90.0),
                skip_n8n_post=_as_bool("SKIP_N8N_POST", False),
                use_mock_data=_as_bool("USE_MOCK_DATA", True),
                stock_universe=os.environ.get("STOCK_UNIVERSE", ""),
            ),
            providers=ProviderConfig(
                openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
                openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                synthesis_model=os.environ.get("SYNTHESIS_MODEL", "gpt-4o-mini"),
                sentry_dsn=os.environ.get("SENTRY_DSN", ""),
                cron_secret=os.environ.get("CRON_SECRET", ""),
                cors_origins=cors,
            ),
            concurrency=ConcurrencyConfig(
                tool_parallelism=_as_int("TOOL_PARALLELISM", 8),
                rag_parallelism=_as_int("RAG_PARALLELISM", 6),
                synthesis_parallelism=_as_int("SYNTHESIS_PARALLELISM", 4),
            ),
            features=FeatureToggles(
                trigger_weekly_digest=_as_bool("FEATURE_WEEKLY_DIGEST", True),
                enable_post_candidates=_as_bool("FEATURE_POST_CANDIDATES", True),
            ),
            pipeline=PipelineTuningConfig(
                quality_weight=_as_float("QUALITY_WEIGHT", 0.55),
                momentum_weight=_as_float("MOMENTUM_WEIGHT", 0.45),
                evidence_top_n=_as_int("EVIDENCE_TOP_N", 25),
                rag_lookback_days=_as_int("RAG_LOOKBACK_DAYS", 42),
                rag_top_k=_as_int("RAG_TOP_K", 5),
            ),
        )
    except ValidationError as exc:
        logger.warning("Settings validation failed; falling back to defaults: %s", exc)
        settings = AppSettings(
            run=RunBehaviorConfig(),
            providers=ProviderConfig(),
            concurrency=ConcurrencyConfig(),
            features=FeatureToggles(),
            pipeline=PipelineTuningConfig(),
        )

    if not settings.providers.openai_api_key and not settings.run.use_mock_data:
        logger.warning("OPENAI_API_KEY is missing while USE_MOCK_DATA=false; synthesis/planning may fail")

    return settings
