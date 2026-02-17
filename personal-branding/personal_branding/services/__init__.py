"""External service integrations."""

from .llm_client import generate_completion
from .cohere_evaluator import evaluate_candidates_with_cohere

__all__ = ["generate_completion", "evaluate_candidates_with_cohere"]
