import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from personal_branding.services.llm_client import generate_completion
from personal_branding.pipeline.generate_post import doc_processor


BRAND_CHECK_SYSTEM_PROMPT = """
You are a strict evaluator for SME-focused LinkedIn content quality.
Score the content objectively and return JSON only.
""".strip()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_prompt_file(filename: str) -> str:
    prompt_path = _project_root() / "prompts" / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def _build_brand_check_prompt(post: str, brand_context: str) -> str:
    template = _load_prompt_file("brand_check_prompt.txt")
    # Use direct token replacement so JSON braces in the template are not interpreted.
    return (
        template.replace("{post}", post)
        .replace("{brand_context}", brand_context)
        .replace("{market_context}", "N/A")
    )


def _safe_int(value: Any, low: int, high: int) -> int:
    try:
        number = int(value)
    except Exception:
        number = 0
    return max(low, min(high, number))


def _extract_json_block(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def check_brand_consistency(post: str, config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not (post or "").strip():
        result = {"score": 0, "feedback_summary": "No post content provided."}
        metadata = {"error": "Empty post input."}
        return result, metadata

    brand_context = doc_processor.search(post)

    messages = [
        {"role": "system", "content": BRAND_CHECK_SYSTEM_PROMPT},
        {"role": "user", "content": _build_brand_check_prompt(post, brand_context=brand_context)},
    ]

    llm_result = generate_completion(messages=messages, config=config)
    parsed = _extract_json_block(llm_result.get("content", ""))

    tone_alignment = _safe_int(parsed.get("tone_alignment"), 0, 20)
    sme_relevance = _safe_int(parsed.get("sme_relevance"), 0, 20)
    presence_of_example = _safe_int(parsed.get("presence_of_example"), 0, 20)
    business_clarity = _safe_int(parsed.get("business_clarity"), 0, 20)
    differentiation = _safe_int(parsed.get("differentiation"), 0, 20)

    computed_score = tone_alignment + sme_relevance + presence_of_example + business_clarity + differentiation
    score = _safe_int(parsed.get("score", computed_score), 0, 100)

    if abs(score - computed_score) > 5:
        score = computed_score

    feedback_summary = (parsed.get("feedback_summary") or "").strip()
    if not feedback_summary:
        feedback_summary = "Model did not return a valid feedback summary."

    result = {
        "tone_alignment": tone_alignment,
        "sme_relevance": sme_relevance,
        "presence_of_example": presence_of_example,
        "business_clarity": business_clarity,
        "differentiation": differentiation,
        "score": score,
        "feedback_summary": feedback_summary,
    }

    metadata = {
        "prompt_files": {
            "system": "in-code:BRAND_CHECK_SYSTEM_PROMPT",
            "template": "prompts/brand_check_prompt.txt",
        },
        "llm": {
            "model": llm_result.get("model"),
            "attempts": llm_result.get("attempts"),
            "usage": llm_result.get("usage", {}),
            "length": llm_result.get("length", {}),
            "estimated_cost_usd": llm_result.get("estimated_cost_usd", 0.0),
            "error": llm_result.get("error"),
        },
    }
    return result, metadata
