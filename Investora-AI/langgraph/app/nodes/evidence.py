from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ..mcp_tools import get_rag_tool
from ..reporting import DEFAULT_COMPANIES
from ..scoring import momentum_weekly_return
from ..settings import get_settings
from ..state import GraphState

logger = logging.getLogger(__name__)
settings = get_settings()


def _parse_synthesis_json(content: str) -> Dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            content = "\n".join(lines[1:-1]).strip()
            if content.lower().startswith("json"):
                content = content[4:].strip()
    return json.loads(content)


def _build_evidence_bundle(
    ticker: str,
    per_ticker_data: Dict[str, Dict[str, Any]],
    scores: Dict[str, Dict[str, float]],
    rag_context: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    data = per_ticker_data.get(ticker, {})
    prices = data.get("market", {}).get("prices", [])
    metrics = data.get("fundamentals", {}).get("metrics", {})
    articles = data.get("news", {}).get("articles", [])

    weekly_return = momentum_weekly_return(prices)
    price_end = float(prices[0]["close"]) if prices and prices[0].get("close") is not None else None
    price_start = float(prices[4]["close"]) if len(prices) >= 5 and prices[4].get("close") is not None else None

    def _pct(key: str) -> Optional[float]:
        try:
            v = float(metrics.get(key))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        return round(v * 100.0 if -2.0 < v < 2.0 else v, 1)

    return {
        "ticker": ticker,
        "company_name": DEFAULT_COMPANIES.get(ticker, {}).get("name", ticker),
        "market": {
            "weekly_return_pct": round(weekly_return, 2) if weekly_return is not None else None,
            "price_start": round(price_start, 2) if price_start is not None else None,
            "price_end": round(price_end, 2) if price_end is not None else None,
        },
        "fundamentals": {
            "roe_pct": _pct("roe"),
            "operating_margin_pct": _pct("operating_margin"),
            "debt_to_equity": metrics.get("debt_to_equity"),
            "revenue_growth_pct": _pct("revenue_growth"),
            "eps_growth_pct": _pct("eps_growth"),
        },
        "headlines": [a.get("headline", "") for a in articles[:5] if a.get("headline")],
        "rag_context": rag_context or [],
        "scores": scores.get(ticker, {}),
    }


def _evidence_target_tickers(state: GraphState) -> List[str]:
    scored = list(state.get("scores", {}).items())
    if not scored:
        return []

    top_n = settings.pipeline.evidence_top_n
    ranked = sorted(scored, key=lambda kv: float(kv[1].get("overall", 0.0)), reverse=True)

    selected: List[str]
    if top_n <= 0:
        selected = [t for t, _ in ranked]
    else:
        selected = [t for t, _ in ranked[:top_n]]

    scored_set = {t for t, _ in ranked}
    selected_set = set(selected)
    for profile in state.get("user_profiles", []):
        for t in profile.get("watchlist", []):
            tt = str(t).upper()
            if tt in scored_set and tt not in selected_set:
                selected.append(tt)
                selected_set.add(tt)

    return selected


def retrieve_rag_context_node(state: GraphState) -> GraphState:
    if state.get("skip_synthesis"):
        state["per_ticker_rag_context"] = {}
        state["rag_stats"] = {"retrieved_items": 0, "queries_run": 0}
        return state

    tool = get_rag_tool()
    context_map: Dict[str, List[Dict[str, Any]]] = {}
    retrieved_items = 0
    queries_run = 0

    lookback_days = settings.pipeline.rag_lookback_days
    top_k = settings.pipeline.rag_top_k
    parallelism = settings.concurrency.rag_parallelism

    target_tickers = _evidence_target_tickers(state)
    if not target_tickers:
        state["per_ticker_rag_context"] = {}
        state["rag_stats"] = {"retrieved_items": 0, "queries_run": 0}
        return state

    max_workers = max(1, min(parallelism, len(target_tickers)))

    def _fetch_one(ticker: str) -> tuple[str, List[Dict[str, Any]], Optional[str]]:
        query = (
            f"{ticker} catalysts, trend confirmation, risk factors and "
            "fundamental context for this week's investment analysis"
        )
        try:
            rag = tool.run(
                {
                    "ticker": ticker,
                    "query": query,
                    "lookback_days": lookback_days,
                    "top_k": top_k,
                    "end_date": state["run_date"],
                }
            )
            matches = list(rag.get("matches") or [])
            return ticker, matches, None
        except Exception as exc:  # noqa: BLE001
            return ticker, [], str(exc)

    futures: Dict[Any, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for ticker in target_tickers:
            queries_run += 1
            futures[pool.submit(_fetch_one, ticker)] = ticker

        for future in as_completed(futures):
            ticker = futures[future]
            try:
                t, matches, err = future.result()
            except Exception as exc:  # noqa: BLE001
                context_map[ticker] = []
                state["errors"].append({"ticker": ticker, "tool": "rag_retrieval", "error": str(exc)})
                continue

            context_map[t] = matches
            retrieved_items += len(matches)
            if err:
                state["errors"].append({"ticker": t, "tool": "rag_retrieval", "error": err})

    state["per_ticker_rag_context"] = context_map
    state["rag_stats"] = {"retrieved_items": retrieved_items, "queries_run": queries_run}
    logger.info(
        "retrieve_rag_context_node",
        extra={"run_id": state["run_id"], "retrieved_items": retrieved_items, "queries_run": queries_run},
    )
    return state


def synthesize_evidence_node(state: GraphState) -> GraphState:
    from ..models import empty_synthesis

    if state.get("skip_synthesis"):
        logger.info("synthesize_evidence_node: skip_synthesis=True; bypassing LLM synthesis.")
        state["per_ticker_synthesis"] = {}
        return state

    api_key = settings.providers.openai_api_key
    if not api_key:
        logger.warning("synthesize_evidence_node: OPENAI_API_KEY not set; skipping synthesis.")
        state["per_ticker_synthesis"] = {}
        return state

    model = settings.providers.synthesis_model
    synthesis: Dict[str, Any] = {}
    parallelism = settings.concurrency.synthesis_parallelism

    target_tickers = _evidence_target_tickers(state)
    if not target_tickers:
        state["per_ticker_synthesis"] = {}
        return state

    system_prompt = (
        "You are a financial analyst producing structured observations for a stock screening system. "
        "Given evidence, return ONLY a JSON object with these exact keys: "
        "quality_narrative (str), momentum_narrative (str), "
        "news_catalyst ({present: bool, headline: str|null, impact: str, strength: str}), "
        "risk_factors (list of str). "
        "Use rag_context when present and prefer evidence-backed statements. "
        "If rag_context is empty or weak, avoid overconfident claims. "
        "Be factual and concise. Never make buy/sell recommendations."
    )

    max_workers = max(1, min(parallelism, len(target_tickers)))

    def _synthesize_one(ticker: str) -> tuple[str, Dict[str, Any], Optional[str]]:
        bundle = _build_evidence_bundle(
            ticker,
            state["per_ticker_data"],
            state["scores"],
            rag_context=state.get("per_ticker_rag_context", {}).get(ticker, []),
        )
        try:
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(bundle)},
                ],
                temperature=0,
            )
            content = getattr(response, "output_text", "") or ""
            payload = _parse_synthesis_json(content)
            catalyst = payload.get("news_catalyst") or {}
            return (
                ticker,
                {
                    "ticker": ticker,
                    "quality_narrative": str(payload.get("quality_narrative", "")),
                    "momentum_narrative": str(payload.get("momentum_narrative", "")),
                    "news_catalyst": {
                        "present": bool(catalyst.get("present", False)),
                        "headline": catalyst.get("headline"),
                        "impact": str(catalyst.get("impact", "neutral")),
                        "strength": str(catalyst.get("strength", "low")),
                    },
                    "risk_factors": list(payload.get("risk_factors") or []),
                },
                None,
            )
        except Exception as exc:  # noqa: BLE001
            return ticker, empty_synthesis(ticker), str(exc)

    futures: Dict[Any, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for ticker in target_tickers:
            futures[pool.submit(_synthesize_one, ticker)] = ticker

        for future in as_completed(futures):
            ticker = futures[future]
            try:
                t, payload, err = future.result()
            except Exception as exc:  # noqa: BLE001
                logger.warning("synthesize_evidence_node: %s failed: %s", ticker, exc)
                state["errors"].append({"ticker": ticker, "tool": "synthesize_evidence", "error": str(exc)})
                synthesis[ticker] = empty_synthesis(ticker)
                continue

            synthesis[t] = payload
            if err:
                logger.warning("synthesize_evidence_node: %s failed: %s", t, err)
                state["errors"].append({"ticker": t, "tool": "synthesize_evidence", "error": err})

    state["per_ticker_synthesis"] = synthesis
    logger.info("synthesize_evidence_node", extra={"run_id": state["run_id"], "count": len(synthesis)})
    return state
