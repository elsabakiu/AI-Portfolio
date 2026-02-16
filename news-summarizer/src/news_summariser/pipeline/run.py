"""Pipeline orchestration for fetch -> summarise -> sentiment -> report."""

from __future__ import annotations

import asyncio
import logging

from news_summariser.config import Settings
from news_summariser.pipeline.errors import NewsSummariserError
from news_summariser.pipeline.models import Article, FailureRecord, ProcessedArticle, RunResult
from news_summariser.processing.dedupe import dedupe_articles
from news_summariser.processing.sentiment import build_sentiment_prompt
from news_summariser.processing.summariser import build_summary_prompt
from news_summariser.providers.cohere_client import CohereClient
from news_summariser.providers.gdelt_client import GdeltClient
from news_summariser.providers.newsapi_client import NewsApiClient
from news_summariser.providers.openai_client import OpenAIClient
from news_summariser.reporting.metrics import MetricsCollector
from news_summariser.utils.time import monotonic_ms, utc_now_iso

logger = logging.getLogger(__name__)


class PipelineRunner:
    def __init__(
        self,
        *,
        settings: Settings,
        news_client: NewsApiClient | None = None,
        gdelt_client: GdeltClient | None = None,
        openai_client: OpenAIClient | None = None,
        cohere_client: CohereClient | None = None,
    ) -> None:
        self.settings = settings
        self.news_client = news_client or NewsApiClient(settings)
        self.gdelt_client = gdelt_client or GdeltClient(settings)
        self.openai_client = openai_client or OpenAIClient(settings)
        self.cohere_client = cohere_client or CohereClient(settings)

    def fetch_articles(
        self,
        *,
        source: str,
        category: str | None,
        query: str | None,
        limit: int,
        language: str,
    ) -> list[Article]:
        providers: list[str]
        if source == "all":
            providers = ["newsapi", "gdelt"]
        else:
            providers = [source]

        output: list[Article] = []
        for provider in providers:
            started = monotonic_ms()
            try:
                if provider == "newsapi":
                    output.extend(
                        self.news_client.fetch_articles(
                            category=category,
                            query=query,
                            limit=limit,
                            language=language,
                        )
                    )
                else:
                    output.extend(
                        self.gdelt_client.fetch_articles(
                            category=category,
                            query=query,
                            limit=limit,
                            language=language,
                        )
                    )
            except NewsSummariserError:
                logger.error("Provider fetch failed", extra={"event": "fetch_failed", "provider": provider})
                logger.debug("Provider fetch failed with trace", exc_info=True)
            finally:
                logger.info(
                    "Provider fetch finished",
                    extra={
                        "event": "fetch_finished",
                        "provider": provider,
                        "latency_ms": round(monotonic_ms() - started, 2),
                    },
                )

        deduped = dedupe_articles(output)
        return deduped[:limit]

    def run(
        self,
        *,
        run_id: str,
        source: str,
        category: str | None,
        query: str | None,
        limit: int,
        language: str,
        mode: str,
    ) -> RunResult:
        metrics = MetricsCollector()
        logger.info("Run started", extra={"event": "run_started"})

        fetch_start = monotonic_ms()
        articles = self.fetch_articles(
            source=source,
            category=category,
            query=query,
            limit=limit,
            language=language,
        )
        metrics.record_stage_latency("fetch", monotonic_ms() - fetch_start)

        if mode == "async":
            processed, failures = asyncio.run(self._process_articles_async(articles, metrics))
        else:
            processed, failures = self._process_articles_sync(articles, metrics)

        metrics.set_counts(
            fetched=len(articles),
            processed=len(articles),
            succeeded=len(processed),
            failed=len(failures),
        )

        result = RunResult(
            run_id=run_id,
            source=source,
            category=category,
            query=query,
            language=language,
            mode=mode,
            requested_limit=limit,
            generated_at=utc_now_iso(),
            articles=processed,
            failures=failures,
            metrics=metrics.metrics,
        )
        logger.info("Run finished", extra={"event": "run_finished"})
        return result

    def _process_articles_sync(
        self,
        articles: list[Article],
        metrics: MetricsCollector,
    ) -> tuple[list[ProcessedArticle], list[FailureRecord]]:
        processed: list[ProcessedArticle] = []
        failures: list[FailureRecord] = []

        for article in articles:
            outcome = self._process_one_article(article, metrics)
            if isinstance(outcome, ProcessedArticle):
                processed.append(outcome)
            else:
                failures.append(outcome)
        return processed, failures

    async def _process_articles_async(
        self,
        articles: list[Article],
        metrics: MetricsCollector,
    ) -> tuple[list[ProcessedArticle], list[FailureRecord]]:
        semaphore = asyncio.Semaphore(self.settings.async_max_concurrent)

        async def _task(article: Article):
            async with semaphore:
                return await asyncio.to_thread(self._process_one_article, article, metrics)

        results = await asyncio.gather(*[_task(article) for article in articles], return_exceptions=True)
        processed: list[ProcessedArticle] = []
        failures: list[FailureRecord] = []

        for outcome in results:
            if isinstance(outcome, ProcessedArticle):
                processed.append(outcome)
            elif isinstance(outcome, FailureRecord):
                failures.append(outcome)
            else:
                logger.error("Unexpected async processing error", extra={"event": "process_unexpected"})
                logger.debug("Unexpected async processing error detail: %s", outcome)
                failures.append(FailureRecord(url="", title="", stage="unknown", error=str(outcome)))

        return processed, failures

    def _process_one_article(
        self,
        article: Article,
        metrics: MetricsCollector,
    ) -> ProcessedArticle | FailureRecord:
        started = monotonic_ms()
        try:
            summary_prompt = build_summary_prompt(article)
            summary_text, summary_usage = self._generate_with_fallback(summary_prompt, stage="summary")
            metrics.record_usage(
                provider=summary_usage.provider,
                input_tokens=summary_usage.input_tokens,
                output_tokens=summary_usage.output_tokens,
                estimated_cost_usd=summary_usage.estimated_cost_usd,
            )
            self._enforce_budget(metrics)

            sentiment_prompt = build_sentiment_prompt(summary_text)
            sentiment_text, sentiment_usage = self._generate_with_fallback(sentiment_prompt, stage="sentiment")
            metrics.record_usage(
                provider=sentiment_usage.provider,
                input_tokens=sentiment_usage.input_tokens,
                output_tokens=sentiment_usage.output_tokens,
                estimated_cost_usd=sentiment_usage.estimated_cost_usd,
            )
            self._enforce_budget(metrics)

            if self.settings.debug_log_article_text:
                logger.debug(
                    "Article text used for prompts",
                    extra={"event": "article_debug", "article_url": article.url},
                )

            logger.info(
                "Article processed",
                extra={
                    "event": "article_processed",
                    "article_url": article.url,
                    "latency_ms": round(monotonic_ms() - started, 2),
                },
            )
            metrics.record_stage_latency("article_process", monotonic_ms() - started)
            return ProcessedArticle(
                title=article.title,
                description=article.description,
                content=article.content,
                url=article.url,
                source=article.source,
                published_at=article.published_at,
                summary=summary_text,
                sentiment=sentiment_text,
            )
        except Exception as error:  # noqa: BLE001
            logger.warning(
                "Article failed",
                extra={"event": "article_failed", "article_url": article.url, "stage": "process"},
            )
            logger.debug("Article failed with trace", exc_info=True)
            metrics.record_stage_latency("article_process", monotonic_ms() - started)
            return FailureRecord(
                url=article.url,
                title=article.title,
                stage="process",
                error=str(error),
            )

    def _generate_with_fallback(self, prompt: str, *, stage: str):
        if stage == "sentiment":
            primary = "cohere"
        else:
            primary = self.settings.llm_primary if self.settings.llm_primary in {"openai", "cohere"} else "openai"
        ordered = [primary, "cohere" if primary == "openai" else "openai"]

        errors: list[str] = []
        for provider in ordered:
            started = monotonic_ms()
            try:
                logger.info("Calling LLM provider", extra={"event": "llm_call", "provider": provider, "stage": stage})
                if provider == "openai":
                    text, usage = self.openai_client.generate(prompt)
                else:
                    text, usage = self.cohere_client.generate(prompt)

                logger.info(
                    "LLM provider succeeded",
                    extra={
                        "event": "llm_success",
                        "provider": provider,
                        "stage": stage,
                        "latency_ms": round(monotonic_ms() - started, 2),
                    },
                )
                return text, usage
            except Exception as error:  # noqa: BLE001
                errors.append(f"{provider}: {error}")
                logger.warning(
                    "LLM provider failed: provider=%s stage=%s error=%s",
                    provider,
                    stage,
                    error,
                    extra={"event": "llm_failed", "provider": provider, "stage": stage},
                )
                logger.debug("LLM provider failure trace", exc_info=True)

        raise RuntimeError(f"All LLM providers failed during {stage}: {' | '.join(errors)}")

    def _enforce_budget(self, metrics: MetricsCollector) -> None:
        total = metrics.total_estimated_cost()
        if total >= self.settings.daily_budget:
            raise RuntimeError(
                f"Daily budget ${self.settings.daily_budget:.2f} exceeded. Current estimate: ${total:.6f}"
            )
