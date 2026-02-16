"""RAG orchestration pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

from stock_market_rag.config import Settings
from stock_market_rag.indexing.chunking import recursive_character_chunking
from stock_market_rag.indexing.io_utils import discover_documents, load_document
from stock_market_rag.pipeline.errors import RetrievalError, UpstreamDataError
from stock_market_rag.pipeline.models import Chunk, EmbeddedChunk, QuestionResult, RagRunResult, RetrievedChunk
from stock_market_rag.providers.openai_client import OpenAIProvider
from stock_market_rag.reporting.metrics import MetricsCollector
from stock_market_rag.retrieval.vector_store import InMemoryVectorStore
from stock_market_rag.utils.time import monotonic_ms, utc_now_iso

logger = logging.getLogger(__name__)


class RagPipeline:
    def __init__(self, *, settings: Settings, provider: OpenAIProvider | None = None) -> None:
        self.settings = settings
        self.provider = provider or OpenAIProvider(settings)

    def discover_documents(self, dataset_root: Path) -> list[Path]:
        return discover_documents(dataset_root)

    def build_index_from_documents(
        self,
        *,
        document_paths: list[Path],
        dataset_root: Path,
        metrics: MetricsCollector,
    ) -> tuple[InMemoryVectorStore, list[Chunk]]:
        store = InMemoryVectorStore()
        all_chunks: list[Chunk] = []

        for path in document_paths:
            source = str(path.relative_to(dataset_root)).replace("/", "-")
            started = monotonic_ms()
            try:
                text = load_document(path)
                chunks = recursive_character_chunking(
                    text=text,
                    source=source,
                    chunk_size=self.settings.chunk_size,
                    overlap=self.settings.chunk_overlap,
                )
                if not chunks:
                    continue

                embeddings = self.provider.embed_texts(
                    [c.text for c in chunks],
                    model=self.settings.embedding_model,
                    batch_size=self.settings.embedding_batch_size,
                )
                metrics.metrics.embedding_calls += 1

                store.add([
                    EmbeddedChunk(chunk=chunk, embedding=embedding)
                    for chunk, embedding in zip(chunks, embeddings)
                ])
                all_chunks.extend(chunks)
                metrics.metrics.docs_indexed += 1
                metrics.metrics.chunks_indexed += len(chunks)
                logger.info(
                    "Indexed document",
                    extra={"event": "doc_indexed", "doc": str(path), "chunks": len(chunks)},
                )
            except UpstreamDataError:
                metrics.metrics.failed_docs += 1
                logger.warning("Skipping unreadable document: %s", path, extra={"event": "doc_skipped"})
                logger.debug("Unreadable document trace", exc_info=True)
            except Exception:
                metrics.metrics.failed_docs += 1
                logger.warning("Failed indexing document: %s", path, extra={"event": "doc_failed"})
                logger.debug("Document indexing trace", exc_info=True)
            finally:
                metrics.record_stage_latency("index_document", monotonic_ms() - started)

        return store, all_chunks

    def retrieve(self, *, store: InMemoryVectorStore, query: str, top_k: int, metrics: MetricsCollector):
        started = monotonic_ms()
        try:
            query_embedding = self.provider.embed_texts([query], model=self.settings.embedding_model, batch_size=1)[0]
            metrics.metrics.embedding_calls += 1
            matches = store.search_with_scores(query_embedding=query_embedding, top_k=top_k)
            metrics.metrics.retrieval_requests += 1
            return matches
        except Exception as error:  # noqa: BLE001
            raise RetrievalError(f"Retrieval failed for query: {error}") from error
        finally:
            metrics.record_stage_latency("retrieval", monotonic_ms() - started)

    @staticmethod
    def _format_context(matches: list[tuple[EmbeddedChunk, float]]) -> list[str]:
        contexts: list[str] = []
        for idx, (item, score) in enumerate(matches, start=1):
            contexts.append(
                f"[Context {idx}] source={item.chunk.source} chunk_id={item.chunk.id} similarity={score:.4f}\n{item.chunk.text}"
            )
        return contexts

    def answer_question(self, *, question: str, matches: list[tuple[EmbeddedChunk, float]], metrics: MetricsCollector) -> str:
        started = monotonic_ms()
        try:
            answer = self.provider.answer_with_context(
                question=question,
                context_chunks=self._format_context(matches),
                model=self.settings.chat_model,
            )
            metrics.metrics.chat_calls += 1
            return answer
        finally:
            metrics.record_stage_latency("answer", monotonic_ms() - started)

    def run(
        self,
        *,
        run_id: str,
        dataset_root: Path,
        questions: list[str],
        top_k: int,
    ) -> RagRunResult:
        metrics = MetricsCollector()
        doc_paths = self.discover_documents(dataset_root)
        if not doc_paths:
            raise UpstreamDataError(f"No supported documents found under {dataset_root}")

        store, _chunks = self.build_index_from_documents(
            document_paths=doc_paths,
            dataset_root=dataset_root,
            metrics=metrics,
        )

        outputs: list[QuestionResult] = []
        for question in questions:
            matches = self.retrieve(store=store, query=question, top_k=top_k, metrics=metrics)
            answer = self.answer_question(question=question, matches=matches, metrics=metrics)
            outputs.append(
                QuestionResult(
                    question=question,
                    answer=answer,
                    retrieved=[
                        RetrievedChunk(
                            chunk_id=item.chunk.id,
                            source=item.chunk.source,
                            similarity=score,
                            text_preview=item.chunk.text[:120].replace("\n", " "),
                        )
                        for item, score in matches
                    ],
                )
            )

        return RagRunResult(
            run_id=run_id,
            dataset_root=str(dataset_root),
            embedding_model=self.settings.embedding_model,
            chat_model=self.settings.chat_model,
            questions=outputs,
            metrics=metrics.metrics,
            generated_at=utc_now_iso(),
        )
