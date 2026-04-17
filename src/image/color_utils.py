"""WCAG color contrast calculation utilities.

Provides relative luminance and contrast ratio calculations per WCAG 2.1.
Used for accessibility checking in image review validators.

References:
- WCAG 2.1: https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
- IMG-05: Accessibility contrast checking
"""

import math


def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.1.

    Formula: https://www.w3.org/TR/WCAG21/#dfn-relative-luminance

    Args:
        r: Red channel (0-255)
        g: Green channel (0-255)
        b: Blue channel (0-255)

    Returns:
        Relative luminance value (0.0 to 1.0)
    """
    def adjust_channel(c: int) -> float:
        c = c / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r, g, b = adjust_channel(r), adjust_channel(g), adjust_channel(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> float:
    """Calculate contrast ratio between two colors.

    Args:
        color1: RGB tuple (r, g, b)
        color2: RGB tuple (r, g, b)

    Returns:
        Contrast ratio from 1 to 21 (e.g., 4.5:1).
    """
    lum1 = relative_luminance(*color1)
    lum2 = relative_luminance(*color2)

    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)

    return (lighter + 0.05) / (darker + 0.05)


# WCAG AA thresholds
WCAG_AA_NORMAL_TEXT = 4.5  # Minimum 4.5:1 for normal text
WCAG_AA_LARGE_TEXT = 3.0    # Minimum 3.0:1 for large text (18pt+ or 14pt+ bold)
WCAG_AA_UI_COMPONENTS = 3.0 # Minimum 3.0:1 for UI components


def check_wcag_compliance(
    text_color: tuple[int, int, int],
    bg_color: tuple[int, int, int],
    text_size: float = 14.0,
) -> dict:
    """Check WCAG AA compliance for text/background combination.

    Args:
        text_color: RGB tuple for text color
        bg_color: RGB tuple for background color
        text_size: Font size in points (default 14.0)

    Returns:
        dict with ratio, required threshold, compliant status, and level.
    """
    ratio = contrast_ratio(text_color, bg_color)

    # Determine required threshold based on text size
    if text_size >= 18 or (text_size >= 14 and text_size < 18):
        required = WCAG_AA_LARGE_TEXT
    else:
        required = WCAG_AA_NORMAL_TEXT

    compliant = ratio >= required

    return {
        "ratio": round(ratio, 2),
        "required": required,
        "compliant": compliant,
        "level": "AA" if compliant else "Fail",
        "ratio_string": f"{ratio:.1f}:1",
    }


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple.

    Args:
        hex_color: Hex color string like "#FF5500" or "FF5500"

    Returns:
        RGB tuple (r, g, b)
    """
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB tuple to hex color string.

    Args:
        r: Red channel (0-255)
        g: Green channel (0-255)
        b: Blue channel (0-255)

    Returns:
        Hex color string like "#FF5500"
    """
    return f"#{r:02x}{g:02x}{b:02x}"


__all__ = [
    "relative_luminance",
    "contrast_ratio",
    "check_wcag_compliance",
    "hex_to_rgb",
    "rgb_to_hex",
    "WCAG_AA_NORMAL_TEXT",
    "WCAG_AA_LARGE_TEXT",
    "WCAG_AA_UI_COMPONENTS",
]
