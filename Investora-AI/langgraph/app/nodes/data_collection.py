from __future__ import annotations

import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Literal, Optional, Tuple

from openai import OpenAI

from ..budget_manager import budget_manager
from ..graph_constants import DEFAULT_UNIVERSE, UNIVERSE_PATH
from ..mcp_tools import MCPToolError, get_fundamentals_tool, get_market_tool, get_news_tool
from ..metrics import record_provider_call
from ..logging_utils import install_redaction_filter
from ..profile_store import load_all_profiles
from ..settings import get_settings
from ..state import GraphState, today_iso

logger = logging.getLogger(__name__)
settings = get_settings()


def _load_universe_tickers() -> List[str]:
    use_mock_data = settings.run.use_mock_data
    if use_mock_data and UNIVERSE_PATH.exists():
        try:
            with UNIVERSE_PATH.open() as f:
                data = json.load(f)
            tickers = [t["ticker"] for t in data.get("tickers", [])]
            if tickers:
                logger.debug("_load_universe_tickers: loaded %d tickers", len(tickers))
                return tickers
        except Exception as exc:  # noqa: BLE001
            logger.warning("_load_universe_tickers: failed to load universe_mock.json: %s", exc)

    if use_mock_data and not UNIVERSE_PATH.exists():
        logger.warning("_load_universe_tickers: universe_mock.json missing; using STOCK_UNIVERSE/default")
    return _parse_universe()


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    install_redaction_filter()


def _parse_universe() -> List[str]:
    raw = settings.run.stock_universe
    if raw.strip():
        tickers = [x.strip().upper() for x in raw.split(",") if x.strip()]
    else:
        tickers = DEFAULT_UNIVERSE[:]

    tickers = sorted(set(tickers))
    if len(tickers) > 50:
        tickers = tickers[:50]
    return tickers


def init_state(state: GraphState) -> GraphState:
    _configure_logging()
    run_id = state.get("run_id") or str(uuid.uuid4())
    run_date = state.get("run_date") or settings.run.run_date or today_iso()

    tickers = state.get("tickers") or _load_universe_tickers()

    skip_synthesis = bool(state.get("skip_synthesis", False))
    skip_post = bool(state.get("skip_post", settings.run.skip_n8n_post))
    scope = state.get("scope") or ("fast" if skip_synthesis else "full")
    trigger_weekly_digest = bool(state.get("trigger_weekly_digest", False))

    user_profiles = load_all_profiles()
    all_watchlist_tickers: List[str] = []
    for profile in user_profiles:
        all_watchlist_tickers.extend(profile.get("watchlist", []))

    tickers = budget_manager.prioritize_tickers(tickers, all_watchlist_tickers)
    per_ticker_data = {t: {} for t in tickers}

    return {
        "run_id": run_id,
        "run_date": run_date,
        "tickers": tickers,
        "scope": scope,
        "trigger_weekly_digest": trigger_weekly_digest,
        "skip_synthesis": skip_synthesis,
        "skip_post": skip_post,
        "current_ticker": None,
        "action": None,
        "action_reason": None,
        "done_collection": False,
        "failed_tickers": [],
        "per_ticker_data": per_ticker_data,
        "scores": {},
        "per_ticker_rag_context": {},
        "rag_stats": {"retrieved_items": 0, "queries_run": 0},
        "per_ticker_synthesis": {},
        "signal_events": [],
        "anomaly_signals": [],
        "personalized_bundles": {},
        "triggered_user_alerts": [],
        "report_json": None,
        "report_markdown": "",
        "errors": [],
        "react_history": [],
        "user_profiles": user_profiles,
        "node_timings": {},
    }


def _next_missing_for_ticker(data: Dict[str, Any]) -> Literal["market", "fundamentals", "news", "complete"]:
    if "market" not in data:
        return "market"
    if "fundamentals" not in data:
        return "fundamentals"
    if "news" not in data:
        return "news"
    return "complete"


def _pending_action_candidates(state: GraphState) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    failed = set(state["failed_tickers"])
    for ticker in state["tickers"]:
        if ticker in failed:
            continue
        next_missing = _next_missing_for_ticker(state["per_ticker_data"].get(ticker, {}))
        if next_missing != "complete":
            out.append((ticker, next_missing))
    return out


def _validate_llm_choice(
    state: GraphState,
    ticker: Optional[str],
    action: str,
    reason: str,
    pending: Optional[List[Tuple[str, str]]] = None,
) -> Tuple[Optional[str], str, str]:
    if pending is None:
        pending = _pending_action_candidates(state)
    pending_set = {(t, a) for t, a in pending}
    if action == "compute" and not pending:
        return None, "compute", reason
    if action in {"market", "fundamentals", "news"} and ticker and (ticker, action) in pending_set:
        return ticker, action, reason
    raise ValueError(f"Invalid planner action/ticker: action={action}, ticker={ticker}, pending={pending}")


def _openai_react_plan(state: GraphState) -> Tuple[Optional[str], str, str]:
    pending = _pending_action_candidates(state)
    if not pending:
        return None, "compute", "All required tool data collected; proceed to scoring."

    api_key = settings.providers.openai_api_key
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for ReAct planning.")

    model = settings.providers.openai_model
    client = OpenAI(api_key=api_key)

    universe_snapshot = []
    for ticker in state["tickers"]:
        data = state["per_ticker_data"].get(ticker, {})
        universe_snapshot.append(
            {
                "ticker": ticker,
                "failed": ticker in set(state["failed_tickers"]),
                "market_already_fetched": "market" in data,
                "fundamentals_already_fetched": "fundamentals" in data,
                "news_already_fetched": "news" in data,
            }
        )

    prompt = {
        "goal": "Choose exactly one next data-fetch action for a ReAct stock-analysis agent.",
        "instruction": (
            "pending_pairs lists every (ticker, action) that still needs fetching. "
            "false in universe_status means NOT YET FETCHED — the data needs to be retrieved. "
            "You MUST pick one item from pending_pairs. "
            "compute is only valid when pending_pairs is empty."
        ),
        "pending_pairs": [{"ticker": t, "action": a} for t, a in pending],
        "universe_status": universe_snapshot,
    }

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a data-fetch planner. pending_pairs contains items that still need fetching. "
                    "Pick one item from pending_pairs and return ONLY compact JSON: "
                    "{\"thought\": \"...\", \"action\": \"<market|fundamentals|news>\", \"ticker\": \"<TICKER>\", \"reason\": \"...\"}. "
                    "Never choose action=compute while pending_pairs is non-empty."
                ),
            },
            {"role": "user", "content": json.dumps(prompt)},
        ],
        temperature=0,
    )

    content = getattr(response, "output_text", "") or ""
    if not content.strip():
        raise ValueError("Planner returned empty output_text.")

    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                cleaned = "\n".join(lines[1:-1]).strip()
                if cleaned.lower().startswith("json"):
                    cleaned = cleaned[4:].strip()
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Planner returned non-JSON response: {content[:200]}") from exc

    ticker = payload.get("ticker")
    action = str(payload.get("action", "compute")).strip().lower()
    reason = str(payload.get("reason", "LLM planned next step.")).strip()
    return _validate_llm_choice(state, ticker, action, reason, pending=pending)


def plan_next_action(state: GraphState) -> GraphState:
    pending = _pending_action_candidates(state)

    if settings.run.use_mock_data:
        if pending:
            selected_ticker, selected_action, reason = (
                pending[0][0],
                pending[0][1],
                "Deterministic planner in mock mode: selecting first pending action.",
            )
        else:
            selected_ticker, selected_action, reason = (
                None,
                "compute",
                "All required tool data collected; proceed to scoring.",
            )
    else:
        try:
            selected_ticker, selected_action, reason = _openai_react_plan(state)
        except Exception as exc:  # noqa: BLE001
            state["errors"].append({"ticker": "*", "tool": "planner", "error": str(exc)})
            if pending:
                selected_ticker, selected_action, reason = (
                    pending[0][0],
                    pending[0][1],
                    "Planner failed; falling back to first pending action.",
                )
            else:
                selected_ticker, selected_action, reason = (
                    None,
                    "compute",
                    "Planner failed; proceeding to compute with whatever data is available.",
                )

    logger.info(
        "plan_next_action",
        extra={
            "ticker": selected_ticker,
            "action": selected_action,
            "reason": reason,
            "trace_id": str(uuid.uuid4()),
        },
    )

    state["current_ticker"] = selected_ticker
    state["action"] = selected_action
    state["action_reason"] = reason
    state["done_collection"] = selected_action == "compute"
    state["react_history"].append(
        {
            "phase": "thought_action",
            "ticker": selected_ticker or "",
            "action": selected_action,
            "message": reason,
        }
    )
    return state


def _run_market_tool(state: GraphState, ticker: str) -> None:
    record_provider_call("market")
    tool = get_market_tool()
    result = tool.run({"ticker": ticker})
    state["per_ticker_data"].setdefault(ticker, {})["market"] = result
    state["react_history"].append(
        {"phase": "observation", "ticker": ticker, "action": "market", "message": "Market data fetched."}
    )


def _run_fundamentals_tool(state: GraphState, ticker: str) -> None:
    record_provider_call("fundamentals")
    tool = get_fundamentals_tool()
    result = tool.run({"ticker": ticker})
    state["per_ticker_data"].setdefault(ticker, {})["fundamentals"] = result
    state["react_history"].append(
        {
            "phase": "observation",
            "ticker": ticker,
            "action": "fundamentals",
            "message": "Fundamentals fetched.",
        }
    )


def _run_news_tool(state: GraphState, ticker: str) -> None:
    record_provider_call("news")
    tool = get_news_tool()
    result = tool.run({"ticker": ticker, "end_date": state["run_date"]})
    state["per_ticker_data"].setdefault(ticker, {})["news"] = result
    state["react_history"].append(
        {"phase": "observation", "ticker": ticker, "action": "news", "message": "News data fetched."}
    )


def execute_tool_action(state: GraphState) -> GraphState:
    action = state.get("action")
    if action not in {"market", "fundamentals", "news"}:
        return state

    run_id = state.get("run_id", "unknown")
    failed_set = set(state["failed_tickers"])
    targets = [
        t
        for t in state["tickers"]
        if t not in failed_set and action not in state["per_ticker_data"].get(t, {})
    ]

    if not targets:
        return state

    if action == "market":
        tool = get_market_tool()
        if hasattr(tool, "run_many"):
            if not budget_manager.can_call(action, run_id):
                logger.warning(
                    "budget_manager: run %s exhausted API budget; skipping market batch for %d ticker(s)",
                    run_id,
                    len(targets),
                )
                for ticker in targets:
                    if ticker not in state["failed_tickers"]:
                        state["failed_tickers"].append(ticker)
                state["react_history"].append(
                    {
                        "phase": "observation",
                        "ticker": "",
                        "action": action,
                        "message": f"Skipped: API budget exhausted for market batch ({len(targets)} tickers).",
                    }
                )
                return state

            budget_manager.record_call(action, run_id)
            try:
                batch = tool.run_many(targets)
                for ticker in targets:
                    result = batch.get(ticker)
                    if not isinstance(result, dict):
                        if ticker not in state["failed_tickers"]:
                            state["failed_tickers"].append(ticker)
                        state["errors"].append(
                            {"ticker": ticker, "tool": action, "error": "No market payload returned from batch fetch"}
                        )
                        continue
                    state["per_ticker_data"].setdefault(ticker, {})["market"] = result
                    state["react_history"].append(
                        {
                            "phase": "observation",
                            "ticker": ticker,
                            "action": "market",
                            "message": "Market data fetched (batch).",
                        }
                    )
                return state
            except MCPToolError as exc:
                state["errors"].append({"ticker": "*", "tool": action, "error": str(exc)})
                if "rate limit" in str(exc).lower():
                    for t in state["tickers"]:
                        data = state["per_ticker_data"].get(t, {})
                        if "market" not in data and t not in state["failed_tickers"]:
                            state["failed_tickers"].append(t)
                    return state
                for ticker in targets:
                    if ticker not in state["failed_tickers"]:
                        state["failed_tickers"].append(ticker)
                return state
            except Exception as exc:  # noqa: BLE001
                state["errors"].append({"ticker": "*", "tool": action, "error": str(exc)})
                for ticker in targets:
                    if ticker not in state["failed_tickers"]:
                        state["failed_tickers"].append(ticker)
                return state

    if action in {"fundamentals", "news"}:
        admitted: List[str] = []
        for ticker in targets:
            if not budget_manager.can_call(action, run_id):
                logger.warning(
                    "budget_manager: run %s exhausted API budget; skipping remaining %s calls (%d ticker(s))",
                    run_id,
                    action,
                    len([t for t in targets if t not in admitted]),
                )
                if ticker not in state["failed_tickers"]:
                    state["failed_tickers"].append(ticker)
                state["react_history"].append(
                    {
                        "phase": "observation",
                        "ticker": ticker,
                        "action": action,
                        "message": "Skipped: API budget exhausted for this run.",
                    }
                )
                continue
            budget_manager.record_call(action, run_id)
            admitted.append(ticker)

        if not admitted:
            return state

        tool = get_fundamentals_tool() if action == "fundamentals" else get_news_tool()
        max_workers = max(1, min(settings.concurrency.tool_parallelism, len(admitted)))

        def _fetch_one(ticker: str) -> Dict[str, Any]:
            if action == "fundamentals":
                return tool.run({"ticker": ticker})
            return tool.run({"ticker": ticker, "end_date": state["run_date"]})

        futures: Dict[Any, str] = {}
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for t in admitted:
                futures[pool.submit(_fetch_one, t)] = t

            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    result = future.result()
                    state["per_ticker_data"].setdefault(ticker, {})[action] = result
                    state["react_history"].append(
                        {
                            "phase": "observation",
                            "ticker": ticker,
                            "action": action,
                            "message": f"{action.capitalize()} fetched.",
                        }
                    )
                except MCPToolError as exc:
                    state["errors"].append({"ticker": ticker, "tool": action, "error": str(exc)})
                    if ticker not in state["failed_tickers"]:
                        state["failed_tickers"].append(ticker)
                    state["react_history"].append(
                        {
                            "phase": "observation",
                            "ticker": ticker,
                            "action": action,
                            "message": f"Tool failed: {exc}",
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    state["errors"].append({"ticker": ticker, "tool": action, "error": str(exc)})
                    if ticker not in state["failed_tickers"]:
                        state["failed_tickers"].append(ticker)
                    state["react_history"].append(
                        {
                            "phase": "observation",
                            "ticker": ticker,
                            "action": action,
                            "message": f"Execution failed: {exc}",
                        }
                    )
        return state

    for ticker in targets:
        if not budget_manager.can_call(action, run_id):
            logger.warning(
                "budget_manager: run %s exhausted API budget; skipping remaining %s calls (%d ticker(s))",
                run_id,
                action,
                len([t for t in targets if t not in state["failed_tickers"]]),
            )
            if ticker not in state["failed_tickers"]:
                state["failed_tickers"].append(ticker)
            state["react_history"].append(
                {
                    "phase": "observation",
                    "ticker": ticker,
                    "action": action,
                    "message": "Skipped: API budget exhausted for this run.",
                }
            )
            continue

        budget_manager.record_call(action, run_id)
        try:
            if action == "market":
                _run_market_tool(state, ticker)
            elif action == "fundamentals":
                _run_fundamentals_tool(state, ticker)
            elif action == "news":
                _run_news_tool(state, ticker)
        except MCPToolError as exc:
            state["errors"].append({"ticker": ticker, "tool": action, "error": str(exc)})
            if action == "market" and "rate limit" in str(exc).lower():
                for t in state["tickers"]:
                    data = state["per_ticker_data"].get(t, {})
                    if "market" not in data and t not in state["failed_tickers"]:
                        state["failed_tickers"].append(t)
                break
            if ticker not in state["failed_tickers"]:
                state["failed_tickers"].append(ticker)
            state["react_history"].append(
                {
                    "phase": "observation",
                    "ticker": ticker,
                    "action": action,
                    "message": f"Tool failed: {exc}",
                }
            )
        except Exception as exc:  # noqa: BLE001
            state["errors"].append({"ticker": ticker, "tool": action, "error": str(exc)})
            if ticker not in state["failed_tickers"]:
                state["failed_tickers"].append(ticker)
            state["react_history"].append(
                {
                    "phase": "observation",
                    "ticker": ticker,
                    "action": action,
                    "message": f"Execution failed: {exc}",
                }
            )
    return state
