"""Backward-compatible chunking API.

Prefer `stock_market_rag.indexing.chunking`.
"""

from __future__ import annotations

from dataclasses import dataclass

from stock_market_rag.indexing.chunking import recursive_character_chunking as _recursive_character_chunking


@dataclass
class Chunk:
    id: str
    text: str
    source: str


def simple_character_chunking(text: str, source: str, chunk_size: int = 1000, overlap: int = 100) -> list[Chunk]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(Chunk(id=f"{source}-{index}", text=chunk_text, source=source))
            index += 1
        if end == len(text):
            break
        start = end - overlap
    return chunks


def recursive_character_chunking(
    text: str,
    source: str,
    chunk_size: int = 1000,
    overlap: int = 120,
    separators: list[str] | None = None,
) -> list[Chunk]:
    new_chunks = _recursive_character_chunking(
        text=text,
        source=source,
        chunk_size=chunk_size,
        overlap=overlap,
        separators=separators,
    )
    return [Chunk(id=c.id, text=c.text, source=c.source) for c in new_chunks]
