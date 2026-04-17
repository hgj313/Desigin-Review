"""PRD completeness validation node.

Validates completeness per PRD-03: no placeholder content, no empty sections.
"""

import re
from typing import List

from src.workflow.state import PRDReviewState, Finding


# Placeholder patterns per PRD-03
PLACEHOLDER_PATTERNS = [
    (r'\bTBD\b', "TBD placeholder"),
    (r'\bTODO\b', "TODO placeholder"),
    (r'\bFIXME\b', "FIXME placeholder"),
    (r'\bXXX\b', "XXX placeholder"),
    (r'\[\s*\]', "Unresolved checkbox"),
    (r'\.\.\.\s*$', "Ellipsis at end of list"),
    (r'%\([^)]*\)s', "Unresolved printf variable"),
    (r'\{\{[^}]+\}\}', "Unresolved mustache variable"),
    (r'\{[^}]+\}', "Unresolved template variable"),
    (r'\bas needed\b', "Vague language: 'as needed'"),
    (r'\bas appropriate\b', "Vague language: 'as appropriate'"),
    (r'\betc\.?\b', "Vague language: 'etc.'"),
]


def _find_placeholder_locations(prd_text: str) -> List[tuple[str, str, int]]:
    """Find all placeholder locations with line numbers."""
    locations = []
    lines = prd_text.split('\n')

    for i, line in enumerate(lines, 1):
        for pattern, name in PLACEHOLDER_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                match = re.search(pattern, line, re.IGNORECASE)
                locations.append((name, f"Line {i}: {line.strip()[:50]}", match.group()))
                break

    return locations


def _check_empty_sections(prd_text: str, review_depth: str) -> List[Finding]:
    """Check for empty or near-empty sections."""
    findings = []

    if review_depth != "thorough":
        return findings

    # Split by headings
    sections = re.split(r'^(#{1,6})\s+(.+)$', prd_text, flags=re.MULTILINE)

    # sections is [text, hash, heading, text, hash, heading, ...]
    for i in range(1, len(sections), 3):
        if i + 1 >= len(sections):
            break

        heading = sections[i + 1].strip() if i + 1 < len(sections) else ""
        content_start = i + 2
        if content_start < len(sections):
            content = sections[content_start].strip() if content_start < len(sections) else ""

            # Check if section has less than 10 words
            if len(content.split()) < 10 and len(content) > 0:
                findings.append(Finding(
                    issue_type="completeness",
                    severity="Minor",
                    location=f"Section: {heading}",
                    description_en=f"Section '{heading}' appears incomplete (less than 10 words)",
                    description_zh=f"章节'{heading}'似乎不完整（少于10个词）",
                    suggestion_en="Expand this section with more detail",
                    suggestion_zh="请扩展此章节的详细内容",
                ))

    return findings


def validate_completeness_node(state: PRDReviewState) -> PRDReviewState:
    """Validate PRD completeness for placeholder content and empty sections.

    Args:
        state: PRDReviewState with prd_text and review_depth.

    Returns:
        Updated state with completeness_findings list populated.
    """
    prd_text = state["prd_text"]
    review_depth = state["review_depth"]
    findings: List[Finding] = []

    # Check for placeholder patterns
    placeholder_locations = _find_placeholder_locations(prd_text)
    for name, location, matched_text in placeholder_locations:
        findings.append(Finding(
            issue_type="completeness",
            severity="Major",
            location=location,
            description_en=f"Placeholder content found: {matched_text}",
            description_zh=f"发现占位符内容：{matched_text}",
            suggestion_en="Replace with actual content before review",
            suggestion_zh="在审查前替换为实际内容",
        ))

    # Check for empty/near-empty sections (thorough mode only)
    findings.extend(_check_empty_sections(prd_text, review_depth))

    return {
        "completeness_findings": findings,
    }


__all__ = ["validate_completeness_node"]
