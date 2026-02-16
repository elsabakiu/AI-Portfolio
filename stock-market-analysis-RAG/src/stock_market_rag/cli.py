"""CLI entrypoint for stock market RAG."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from stock_market_rag.config import load_settings
from stock_market_rag.logging_config import configure_logging, set_run_id
from stock_market_rag.pipeline.errors import ConfigError, StockRagError
from stock_market_rag.pipeline.run import RagPipeline
from stock_market_rag.reporting.console_report import build_console_report
from stock_market_rag.reporting.json_report import write_json_report
from stock_market_rag.utils.time import new_run_id

LOGGER = logging.getLogger(__name__)

DEFAULT_QUESTIONS = [
    "Which company appears to have the strongest near-term growth outlook and why?",
    "What are the biggest product or execution risks called out by management across these companies?",
    "If you were prioritizing one AI-related investment thesis from these documents, what is it and what evidence supports it?",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run stock market RAG over local filings/transcripts dataset.")
    parser.add_argument("--dataset-root", default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--question", action="append", dest="questions")
    parser.add_argument("--output", choices=["console", "json"], default="console")
    parser.add_argument("--out-file", default=None)
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()
    configure_logging(level=args.log_level, json_logs=settings.log_json)

    run_id = new_run_id()
    set_run_id(run_id)

    dataset_root = settings.dataset_root if args.dataset_root is None else Path(args.dataset_root).resolve()
    top_k = max(1, args.top_k or settings.top_k)
    questions = args.questions or DEFAULT_QUESTIONS

    try:
        settings.validate()
        pipeline = RagPipeline(settings=settings)
        result = pipeline.run(
            run_id=run_id,
            dataset_root=dataset_root,
            questions=questions,
            top_k=top_k,
        )

        if args.output == "json":
            print(write_json_report(result, out_file=args.out_file))
        else:
            print(build_console_report(result))
            if args.out_file:
                write_json_report(result, out_file=args.out_file)
                print(f"JSON report written: {args.out_file}")
        return 0
    except ConfigError as error:
        LOGGER.error("Configuration error: %s", error)
        LOGGER.debug("Configuration trace", exc_info=True)
        print(f"Configuration error: {error}")
        return 2
    except StockRagError as error:
        LOGGER.error("Runtime error: %s", error)
        LOGGER.debug("Runtime trace", exc_info=True)
        print(f"Runtime error: {error}")
        return 1
    except Exception as error:  # noqa: BLE001
        LOGGER.error("Unexpected error: %s", error)
        LOGGER.debug("Unexpected trace", exc_info=True)
        print(f"Unexpected error: {error}")
        return 1
