from __future__ import annotations

from app.mcp_tools.fundamentals_tool import FundamentalsTool
from app.mcp_tools.news_tool import NewsTool


class _FundamentalsToolStub(FundamentalsTool):
    def __init__(self):
        self.base_url = "https://example.com"
        self.api_key = "key"
        self._cache = {}

    def _read_cache(self, namespace, payload):
        return None

    def _write_cache(self, namespace, payload, data):
        self._cache[(namespace, str(payload))] = data

    def _get_with_retry(self, url, params):
        if "key-metrics-ttm" in url:
            return [{"roe": 0.2, "operatingProfitMarginTTM": 0.3}]
        return [{"debtEquityRatioTTM": 1.1, "revenueGrowth": 0.1, "epsGrowth": 0.2}]


class _NewsToolStub(NewsTool):
    def __init__(self):
        self.base_url = "https://example.com"
        self.api_key = "key"
        self._cache = {}

    def _read_cache(self, namespace, payload):
        return None

    def _write_cache(self, namespace, payload, data):
        self._cache[(namespace, str(payload))] = data

    def _get_with_retry(self, url, params):
        return [{"headline": "h1", "summary": "s", "source": "x", "datetime": 1, "url": "u"}]


def test_fundamentals_tool_normalizes_metrics():
    tool = _FundamentalsToolStub()
    out = tool.run({"ticker": "aapl"})

    assert out["ticker"] == "AAPL"
    assert out["metrics"]["roe"] == 0.2
    assert out["metrics"]["debt_to_equity"] == 1.1


def test_news_tool_normalizes_articles():
    tool = _NewsToolStub()
    out = tool.run({"ticker": "msft", "end_date": "2026-03-07"})

    assert out["ticker"] == "MSFT"
    assert isinstance(out["articles"], list)
    assert out["articles"][0]["headline"] == "h1"
