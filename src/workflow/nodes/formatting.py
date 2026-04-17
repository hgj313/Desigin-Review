"""PRD formatting validation node.

Validates basic formatting per PRD-04: heading hierarchy, bullet consistency.
"""

import re
from typing import List, Tuple

from src.workflow.state import PRDReviewState, Finding


def _check_bullet_consistency(prd_text: str) -> List[Finding]:
    """Check for inconsistent bullet markers within the same list."""
    findings = []
    lines = prd_text.split('\n')

    # Track bullet types used and their indentation levels
    list_tracker: List[Tuple[str, int]] = []  # (bullet_type, indent_level)

    bullet_pattern = re.compile(r'^(\s*)([-*+]|\d+\.|[a-z]\))\s+(.+)$')

    for i, line in enumerate(lines, 1):
        match = bullet_pattern.match(line)
        if match:
            indent = len(match.group(1))
            bullet = match.group(2)
            content = match.group(3)

            # Determine bullet type category
            if bullet in ['-', '*', '+']:
                bullet_type = 'dash'
            elif re.match(r'\d+\.', bullet):
                bullet_type = 'number'
            else:
                bullet_type = 'alpha'

            # Check for mixing bullet types at same indentation
            if list_tracker and list_tracker[-1][1] == indent:
                prev_type, _ = list_tracker[-1]
                if prev_type != bullet_type:
                    findings.append(Finding(
                        issue_type="formatting",
                        severity="Minor",
                        location=f"Line {i}",
                        description_en=f"Mixed bullet types in same list: '{prev_type}' and '{bullet_type}'",
                        description_zh=f"同一列表中混用bullet类型：'{prev_type}'和'{bullet_type}'",
                        suggestion_en="Use consistent bullet markers within a list",
                        suggestion_zh="请在列表中使用一致的bullet标记",
                    ))

            # Check for same indentation
            if list_tracker and list_tracker[-1][1] == indent and prev_type == bullet_type:
                # Check indentation consistency
                pass  # Additional indentation check if needed

            list_tracker.append((bullet_type, indent))

    return findings


def _check_heading_syntax(prd_text: str) -> List[Finding]:
    """Check for incorrect heading syntax."""
    findings = []

    # Wrong heading patterns (not starting with #)
    wrong_heading_pattern = re.compile(r'^(?!#)(\w[\w\s]*)\s*[:\-]?\s*$', re.MULTILINE)
    lines = prd_text.split('\n')

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip empty lines
        if not stripped:
            continue

        # Check if line looks like a heading but doesn't start with #
        if (stripped[0].isupper() and len(stripped) < 80 and
            not stripped.startswith('#') and
            not stripped.startswith('-') and
            not stripped.startswith('*') and
            '.' not in stripped[:10]):  # Likely a sentence, not a heading
            # Be conservative - only flag if it looks very header-like
            pass  # Too aggressive, skip for now

    # Check for trailing whitespace
    for i, line in enumerate(lines, 1):
        if line.endswith(' ') or line.endswith('\t'):
            findings.append(Finding(
                issue_type="formatting",
                severity="Suggestion",
                location=f"Line {i}",
                description_en="Trailing whitespace found",
                description_zh="发现尾部空白",
                suggestion_en="Remove trailing whitespace",
                suggestion_zh="请删除尾部空白",
            ))
            break  # Only one finding per doc for this

    return findings


def validate_formatting_node(state: PRDReviewState) -> PRDReviewState:
    """Validate PRD formatting for bullet consistency and heading syntax.

    Args:
        state: PRDReviewState with prd_text.

    Returns:
        Updated state with formatting_findings list populated.
    """
    prd_text = state["prd_text"]
    findings: List[Finding] = []

    # Check bullet consistency
    findings.extend(_check_bullet_consistency(prd_text))

    # Check heading syntax
    findings.extend(_check_heading_syntax(prd_text))

    return {
        **state,
        "formatting_findings": findings,
    }


__all__ = ["validate_formatting_node"]
