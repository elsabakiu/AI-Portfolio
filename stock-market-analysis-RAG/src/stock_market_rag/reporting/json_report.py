"""JSON report serializer."""

from __future__ import annotations

import json
from pathlib import Path

from stock_market_rag.pipeline.models import RagRunResult


def to_json_dict(result: RagRunResult) -> dict:
    return result.to_dict()


def write_json_report(result: RagRunResult, out_file: str | None = None) -> str:
    payload = json.dumps(result.to_dict(), indent=2, ensure_ascii=True)
    if out_file:
        path = Path(out_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload + "\n", encoding="utf-8")
    return payload
