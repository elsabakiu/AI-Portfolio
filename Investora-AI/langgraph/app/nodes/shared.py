from __future__ import annotations

from ..settings import get_settings
from ..state import GraphState


def should_skip_post(state: GraphState) -> bool:
    """Return whether outbound posting should be skipped for this run."""
    if "skip_post" in state:
        return bool(state.get("skip_post"))
    return get_settings().run.skip_n8n_post
