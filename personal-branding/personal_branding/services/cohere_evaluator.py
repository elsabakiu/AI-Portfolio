import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

COHERE_CHAT_URL = "https://api.cohere.com/v2/chat"
DEFAULT_COHERE_MODEL = "command-a-03-2025"
COHERE_FALLBACK_MODELS = [
    "command-r7b-12-2024",
    "command-r-plus-08-2024",
    "command-r-08-2024",
]


def _extract_text(response_json: Dict[str, Any]) -> str:
    message = response_json.get("message", {})
    content = message.get("content", [])
    if isinstance(content, list):
        text_chunks = []
        for chunk in content:
            if isinstance(chunk, dict) and chunk.get("type") == "text":
                text_chunks.append(chunk.get("text", ""))
        if text_chunks:
            return "\n".join(text_chunks).strip()

    if isinstance(response_json.get("text"), str):
        return response_json["text"].strip()

    return ""


def _safe_json_loads(text: str) -> Dict[str, Any]:
    if not text:
        return {}

    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return {}


def _build_evaluator_prompt(
    topic: str,
    post_type: str,
    business_objective: str,
    candidates: List[Dict[str, Any]],
    brand_context: str = "",
) -> str:
    candidates_payload = []
    for idx, candidate in enumerate(candidates):
        candidates_payload.append(
            {
                "index": idx,
                "angle": candidate.get("angle"),
                "text": candidate.get("text", ""),
            }
        )

    return (
        "You are evaluating LinkedIn drafts for originality and practical SME relevance.\n\n"
        f"Topic: {topic}\n"
        f"Post type: {post_type}\n"
        f"Business objective: {business_objective}\n\n"
        "Relevant context from knowledge base:\n"
        f"{brand_context or 'No specific context found. Use the candidate content as primary signal.'}\n\n"
        "Score each candidate 0-100 using these weighted criteria:\n"
        "- Novelty of insight (30)\n"
        "- Specificity and operational detail (25)\n"
        "- Practitioner credibility signal (20)\n"
        "- Non-generic language (15)\n"
        "- CTA usefulness (10)\n\n"
        "Return strict JSON only with this schema:\n"
        "{\n"
        '  "best_index": 0,\n'
        '  "reason": "one short paragraph",\n'
        '  "scores": [\n'
        '    {"index": 0, "total": 0, "novelty": 0, "specificity": 0, "credibility": 0, "non_generic": 0, "cta": 0}\n'
        "  ]\n"
        "}\n\n"
        "Candidates JSON:\n"
        f"{json.dumps(candidates_payload, ensure_ascii=True)}"
    )


def evaluate_candidates_with_cohere(
    topic: str,
    post_type: str,
    business_objective: str,
    candidates: List[Dict[str, Any]],
    config: Dict[str, Any],
    brand_context: str = "",
) -> Tuple[int, Dict[str, Any]]:
    if not candidates:
        return 0, {"error": "No candidates to evaluate."}

    cohere_api_key = config.get("cohere_api_key") or os.getenv("COHERE_API_KEY")
    if not cohere_api_key:
        return 0, {"error": "COHERE_API_KEY is not set. Falling back to first draft."}

    model = config.get("cohere_model", DEFAULT_COHERE_MODEL)
    candidate_models = [model] + [m for m in COHERE_FALLBACK_MODELS if m != model]
    prompt = _build_evaluator_prompt(
        topic=topic,
        post_type=post_type,
        business_objective=business_objective,
        candidates=candidates,
        brand_context=brand_context,
    )

    last_error: Optional[Dict[str, Any]] = None

    for selected_model in candidate_models:
        payload = {
            "model": selected_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }

        req = urllib.request.Request(
            COHERE_CHAT_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {cohere_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=float(config.get("cohere_timeout", 40))) as response:
                raw = response.read().decode("utf-8")
                response_json = json.loads(raw)
        except urllib.error.HTTPError as exc:
            last_error = {
                "error": f"Cohere HTTP error: {exc.code}",
                "details": exc.read().decode("utf-8", errors="ignore"),
                "model": selected_model,
            }
            # Retry with a fallback model if current one is unavailable.
            if exc.code == 404:
                continue
            return 0, last_error
        except Exception as exc:
            last_error = {"error": f"Cohere request failed: {exc}", "model": selected_model}
            return 0, last_error

        evaluator_text = _extract_text(response_json)
        parsed = _safe_json_loads(evaluator_text)

        best_index = parsed.get("best_index", 0)
        try:
            best_index = int(best_index)
        except Exception:
            best_index = 0

        if best_index < 0 or best_index >= len(candidates):
            best_index = 0

        metadata = {
            "provider": "cohere",
            "model": selected_model,
            "raw_text": evaluator_text,
            "parsed": parsed,
            "fallback_chain": candidate_models,
        }
        return best_index, metadata

    return 0, {
        "error": "Cohere evaluator failed for all configured models.",
        "last_error": last_error,
        "fallback_chain": candidate_models,
    }
