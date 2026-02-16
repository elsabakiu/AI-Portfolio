"""Gradio UI entrypoint for News Summariser."""

from __future__ import annotations

from typing import Any

from news_summariser.config import load_settings
from news_summariser.logging_config import configure_logging, set_run_id
from news_summariser.pipeline.run import PipelineRunner
from news_summariser.utils.time import new_run_id

NEWS_CATEGORIES = [
    "business",
    "entertainment",
    "general",
    "health",
    "science",
    "sports",
    "technology",
]
NEWS_PROVIDER_CHOICES = ["all", "newsapi", "gdelt"]


def _parse_num_articles(raw_value: Any, default: int, max_limit: int) -> int:
    try:
        value = int(float(raw_value))
    except (TypeError, ValueError):
        value = default
    value = max(1, value)
    return min(value, max_limit)


def _normalize_news_provider(raw_value: Any) -> str:
    normalized = str(raw_value or "all").strip().lower()
    return normalized if normalized in NEWS_PROVIDER_CHOICES else "all"


def _format_report(result) -> str:  # noqa: ANN001
    if not result.articles:
        return (
            "## News Summariser Report\n"
            f"- Run ID: `{result.run_id}`\n"
            f"- Category: `{result.category or '-'}`\n"
            f"- Requested articles: `{result.requested_limit}`\n"
            f"- News provider: `{result.source}`\n\n"
            "No articles found for the selected inputs."
        )

    lines = [
        "## News Summariser Report",
        f"- Run ID: `{result.run_id}`",
        f"- Category: `{result.category or '-'}`",
        f"- Requested articles: `{result.requested_limit}`",
        f"- News provider: `{result.source}`",
        f"- Mode: `{result.mode}`",
        "",
    ]

    for idx, article in enumerate(result.articles, 1):
        lines.extend(
            [
                f"### {idx}. {article.title}",
                f"- Source: {article.source}",
                f"- Published: {article.published_at}",
                f"- URL: {article.url}",
                "",
                "**Summary**",
                article.summary,
                "",
                "**Sentiment**",
                article.sentiment,
                "",
            ]
        )

    if result.failures:
        lines.append("## Failures")
        for failure in result.failures:
            lines.append(f"- {failure.stage}: {failure.title or failure.url or 'Unknown article'} -> {failure.error}")
        lines.append("")

    metrics = result.metrics
    lines.extend(
        [
            "## Metrics",
            f"- Fetched: {metrics.n_fetched}",
            f"- Processed: {metrics.n_processed}",
            f"- Succeeded: {metrics.n_succeeded}",
            f"- Failed: {metrics.n_failed}",
        ]
    )

    total_cost = 0.0
    for provider, usage in metrics.token_usage_by_provider.items():
        lines.append(
            f"- {provider}: requests={usage.requests}, input_tokens={usage.input_tokens}, "
            f"output_tokens={usage.output_tokens}, estimated_cost=${usage.estimated_cost_usd:.6f}"
        )
        total_cost += usage.estimated_cost_usd

    lines.append(f"- Estimated total cost: ${total_cost:.6f}")
    return "\n".join(lines)


def _format_result_rows(result) -> list[list[str]]:  # noqa: ANN001
    rows: list[list[str]] = []
    for article in result.articles:
        rows.append(
            [
                article.title,
                article.source,
                article.published_at,
                article.summary,
                article.sentiment,
                article.url,
            ]
        )
    return rows


def run_app(
    category: str,
    num_articles: int,
    use_async: bool,
    news_provider: str,
) -> tuple[str, list[list[str]]]:
    settings = load_settings()
    configure_logging(level="INFO", json_logs=settings.log_json)
    set_run_id(new_run_id())
    resolved_category = (category or settings.default_category).strip().lower()
    if resolved_category not in NEWS_CATEGORIES:
        resolved_category = settings.default_category

    limit = _parse_num_articles(num_articles, default=settings.default_limit, max_limit=settings.max_limit)
    source = _normalize_news_provider(news_provider)
    mode = "async" if use_async else "sync"

    try:
        settings.validate_runtime(source)
        runner = PipelineRunner(settings=settings)
        result = runner.run(
            run_id="gradio-session",
            source=source,
            category=resolved_category,
            query=None,
            limit=limit,
            language="en",
            mode=mode,
        )
        report = _format_report(result)
        rows = _format_result_rows(result)
        return report, rows
    except Exception as error:  # noqa: BLE001
        return f"## Error\n\n{error}", []


def build_demo():
    import gradio as gr

    settings = load_settings()

    with gr.Blocks(title="News Summariser") as demo:
        gr.Markdown("# News Summariser")
        gr.Markdown("Fetch headlines, summarise with LLMs, and get sentiment + cost analysis.")

        with gr.Row():
            category = gr.Dropdown(
                label="Category",
                choices=NEWS_CATEGORIES,
                value=settings.default_category if settings.default_category in NEWS_CATEGORIES else "technology",
            )
            num_articles = gr.Slider(
                minimum=1,
                maximum=settings.max_limit,
                step=1,
                value=settings.default_limit,
                label="Number of articles",
            )
            news_provider = gr.Dropdown(
                label="News provider",
                choices=NEWS_PROVIDER_CHOICES,
                value="all",
            )

        use_async = gr.Checkbox(value=False, label="Use async processing")
        run_button = gr.Button("Run Summariser", variant="primary")

        report_output = gr.Markdown(label="Report")
        results_output = gr.Dataframe(
            headers=["Title", "Source", "Published", "Summary", "Sentiment", "URL"],
            datatype=["str", "str", "str", "str", "str", "str"],
            col_count=(6, "fixed"),
            row_count=(0, "dynamic"),
            interactive=False,
            wrap=True,
            label="Summarised Results",
        )

        run_button.click(
            fn=run_app,
            inputs=[category, num_articles, use_async, news_provider],
            outputs=[report_output, results_output],
        )

    return demo


def main() -> None:
    demo = build_demo()
    demo.launch()


if __name__ == "__main__":
    main()
