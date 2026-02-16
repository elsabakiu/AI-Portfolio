"""Console report builder."""

from __future__ import annotations

from stock_market_rag.pipeline.models import RagRunResult


def build_console_report(result: RagRunResult) -> str:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("Stock Market RAG Run")
    lines.append("=" * 80)
    lines.append(f"run_id: {result.run_id}")
    lines.append(f"dataset_root: {result.dataset_root}")
    lines.append(f"embedding_model: {result.embedding_model}")
    lines.append(f"chat_model: {result.chat_model}")
    lines.append("")

    for idx, item in enumerate(result.questions, start=1):
        lines.append(f"Q{idx}: {item.question}")
        lines.append("Answer:")
        lines.append(item.answer)
        lines.append("Retrieved:")
        for retrieved in item.retrieved:
            lines.append(
                f"- {retrieved.chunk_id} source={retrieved.source} similarity={retrieved.similarity:.4f} "
                f"preview={retrieved.text_preview}"
            )
        lines.append("")

    metrics = result.metrics
    lines.append("Metrics")
    lines.append("-" * 80)
    lines.append(f"docs_indexed={metrics.docs_indexed}")
    lines.append(f"chunks_indexed={metrics.chunks_indexed}")
    lines.append(f"embedding_calls={metrics.embedding_calls}")
    lines.append(f"chat_calls={metrics.chat_calls}")
    lines.append(f"retrieval_requests={metrics.retrieval_requests}")
    lines.append(f"failed_docs={metrics.failed_docs}")
    for stage, value in sorted(metrics.stage_latency_ms.items()):
        lines.append(f"avg_latency_{stage}_ms={value}")

    lines.append("=" * 80)
    return "\n".join(lines)
