"""File readers for supported document types."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from stock_market_rag.pipeline.errors import UpstreamDataError


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise UpstreamDataError(f"Failed to decode text file: {path}") from error


def read_pdf_text(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as error:  # noqa: BLE001
        raise UpstreamDataError(f"Failed to read PDF file: {path}") from error


def load_document(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return read_pdf_text(path)
    return read_text_file(path)


def discover_documents(dataset_root: Path) -> list[Path]:
    allowed = {".pdf", ".txt", ".htm", ".html", ".md", ".csv"}
    return sorted(path for path in dataset_root.rglob("*") if path.is_file() and path.suffix.lower() in allowed)
