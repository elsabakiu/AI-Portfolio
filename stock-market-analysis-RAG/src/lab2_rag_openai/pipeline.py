"""Backward-compatible pipeline helpers."""

from __future__ import annotations

from pathlib import Path

from lab2_rag_openai.chunking import Chunk
from lab2_rag_openai.openai_client import OpenAIService
from lab2_rag_openai.vector_store import EmbeddedChunk, InMemoryVectorStore
from stock_market_rag.config import load_settings
from stock_market_rag.pipeline.run import RagPipeline


def load_document(path: Path) -> str:
    from stock_market_rag.indexing.io_utils import load_document as _load_document

    return _load_document(path)


def discover_documents(dataset_root: Path) -> list[Path]:
    from stock_market_rag.indexing.io_utils import discover_documents as _discover_documents

    return _discover_documents(dataset_root)


def build_index_from_documents(
    document_paths: list[Path],
    dataset_root: Path,
    service: OpenAIService,
    chunk_size: int = 1000,
    overlap: int = 120,
    embedding_batch_size: int = 100,
) -> tuple[InMemoryVectorStore, list[Chunk]]:
    settings = load_settings()
    settings = settings.__class__(
        openai_api_key=settings.openai_api_key,
        embedding_model=settings.embedding_model,
        chat_model=settings.chat_model,
        embedding_batch_size=embedding_batch_size,
        request_timeout=settings.request_timeout,
        max_retries=settings.max_retries,
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        top_k=settings.top_k,
        log_json=settings.log_json,
        dataset_root=settings.dataset_root,
    )
    pipeline = RagPipeline(settings=settings, provider=service.provider)

    from stock_market_rag.reporting.metrics import MetricsCollector

    metrics = MetricsCollector()
    store_new, chunks_new = pipeline.build_index_from_documents(
        document_paths=document_paths,
        dataset_root=dataset_root,
        metrics=metrics,
    )

    store = InMemoryVectorStore()
    store._store = store_new
    chunks = [Chunk(id=c.id, text=c.text, source=c.source) for c in chunks_new]
    return store, chunks


def build_index(
    document_path: Path,
    source_name: str,
    service: OpenAIService,
    chunk_size: int = 1000,
    overlap: int = 120,
    embedding_batch_size: int = 100,
) -> tuple[InMemoryVectorStore, list[Chunk]]:
    return build_index_from_documents(
        document_paths=[document_path],
        dataset_root=document_path.parent,
        service=service,
        chunk_size=chunk_size,
        overlap=overlap,
        embedding_batch_size=embedding_batch_size,
    )


def retrieve_top_k_chunks(
    store: InMemoryVectorStore,
    query: str,
    service: OpenAIService,
    top_k: int = 3,
) -> list[tuple[EmbeddedChunk, float]]:
    query_embedding = service.embed_texts([query])[0]
    return store.search_with_scores(query_embedding=query_embedding, top_k=top_k)


def format_context_for_llm(retrieved_with_scores: list[tuple[EmbeddedChunk, float]]) -> list[str]:
    context_blocks: list[str] = []
    for idx, (item, score) in enumerate(retrieved_with_scores, start=1):
        context_blocks.append(
            f"[Context {idx}] source={item.chunk.source} chunk_id={item.chunk.id} similarity={score:.4f}\n{item.chunk.text}"
        )
    return context_blocks


def rag_query(
    store: InMemoryVectorStore,
    question: str,
    service: OpenAIService,
    top_k: int = 3,
) -> tuple[str, list[EmbeddedChunk], list[tuple[EmbeddedChunk, float]]]:
    retrieved_with_scores = retrieve_top_k_chunks(store=store, query=question, service=service, top_k=top_k)
    retrieved = [item for item, _ in retrieved_with_scores]
    context_chunks = format_context_for_llm(retrieved_with_scores)
    answer = service.answer_with_context(question=question, context_chunks=context_chunks)
    return answer, retrieved, retrieved_with_scores


def answer_question(
    store: InMemoryVectorStore,
    question: str,
    service: OpenAIService,
    top_k: int = 3,
) -> tuple[str, list[EmbeddedChunk]]:
    answer, retrieved, _ = rag_query(
        store=store,
        question=question,
        service=service,
        top_k=top_k,
    )
    return answer, retrieved
