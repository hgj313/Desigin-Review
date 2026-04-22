"""Severity calibration module.

Hybrid severity: rule-based floor + LLM escalation (max 1 level) per D-14.
"""

from typing import Optional, Literal
from pydantic import BaseModel


SEVERITY_HIERARCHY = ["Critical", "Major", "Minor", "Suggestion"]

# Rule-based severity floor map per D-14
RULE_SEVERITY_MAP = {
    "missing_section": "Critical",  # Required section absent
    "undefined_term": "Major",       # Terminology issue
    "placeholder_content": "Major",  # TBD, TODO, etc.
    "heading_inconsistency": "Minor",  # Structural violation
    "bullet_inconsistency": "Minor",  # List formatting
    "heading_syntax": "Minor",        # Wrong heading format
    "trailing_whitespace": "Suggestion",  # Style preference
    "structure": "Critical",          # Missing required section
    "terminology": "Major",           # Term usage issue
    "completeness": "Major",          # Placeholder content
    "formatting": "Minor",            # Style issue
}


class SeverityAssessment(BaseModel):
    """LLM severity assessment.

    Attributes:
        suggested_severity: LLM's suggested severity level.
        reasoning_zh: Chinese reasoning for the suggestion.
        should_elevate: Whether LLM believes escalation is warranted.
    """

    suggested_severity: str  # Critical, Major, Minor, Suggestion
    reasoning_zh: str
    should_elevate: bool


def calculate_severity(
    issue_type: str,
    location: str,
    content: str,
    llm_assessment: Optional[SeverityAssessment] = None,
) -> str:
    """Calculate final severity using rule-based floor + optional LLM escalation.

    Per D-14: LLM can escalate by at most ONE level. This prevents all
    issues becoming Critical.

    Args:
        issue_type: Type of issue (structure/terminology/completeness/formatting).
        location: Location of the issue in the document.
        content: Content context for the issue.
        llm_assessment: Optional LLM-based severity assessment.

    Returns:
        Calibrated severity level (Critical, Major, Minor, or Suggestion).
    """
    # 1. Get rule-based floor severity
    base_severity = RULE_SEVERITY_MAP.get(issue_type, "Minor")

    # 2. If no LLM assessment, return rule-based
    if llm_assessment is None:
        return base_severity

    # 3. Apply LLM escalation (max 1 level per D-14)
    try:
        current_idx = SEVERITY_HIERARCHY.index(base_severity)
        suggested_idx = SEVERITY_HIERARCHY.index(llm_assessment.suggested_severity)

        # LLM can only escalate by at most 1 level (lower index = higher severity)
        if suggested_idx < current_idx:  # Higher severity (lower index)
            new_idx = max(0, current_idx - 1)  # Max 1 level up
            return SEVERITY_HIERARCHY[new_idx]
    except ValueError:
        # Invalid severity string from LLM, fall back to rule-based
        pass

    return base_severity


def assess_severity_with_llm(
    issue_type: str,
    description: str,
    context: str,
    api_key: str,
    model: str = "MiniMax/M2.7",
) -> SeverityAssessment:
    """Assess severity using LLM for nuanced judgment.

    Args:
        issue_type: Type of issue.
        description: Description of the finding.
        context: Surrounding context from the document.
        api_key: MiniMax API key.
        model: Model to use for assessment.

    Returns:
        SeverityAssessment with LLM's judgment.
    """
    from src.prompts.templates import format_severity_assessment
    import openai

    # Format the assessment prompt
    format_instructions = """Return JSON with:
{
    "suggested_severity": "Critical|Major|Minor|Suggestion",
    "reasoning_zh": "Chinese explanation",
    "should_elevate": true|false
}"""

    prompt = format_severity_assessment(
        issue_type=issue_type,
        description=description,
        context=context,
        format_instructions=format_instructions,
    )

    # Call MiniMax API (OpenAI-compatible)
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.minimax.chat/v1",
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,  # Lower temperature for more consistent judgments
    )

    import json
    result_text = response.choices[0].message.content

    # Parse JSON response
    try:
        # Try to extract JSON from the response
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        result = json.loads(result_text.strip())

        return SeverityAssessment(
            suggested_severity=result["suggested_severity"],
            reasoning_zh=result["reasoning_zh"],
            should_elevate=result["should_elevate"],
        )
    except (json.JSONDecodeError, KeyError) as e:
        # If parsing fails, return a neutral assessment
        return SeverityAssessment(
            suggested_severity="Minor",
            reasoning_zh=f"无法解析LLM响应：{str(e)}",
            should_elevate=False,
        )


__all__ = [
    "SeverityAssessment",
    "calculate_severity",
    "assess_severity_with_llm",
    "SEVERITY_HIERARCHY",
    "RULE_SEVERITY_MAP",
]
