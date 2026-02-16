"""Command line interface for the News Summariser."""

from __future__ import annotations

import argparse
import logging

from news_summariser.config import load_settings
from news_summariser.logging_config import configure_logging, set_run_id
from news_summariser.pipeline.errors import ConfigError, NewsSummariserError
from news_summariser.pipeline.run import PipelineRunner
from news_summariser.reporting.console_report import build_console_report, build_summary_line
from news_summariser.reporting.json_report import write_json_report
from news_summariser.utils.time import new_run_id

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarise current news with sentiment and cost tracking.")
    parser.add_argument("--source", choices=["all", "newsapi", "gdelt"], default="all")
    parser.add_argument("--category", default=None)
    parser.add_argument("--query", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output", choices=["console", "json"], default="console")
    parser.add_argument("--out-file", default=None)
    parser.add_argument("--language", default="en")
    parser.add_argument("--mode", choices=["sync", "async"], default="sync")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = load_settings()
    configure_logging(level=args.log_level, json_logs=settings.log_json)

    run_id = new_run_id()
    set_run_id(run_id)

    limit = args.limit if args.limit and args.limit > 0 else settings.default_limit
    limit = min(limit, settings.max_limit)
    category = args.category or settings.default_category

    try:
        settings.validate_runtime(args.source)
        runner = PipelineRunner(settings=settings)
        result = runner.run(
            run_id=run_id,
            source=args.source,
            category=category,
            query=args.query,
            limit=limit,
            language=args.language,
            mode=args.mode,
        )

        if args.output == "json":
            print(write_json_report(result, out_file=args.out_file))
        else:
            print(build_console_report(result))
            print(build_summary_line(result))
            if args.out_file:
                write_json_report(result, out_file=args.out_file)
                print(f"JSON report written: {args.out_file}")

        failure_ratio = (result.metrics.n_failed / max(1, result.metrics.n_processed))
        return 1 if failure_ratio > 0.40 else 0
    except ConfigError as error:
        LOGGER.error("Configuration error: %s", error)
        LOGGER.debug("Configuration error trace", exc_info=True)
        print(f"Configuration error: {error}")
        return 2
    except NewsSummariserError as error:
        LOGGER.error("Runtime error: %s", error)
        LOGGER.debug("Runtime error trace", exc_info=True)
        print(f"Runtime error: {error}")
        return 1
    except Exception as error:  # noqa: BLE001
        LOGGER.error("Unexpected error: %s", error)
        LOGGER.debug("Unexpected error trace", exc_info=True)
        print(f"Unexpected error: {error}")
        return 1
