"""PRD structure validation node.

Validates PRD structure per PRD-01: Overview, User Stories, Acceptance Criteria presence.
"""

import re
from typing import List

from src.workflow.state import PRDReviewState, Finding


# Required sections per PRD-01
REQUIRED_SECTIONS = [
    ("overview", ["Overview", "概述"]),
    ("user_stories", ["User Stories", "用户故事", "用户案例"]),
    ("acceptance_criteria", ["Acceptance Criteria", "验收标准", "验收准则"]),
]

# Heading level jump pattern (H1 -> H3 or more is a violation)
HEADING_JUMP_PATTERN = re.compile(r'^(#{1,4})\s+(.+)$', re.MULTILINE)


def _find_heading_level(heading: str) -> int:
    """Get heading level from number of # symbols."""
    return len(heading) - len(heading.lstrip('#'))


def _check_heading_hierarchy(prd_text: str) -> List[Finding]:
    """Check for heading level jumps."""
    findings = []
    headings = HEADING_JUMP_PATTERN.findall(prd_text)

    prev_level = 0
    for hashmarks, text in headings:
        level = len(hashmarks)
        # Heading level should increase by at most 1 per level
        if prev_level > 0 and level > prev_level + 1:
            findings.append(Finding(
                issue_type="structure",
                severity="Major",
                location=f"Heading: {text.strip()}",
                description_en=f"Heading level jumps more than one level (H{prev_level} to H{level})",
                description_zh=f"标题级别跳跃超过一级（H{prev_level}至H{level}）",
                suggestion_en="Use consistent heading hierarchy (H1 -> H2 -> H3)",
                suggestion_zh="使用一致的标题层级（H1 → H2 → H3）",
            ))
        prev_level = level

    return findings


def validate_structure_node(state: PRDReviewState) -> PRDReviewState:
    """Validate PRD structure for required sections and heading hierarchy.

    Args:
        state: PRDReviewState with prd_text.

    Returns:
        Updated state with structure_findings list populated.
    """
    prd_text = state["prd_text"]
    findings: List[Finding] = []

    # Check for required sections
    for section_key, section_names in REQUIRED_SECTIONS:
        section_found = False
        for name in section_names:
            # Case-insensitive search
            if re.search(rf'#+\s*{re.escape(name)}', prd_text, re.IGNORECASE):
                section_found = True
                break

        if not section_found:
            findings.append(Finding(
                issue_type="structure",
                severity="Critical",
                location="document",
                description_en=f"Missing required section: {section_names[0]}",
                description_zh=f"缺少必需章节：{section_names[0]}",
                suggestion_en=f"Add a {section_names[0]} section to the PRD",
                suggestion_zh=f"在PRD中添加{section_names[0]}章节",
            ))

    # Check heading hierarchy
    findings.extend(_check_heading_hierarchy(prd_text))

    return {
        **state,
        "structure_findings": findings,
    }


__all__ = ["validate_structure_node"]
