import sys
from pathlib import Path
from typing import Any, Dict, Tuple

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from personal_branding.services.llm_client import generate_completion
from personal_branding.pipeline.generate_post import doc_processor


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_prompt_file(filename: str) -> str:
    prompt_path = _project_root() / "prompts" / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def refine_post(
    draft_post: str,
    topic: str,
    post_type: str,
    business_objective: str,
    config: Dict[str, Any],
    brand_feedback_summary: str = "",
    brand_score: int = -1,
) -> Tuple[str, Dict[str, Any]]:
    if not (draft_post or "").strip():
        return "", {"error": "Draft post is empty."}

    rag_query = f"{topic}. Draft refinement for post type {post_type}. Objective: {business_objective}."
    brand_context = doc_processor.search(rag_query)

    system_prompt_template = _load_prompt_file("system_prompt.txt")
    system_prompt = (
        system_prompt_template.replace("{brand_context}", brand_context)
        .replace("{market_context}", "N/A")
    )
    refinement_template = _load_prompt_file("refinement_prompt.txt")
    # Use explicit token replacement so templates can include JSON braces safely.
    refinement_prompt = (
        refinement_template.replace("{draft}", draft_post)
        .replace("{topic}", topic)
        .replace("{post_type}", post_type)
        .replace("{business_objective}", business_objective)
        .replace("{brand_context}", brand_context)
        .replace("{market_context}", "N/A")
    )
    if (brand_feedback_summary or "").strip():
        refinement_prompt += (
            "\n\nAdditional brand checker feedback to incorporate:\n"
            f"- Current brand score: {brand_score if brand_score >= 0 else 'unknown'} / 100\n"
            f"- Feedback summary: {brand_feedback_summary.strip()}\n"
            "- Prioritize these fixes while preserving the strongest parts of the draft."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": refinement_prompt},
    ]
    llm_result = generate_completion(messages=messages, config=config)
    refined_post = (llm_result.get("content") or "").strip()

    metadata = {
        "prompt_files": {
            "system": "prompts/system_prompt.txt",
            "template": "prompts/refinement_prompt.txt",
        },
        "feedback_driven": bool((brand_feedback_summary or "").strip()),
        "llm": {
            "model": llm_result.get("model"),
            "attempts": llm_result.get("attempts"),
            "usage": llm_result.get("usage", {}),
            "length": llm_result.get("length", {}),
            "estimated_cost_usd": llm_result.get("estimated_cost_usd", 0.0),
            "error": llm_result.get("error"),
        },
    }

    return refined_post, metadata
