from __future__ import annotations

from fastapi.testclient import TestClient

from app import api as api_module


class _FakeYF:
    def get_quotes(self, tickers):
        return {tickers[0]: {"price": 100.5, "change_pct": 1.2}}


class _FakeNews:
    def run(self, payload):
        return {"articles": [{"headline": "Headline A"}, {"headline": "Headline B"}]}


class _FakeChatCompletions:
    def create(self, **kwargs):
        class _Msg:
            content = "Short factual summary."

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()


class _FakeClient:
    def __init__(self, *args, **kwargs):
        self.chat = type("Chat", (), {"completions": _FakeChatCompletions()})


def test_debug_metrics_contract():
    client = TestClient(api_module.app)
    response = client.get("/debug/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"node_timings", "provider_counters"}
    assert isinstance(payload["node_timings"], dict)
    assert isinstance(payload["provider_counters"], dict)


def test_ai_view_contract(monkeypatch):
    monkeypatch.setattr(api_module.settings.providers, "openai_api_key", "test-key")

    import app.mcp_tools.yfinance_tool as yf_module
    import app.mcp_tools.news_tool as news_module
    import openai as openai_module

    monkeypatch.setattr(yf_module, "YFinanceTool", _FakeYF)
    monkeypatch.setattr(news_module, "NewsTool", _FakeNews)
    monkeypatch.setattr(openai_module, "OpenAI", _FakeClient)

    client = TestClient(api_module.app)
    response = client.get("/market/ai-view/AAPL")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"summary", "generated_at"}
    assert isinstance(payload["summary"], str)
    assert isinstance(payload["generated_at"], str)
