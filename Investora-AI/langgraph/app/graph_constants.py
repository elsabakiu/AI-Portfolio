from __future__ import annotations

from pathlib import Path

DEFAULT_UNIVERSE = [
    "AAPL",
    "AMZN",
    "GOOGL",
    "JPM",
    "MA",
    "META",
    "MSFT",
    "NVDA",
    "TSLA",
    "V",
]

UNIVERSE_PATH = Path(__file__).parent.parent / "data" / "universe_mock.json"
REPORT_DIR = Path(__file__).resolve().parent.parent / "data" / "reports"
