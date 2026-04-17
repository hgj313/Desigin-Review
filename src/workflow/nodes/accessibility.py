"""WCAG accessibility contrast checking node.

Performs WCAG AA contrast compliance checking on prototype images
by analyzing text/background color combinations.

References:
- IMG-05: Perform accessibility contrast checking (WCAG AA compliance)
- D-20: Use MiniMaxVisionClient for analysis
"""

import re
from typing import List, Tuple

from src.workflow.state import ImageReviewState, Finding
from src.image.minimax_vision import MiniMaxVisionClient
from src.image.color_utils import check_wcag_compliance, hex_to_rgb


def validate_accessibility_node(state: ImageReviewState) -> ImageReviewState:
    """Check accessibility compliance from prototype image.

    IMG-05: Perform accessibility contrast checking (WCAG AA compliance)

    Uses MiniMaxVisionClient for accessibility analysis per D-20.
    Validates contrast ratios using WCAG 2.1 standard.

    Args:
        state: ImageReviewState with image_path.

    Returns:
        Updated state with accessibility_findings list.

    Severity calibration per D-14:
    - Text contrast < 3:1 (fails even large text) -> Critical
    - Normal text contrast < 4.5:1 -> Major
    - Large text contrast < 3:1 -> Minor
    """
    vision_client = MiniMaxVisionClient()
    image_path = state["image_path"]

    # Check accessibility from image
    accessibility_info = vision_client.check_accessibility(image_path)

    findings: List[Finding] = []

    # Parse accessibility analysis for color/contrast issues
    raw = accessibility_info[0].get("raw", "") if accessibility_info else ""

    # Extract text/background color pairs
    color_pairs = _extract_color_pairs(raw)

    for text_color, bg_color, text_size in color_pairs:
        # Convert hex to RGB if needed
        if isinstance(text_color, str):
            text_color = hex_to_rgb(text_color)
        if isinstance(bg_color, str):
            bg_color = hex_to_rgb(bg_color)

        # Check WCAG compliance
        compliance = check_wcag_compliance(text_color, bg_color, text_size)

        if not compliance["compliant"]:
            # Determine severity based on how far from compliant
            ratio = compliance["ratio"]

            if ratio < 3.0:
                severity = "Critical"
            elif ratio < 4.5:
                severity = "Major"
            else:
                severity = "Minor"

            findings.append(Finding(
                issue_type="accessibility",
                severity=severity,
                location=f"Image: {image_path}",
                description_en=f"Text/background contrast ratio is {compliance['ratio_string']}, required {compliance['required']}:1 for {'large' if text_size >= 18 else 'normal'} text",
                description_zh=f"文字/背景对比度为 {compliance['ratio_string']}，{'大号' if text_size >= 18 else '正常'}文字需要 {compliance['required']}:1",
                suggestion_en=f"Increase contrast by adjusting colors to achieve at least {compliance['required']}:1 ratio",
                suggestion_zh=f"请调整颜色以达到至少 {compliance['required']}:1 的对比度",
            ))

    # If no contrast pairs found, note this
    if not color_pairs:
        findings.append(Finding(
            issue_type="accessibility",
            severity="Suggestion",
            location=f"Image: {image_path}",
            description_en="Could not detect specific color combinations for contrast checking",
            description_zh="未检测到具体的颜色组合进行对比度检查",
            suggestion_en="Ensure sufficient contrast between text and backgrounds",
            suggestion_zh="请确保文字和背景之间有足够的对比度",
        ))

    return {"accessibility_findings": findings}


def _extract_color_pairs(accessibility_text: str) -> List[Tuple]:
    """Extract text/background color pairs from accessibility analysis.

    Args:
        accessibility_text: Raw text from MiniMax accessibility analysis.

    Returns:
        List of (text_color, bg_color, text_size) tuples.
    """
    # Look for hex color codes and text size mentions
    hex_pattern = r'#[0-9A-Fa-f]{6}'

    # Find all hex colors in text
    colors = re.findall(hex_pattern, accessibility_text)

    # Find text sizes
    size_pattern = r'(\d+)(?:pt|px)'
    sizes = [float(m) for m in re.findall(size_pattern, accessibility_text)]

    # Create pairs if we have enough colors
    pairs = []
    if len(colors) >= 2:
        # Assume first color is text, second is background
        text_color = colors[0]
        bg_color = colors[1]
        text_size = sizes[0] if sizes else 14.0
        pairs.append((text_color, bg_color, text_size))

    return pairs


__all__ = ["validate_accessibility_node"]
