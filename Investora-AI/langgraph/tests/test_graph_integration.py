from __future__ import annotations

from app.graph import build_graph


def test_graph_mock_fast_path_integration(monkeypatch):
    monkeypatch.setenv("USE_MOCK_DATA", "true")

    app = build_graph(force_rebuild=True)
    result = app.invoke(
        {
            "tickers": ["AAPL", "MSFT", "NVDA"],
            "skip_synthesis": True,
            "skip_post": True,
            "scope": "fast",
            "trigger_weekly_digest": False,
        },
        config={"recursion_limit": 120},
    )

    assert result.get("run_id")
    assert result.get("scores")
    assert "node_timings" in result
    assert isinstance(result.get("errors", []), list)
