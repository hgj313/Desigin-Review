"""Spacing and grid validation node.

Validates spacing and grid alignment from prototype images
against 8pt/4pt grid standards.

References:
- IMG-04: Validate spacing and grid alignment against 8pt/4pt grid standards
- D-20: Use MiniMaxVisionClient for analysis
- D-23: 8pt grid for coarse spacing, 4pt for fine spacing
"""

import re
from typing import List

from src.workflow.state import ImageReviewState, Finding
from src.image.minimax_vision import MiniMaxVisionClient


# Grid constants per D-23
GRID_SIZE = 8       # Coarse grid for spacing between components
FINE_GRID_SIZE = 4  # Fine grid for padding within components
GRID_TOLERANCE = 1  # Allow 1px tolerance for rounding


def validate_spacing_node(state: ImageReviewState) -> ImageReviewState:
    """Validate spacing and grid alignment from prototype image.

    IMG-04: Validate spacing and grid alignment against 8pt/4pt grid standards

    Uses MiniMaxVisionClient for spacing measurement per D-20.
    Validates against 8pt/4pt grid per D-23.

    Args:
        state: ImageReviewState with image_path.

    Returns:
        Updated state with spacing_findings list.

    Severity calibration per D-14:
    - Major spacing (>16px) not on 8pt grid -> Major
    - Component padding not on 4pt grid -> Minor
    - Minor visual misalignments -> Suggestion
    """
    vision_client = MiniMaxVisionClient()
    image_path = state["image_path"]

    # Measure spacing from image
    spacing_info = vision_client.measure_spacing(image_path)

    findings: List[Finding] = []

    # Parse spacing measurements and validate against grid
    raw = spacing_info[0].get("raw", "") if spacing_info else ""

    # Extract spacing values
    spacing_values = _extract_spacing_values(raw)

    for spacing in spacing_values:
        is_coarse_aligned = _is_aligned_to_grid(spacing, GRID_SIZE)
        is_fine_aligned = _is_aligned_to_grid(spacing, FINE_GRID_SIZE)

        if spacing > 16 and not is_coarse_aligned:
            # Major spacing should follow 8pt grid
            findings.append(Finding(
                issue_type="spacing",
                severity="Major",
                location=f"Image: {image_path}",
                description_en=f"Spacing of {spacing}px does not align to {GRID_SIZE}pt grid",
                description_zh=f"{spacing}px 间距不符合{GRID_SIZE}pt 网格",
                suggestion_en=f"Adjust spacing to nearest {GRID_SIZE}pt grid value",
                suggestion_zh=f"请调整间距至最近的{GRID_SIZE}pt 网格值",
            ))
        elif spacing > 4 and not is_fine_aligned and not is_coarse_aligned:
            # Smaller spacing should at least follow 4pt grid
            findings.append(Finding(
                issue_type="spacing",
                severity="Minor",
                location=f"Image: {image_path}",
                description_en=f"Spacing of {spacing}px does not align to {FINE_GRID_SIZE}pt grid",
                description_zh=f"{spacing}px 间距不符合{FINE_GRID_SIZE}pt 网格",
                suggestion_en=f"Adjust spacing to nearest {FINE_GRID_SIZE}pt grid value",
                suggestion_zh=f"请调整间距至最近的{FINE_GRID_SIZE}pt 网格值",
            ))

    # If no spacing values found, note this
    if not spacing_values:
        findings.append(Finding(
            issue_type="spacing",
            severity="Suggestion",
            location=f"Image: {image_path}",
            description_en="Could not detect specific spacing values - assuming compliance",
            description_zh="未检测到具体间距值 - 假设合规",
            suggestion_en=None,
            suggestion_zh=None,
        ))

    return {"spacing_findings": findings}


def _extract_spacing_values(spacing_text: str) -> list[float]:
    """Extract spacing values from spacing analysis text.

    Args:
        spacing_text: Raw text from MiniMax spacing analysis.

    Returns:
        List of spacing values in pixels.
    """
    # Look for spacing values like "16px", "8pt", "margin: 16"
    spacing_values = []
    patterns = [
        r'(\d+)(?:px|pt)',
        r'spacing[:\s]+(\d+)',
        r'margin[:\s]+(\d+)',
        r'padding[:\s]+(\d+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, spacing_text)
        for match in matches:
            val = float(match)
            if 2 <= val <= 100:  # Reasonable spacing range
                spacing_values.append(val)

    return spacing_values


def _is_aligned_to_grid(value: float, grid_size: int, tolerance: float = 1.0) -> bool:
    """Check if a spacing value aligns to a grid.

    Args:
        value: Spacing value in pixels.
        grid_size: Grid size (8 or 4).
        tolerance: Allowed deviation tolerance.

    Returns:
        True if value aligns to grid within tolerance.
    """
    remainder = value % grid_size
    return remainder <= tolerance or remainder >= (grid_size - tolerance)


__all__ = ["validate_spacing_node", "GRID_SIZE", "FINE_GRID_SIZE"]
