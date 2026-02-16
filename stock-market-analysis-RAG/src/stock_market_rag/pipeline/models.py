"""Pipeline models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class DocumentInfo:
    path: Path
    source: str
    chunk_count: int = 0


@dataclass
class Chunk:
    id: str
    text: str
    source: str


@dataclass
class EmbeddedChunk:
    chunk: Chunk
    embedding: list[float]


@dataclass
class RetrievedChunk:
    chunk_id: str
    source: str
    similarity: float
    text_preview: str


@dataclass
class QuestionResult:
    question: str
    answer: str
    retrieved: list[RetrievedChunk]


@dataclass
class UsageMetrics:
    embedding_calls: int = 0
    chat_calls: int = 0
    chunks_indexed: int = 0
    docs_indexed: int = 0
    retrieval_requests: int = 0
    failed_docs: int = 0
    stage_latency_ms: dict[str, float] = field(default_factory=dict)


@dataclass
class RagRunResult:
    run_id: str
    dataset_root: str
    embedding_model: str
    chat_model: str
    questions: list[QuestionResult]
    metrics: UsageMetrics
    generated_at: str

    def to_dict(self) -> dict:
        return asdict(self)
