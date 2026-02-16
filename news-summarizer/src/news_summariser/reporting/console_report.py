"""Console rendering for run reports."""

from __future__ import annotations

from news_summariser.pipeline.models import RunResult


def build_console_report(result: RunResult) -> str:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("News Summariser Run")
    lines.append("=" * 80)
    lines.append(f"run_id: {result.run_id}")
    lines.append(f"source: {result.source}")
    lines.append(f"category: {result.category or '-'}")
    lines.append(f"query: {result.query or '-'}")
    lines.append(f"language: {result.language}")
    lines.append(f"mode: {result.mode}")
    lines.append("")

    for index, article in enumerate(result.articles, start=1):
        lines.append(f"{index}. {article.title}")
        lines.append(f"   source={article.source} published_at={article.published_at}")
        lines.append(f"   url={article.url}")
        lines.append(f"   summary={article.summary}")
        lines.append(f"   sentiment={article.sentiment}")
        lines.append("")

    lines.append("Metrics")
    lines.append("-" * 80)
    lines.append(f"n_fetched={result.metrics.n_fetched}")
    lines.append(f"n_processed={result.metrics.n_processed}")
    lines.append(f"n_succeeded={result.metrics.n_succeeded}")
    lines.append(f"n_failed={result.metrics.n_failed}")

    for stage, latency in sorted(result.metrics.stage_latency_ms.items()):
        lines.append(f"avg_latency_{stage}_ms={latency}")

    cost_total = 0.0
    for provider, usage in sorted(result.metrics.token_usage_by_provider.items()):
        lines.append(
            f"provider={provider} requests={usage.requests} input_tokens={usage.input_tokens} "
            f"output_tokens={usage.output_tokens} estimated_cost_usd={usage.estimated_cost_usd:.6f}"
        )
        cost_total += usage.estimated_cost_usd

    lines.append(f"estimated_total_cost_usd={cost_total:.6f}")
    lines.append("=" * 80)
    return "\n".join(lines)


def build_summary_line(result: RunResult) -> str:
    total_cost = sum(u.estimated_cost_usd for u in result.metrics.token_usage_by_provider.values())
    return (
        f"Run complete: processed={result.metrics.n_processed} succeeded={result.metrics.n_succeeded} "
        f"failed={result.metrics.n_failed} estimated_cost_usd={total_cost:.6f}"
    )
