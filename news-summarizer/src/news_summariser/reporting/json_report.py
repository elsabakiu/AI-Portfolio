"""JSON report serialization."""

from __future__ import annotations

import json
from pathlib import Path

from news_summariser.pipeline.models import RunResult


def to_json_dict(result: RunResult) -> dict:
    return result.to_dict()


def write_json_report(result: RunResult, out_file: str | None = None) -> str:
    payload = to_json_dict(result)
    text = json.dumps(payload, indent=2, ensure_ascii=True)
    if out_file:
        path = Path(out_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    return text
