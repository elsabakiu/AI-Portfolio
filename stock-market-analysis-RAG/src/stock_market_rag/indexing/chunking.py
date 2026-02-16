"""Chunking strategies."""

from __future__ import annotations

from stock_market_rag.pipeline.models import Chunk

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def recursive_character_chunking(
    text: str,
    source: str,
    chunk_size: int = 1000,
    overlap: int = 120,
    separators: list[str] | None = None,
) -> list[Chunk]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    parts = _recursive_split(text, chunk_size=chunk_size, separators=separators or DEFAULT_SEPARATORS)
    parts = _apply_overlap(parts, overlap=overlap)
    return [
        Chunk(id=f"{source}-{idx}", text=part.strip(), source=source)
        for idx, part in enumerate(parts)
        if part.strip()
    ]


def _recursive_split(text: str, *, chunk_size: int, separators: list[str]) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    sep = separators[0]
    if not sep:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    pieces = text.split(sep)
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = (current + sep + piece).strip() if current else piece.strip()
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.extend(_recursive_split(current, chunk_size=chunk_size, separators=separators[1:]))
        current = piece.strip()
        if len(current) > chunk_size:
            chunks.extend(_recursive_split(current, chunk_size=chunk_size, separators=separators[1:]))
            current = ""
    if current:
        chunks.extend(_recursive_split(current, chunk_size=chunk_size, separators=separators[1:]))
    return chunks


def _apply_overlap(parts: list[str], *, overlap: int) -> list[str]:
    if overlap <= 0 or len(parts) <= 1:
        return parts

    out: list[str] = []
    for idx, part in enumerate(parts):
        if idx == 0:
            out.append(part)
            continue
        prefix = parts[idx - 1][-overlap:]
        out.append(f"{prefix}{part}")
    return out
