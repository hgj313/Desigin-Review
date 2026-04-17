"""Vague language detection node.

Detects vague language patterns in PRD documents that indicate
unstated assumptions requiring clarification.

References:
- PRD-05: Detect unstated assumptions (vague language like "as needed", "etc.")
"""

import re
from typing import List, Tuple

from src.workflow.state import ImageReviewState, Finding


# Vague language patterns per 03-RESEARCH.md Pattern 7
VAGUE_LANGUAGE_PATTERNS: List[Tuple[str, str]] = [
    (r'\bas needed\b', "Vague: 'as needed' - what triggers the need?"),
    (r'\bas appropriate\b', "Vague: 'as appropriate' - what determines appropriateness?"),
    (r'\betc\.?\b', "Vague: 'etc.' - what specifically is included?"),
    (r'\band so on\b', "Vague: 'and so on' - enumerate specific items"),
    (r'\bsuch as\b', "Vague: 'such as' - provide complete list or use 'including'"),
    (r'\bto be determined\b', "Unstated: 'TBD' - specify actual value"),
    (r'\bpending\b', "Unstated: 'pending' - specify deadline or trigger"),
    (r'\bmaybe\b', "Vague: 'maybe' - state actual condition"),
    (r'\bsometime\b', "Vague: 'sometime' - specify actual timeline"),
    (r'\bmight\b', "Vague: 'might' - state actual probability or trigger"),
    (r'\bpossibly\b', "Vague: 'possibly' - state actual likelihood"),
    (r'\bif possible\b', "Vague: 'if possible' - specify actual requirement"),
    (r'\bwhen necessary\b', "Vague: 'when necessary' - define specific criteria"),
    (r'\bas required\b', "Vague: 'as required' - specify by whom and what"),
]


def detect_prd_assumptions_node(state: ImageReviewState) -> ImageReviewState:
    """Detect vague language indicating unstated assumptions per PRD-05.

    PRD-05: System detects unstated assumptions in requirements (vague language)

    Args:
        state: ImageReviewState with prd_text.

    Returns:
        Updated state with assumption_findings list.

    Severity calibration per D-14:
    - TBD/pending markers -> Critical (undefined deliverable)
    - etc./and so on -> Major (incomplete scope)
    - as needed/maybe -> Minor (needs clarification)
    - Style preferences -> Suggestion
    """
    prd_text = state.get("prd_text", "")
    findings: List[Finding] = []

    for pattern, description in VAGUE_LANGUAGE_PATTERNS:
        matches = list(re.finditer(pattern, prd_text, re.IGNORECASE))

        for match in matches:
            # Get line number
            line_num = prd_text[:match.start()].count('\n') + 1

            # Determine severity based on pattern type
            severity = _get_severity_for_pattern(pattern, description)

            findings.append(Finding(
                issue_type="assumptions",
                severity=severity,
                location=f"Line {line_num}",
                description_en=f"Unstated assumption detected: {description}",
                description_zh=f"检测到未说明的假设：{description}",
                suggestion_en="Provide specific criteria, enumerate all items, or replace with concrete requirements",
                suggestion_zh="请提供具体标准、列举所有项目，或用具体需求替换",
            ))

    # If no vague language found
    if not findings:
        findings.append(Finding(
            issue_type="assumptions",
            severity="Suggestion",
            location="PRD document",
            description_en="No vague language patterns detected - requirements appear specific",
            description_zh="未检测到模糊语言模式 - 需求似乎很具体",
            suggestion_en=None,
            suggestion_zh=None,
        ))

    return {"assumption_findings": findings}


def _get_severity_for_pattern(pattern: str, description: str) -> str:
    """Determine severity based on vague language pattern.

    Args:
        pattern: Regex pattern matched.
        description: Human-readable description.

    Returns:
        Severity level string.
    """
    # Critical patterns - undefined deliverables
    critical_patterns = ["TBD", "pending", "to be determined"]
    for cp in critical_patterns:
        if cp.lower() in description.lower():
            return "Critical"

    # Major patterns - incomplete scope
    major_patterns = ["etc", "and so on", "such as"]
    for mp in major_patterns:
        if mp.lower() in description.lower():
            return "Major"

    # Minor patterns - needs clarification
    minor_patterns = ["as needed", "maybe", "sometime", "might", "possibly", "if possible", "when necessary", "as required"]
    for mp in minor_patterns:
        if mp.lower() in description.lower():
            return "Minor"

    return "Suggestion"


__all__ = ["detect_prd_assumptions_node", "VAGUE_LANGUAGE_PATTERNS"]
