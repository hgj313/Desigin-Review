"""Review bounded context - LLM prompt templates."""

from src_v2.domain.review.llm_prompts.prompts import (
    CROSS_REFERENCE_VALIDATION_PROMPT,
    SEMANTIC_COMPLETENESS_PROMPT,
    VAGUE_LANGUAGE_DETECTION_PROMPT,
)

__all__ = [
    "VAGUE_LANGUAGE_DETECTION_PROMPT",
    "SEMANTIC_COMPLETENESS_PROMPT",
    "CROSS_REFERENCE_VALIDATION_PROMPT",
]
