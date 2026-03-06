from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app import api as api_module
from app import event_store

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_json(name: str) -> Any:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


class _FakeGraph:
    def stream(self, initial: Dict[str, Any], config: Dict[str, Any]):
        nodes: List[str] = _load_json("stream_nodes_fixture.json")
        for node in nodes:
            yield {node: {"ok": True}}


def test_run_analysis_stream_contract(monkeypatch):
    monkeypatch.setattr(api_module.run_limiter, "acquire", lambda timeout_s=90.0: "acquired")
    monkeypatch.setattr(api_module.run_limiter, "release", lambda: None)

    import app.graph as graph_module

    monkeypatch.setattr(graph_module, "build_graph", lambda force_rebuild=False: _FakeGraph())

    client = TestClient(api_module.app)
    response = client.post(
        "/run-analysis-stream",
        json={"tickers": ["AAPL"], "skip_synthesis": True, "no_post": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    lines = [line for line in response.text.splitlines() if line.startswith("data: ")]
    assert any('"type": "node_complete"' in line for line in lines)
    assert any('"type": "done"' in line for line in lines)


def test_dashboard_contract(monkeypatch, tmp_path):
    db_path = tmp_path / "investora_test.db"
    monkeypatch.setattr(event_store, "DB_PATH", db_path)
    event_store.init_db()

    expected_bundle = _load_json("bundle_fixture.json")
    event_store.save_bundle(expected_bundle)

    client = TestClient(api_module.app)
    response = client.get(f"/user/{expected_bundle['user_id']}/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == expected_bundle["user_id"]
    assert payload["run_id"] == expected_bundle["run_id"]
    assert isinstance(payload["watchlist_signals"], list)
    assert isinstance(payload["discovery_signals"], list)


def test_personalized_signals_contract(monkeypatch, tmp_path):
    db_path = tmp_path / "investora_test.db"
    monkeypatch.setattr(event_store, "DB_PATH", db_path)
    event_store.init_db()

    bundle = _load_json("bundle_fixture.json")
    event_store.save_bundle(bundle)

    client = TestClient(api_module.app)
    response = client.get(f"/user/{bundle['user_id']}/personalized-signals")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"watchlist_signals", "discovery_signals"}
    assert payload["watchlist_signals"] == bundle["watchlist_signals"]
    assert payload["discovery_signals"] == bundle["discovery_signals"]
