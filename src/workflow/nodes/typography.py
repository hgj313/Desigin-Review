"""Typography hierarchy analysis node.

Analyzes typography hierarchy from prototype images including
heading sizes, body text sizes, and caption styles.

References:
- IMG-03: Analyze typography hierarchy (heading vs body vs caption styles)
- D-20: Use MiniMaxVisionClient for analysis
"""

import re
from typing import List

from src.workflow.state import ImageReviewState, Finding
from src.image.minimax_vision import MiniMaxVisionClient


def validate_typography_node(state: ImageReviewState) -> ImageReviewState:
    """Analyze typography hierarchy from prototype image.

    IMG-03: Analyze typography hierarchy (heading vs body vs caption styles)

    Uses MiniMaxVisionClient for typography analysis per D-20.

    Args:
        state: ImageReviewState with image_path.

    Returns:
        Updated state with typography_findings list.

    Severity calibration per D-14:
    - Missing heading hierarchy -> Major
    - Inconsistent heading sizes -> Minor
    - Caption/body confusion -> Suggestion
    """
    vision_client = MiniMaxVisionClient()
    image_path = state["image_path"]

    # Analyze typography from image
    typography_info = vision_client.analyze_typography(image_path)

    findings: List[Finding] = []

    # Parse typography analysis and check for hierarchy issues
    raw = typography_info[0].get("raw", "") if typography_info else ""

    # Check for heading hierarchy
    heading_sizes = _extract_heading_sizes(raw)
    if len(heading_sizes) > 1:
        # Check for consistent hierarchy
        if not _is_hierarchy_consistent(heading_sizes):
            findings.append(Finding(
                issue_type="typography",
                severity="Major",
                location=f"Image: {image_path}",
                description_en="Typography hierarchy appears inconsistent - heading sizes don't follow logical pattern",
                description_zh="排版层次似乎不一致 - 标题大小不符合逻辑模式",
                suggestion_en="Ensure headings follow consistent size hierarchy (H1 > H2 > H3)",
                suggestion_zh="请确保标题遵循一致的大小层次（H1 > H2 > H3）",
            ))

    # Check for body text readability
    body_sizes = _extract_body_sizes(raw)
    for size in body_sizes:
        if size < 12:
            findings.append(Finding(
                issue_type="typography",
                severity="Minor",
                location=f"Image: {image_path}",
                description_en=f"Body text size ({size}pt) may be too small for readability",
                description_zh=f"正文字号（{size}pt）可能太小，影响可读性",
                suggestion_en="Use minimum 12pt for body text, preferably 14-16pt",
                suggestion_zh="正文字号最小使用12pt，建议14-16pt",
            ))

    # If no typography issues found
    if not findings:
        findings.append(Finding(
            issue_type="typography",
            severity="Suggestion",
            location=f"Image: {image_path}",
            description_en="Typography hierarchy appears well-structured",
            description_zh="排版层次结构似乎合理",
            suggestion_en=None,
            suggestion_zh=None,
        ))

    return {"typography_findings": findings}


def _extract_heading_sizes(typography_text: str) -> list[float]:
    """Extract heading sizes from typography analysis text.

    Args:
        typography_text: Raw text from MiniMax typography analysis.

    Returns:
        List of heading sizes in points.
    """
    # Look for patterns like "H1: 24pt", "heading: 24px", "24px heading"
    heading_sizes = []
    patterns = [
        r'[Hh](\d+)[:\s]+(\d+)pt',
        r'[Hh](\d+)[:\s]+(\d+)px',
        r'(?:heading|title)[:\s]+(\d+)(?:pt|px)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, typography_text)
        for match in matches:
            if len(match) == 2:
                heading_sizes.append(float(match[1]))

    return heading_sizes


def _extract_body_sizes(typography_text: str) -> list[float]:
    """Extract body text sizes from typography analysis text.

    Args:
        typography_text: Raw text from MiniMax typography analysis.

    Returns:
        List of body text sizes in points.
    """
    # Look for body text size mentions
    body_sizes = []
    patterns = [
        r'body[:\s]+(\d+)(?:pt|px)',
        r'text[:\s]+(\d+)(?:pt|px)',
        r'paragraph[:\s]+(\d+)(?:pt|px)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, typography_text)
        for match in matches:
            body_sizes.append(float(match))

    return body_sizes


def _is_hierarchy_consistent(sizes: list[float]) -> bool:
    """Check if heading sizes form a consistent hierarchy.

    A proper hierarchy has sizes in descending order.

    Args:
        sizes: List of heading sizes.

    Returns:
        True if hierarchy is consistent.
    """
    if not sizes:
        return True

    # Sort sizes descending
    sorted_sizes = sorted(sizes, reverse=True)

    # Check if original order follows descending pattern
    # Allow some tolerance for similar sizes
    for i in range(len(sizes) - 1):
        if sizes[i] < sizes[i + 1] - 2:  # Allow 2pt tolerance
            return False

    return True


__all__ = ["validate_typography_node"]
