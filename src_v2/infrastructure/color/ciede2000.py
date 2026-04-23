"""CIEDE2000 color difference calculation for perceptual color consistency checks.

Per D-08: Colors are consistent when CIEDE2000 delta_e < 10.
Reference: https://en.wikipedia.org/wiki/Color_difference#CIEDE2000
"""

from __future__ import annotations

__all__ = [
    "calculate_delta_e_2000",
    "colors_consistent",
    "extract_palette_from_image",
]

from typing import Protocol

import numpy as np

from colormath import color_conversions
from colormath.color_objects import LabColor, sRGBColor
from colormath.color_diff import delta_e_cie2000


def _apply_numpy_asscalar_patch() -> None:
    """Patch deprecated numpy.asscalar for older colormath versions."""
    if not hasattr(np, 'asscalar'):
        # numpy.asscalar was deprecated in numpy 1.16 and removed later
        # Re-add it as an alias to np.asscalar -> np.item
        np.asscalar = lambda x: x.item()


def calculate_delta_e_2000(hex1: str, hex2: str) -> float:
    """Calculate CIEDE2000 perceptual color difference between two hex colors.

    Args:
        hex1: First color as hex string (e.g., '#FF0000' or 'FF0000')
        hex2: Second color as hex string (e.g., '#FF0000' or 'FF0000')

    Returns:
        Delta E value (0 = identical, higher = more different).
        Perceptually: < 1 = imperceptible, 1-2 = slight, 2-10 = noticeable,
        > 10 = very noticeable.

    Example:
        >>> delta = calculate_delta_e_2000('#FF0000', '#FF1100')
        >>> print(f"Similar reds delta_e: {delta}")  # Should be small (e.g., < 5)
    """
    # Apply numpy patch before calling colormath
    _apply_numpy_asscalar_patch()

    # Normalize hex strings (ensure '#' prefix)
    hex1 = hex1.lstrip("#")
    hex2 = hex2.lstrip("#")

    # Parse hex strings to sRGB
    rgb1 = sRGBColor.new_from_rgb_hex(hex1)
    rgb2 = sRGBColor.new_from_rgb_hex(hex2)

    # Convert to Lab color space (perceptual)
    lab1 = color_conversions.convert_color(rgb1, LabColor)
    lab2 = color_conversions.convert_color(rgb2, LabColor)

    # Calculate CIEDE2000 difference
    # Note: colormath uses delta_e_cie2000 (same formula as delta_e_2000)
    delta_e = delta_e_cie2000(lab1, lab2)

    return float(delta_e)


def colors_consistent(hex1: str, hex2: str, threshold: float = 10.0) -> bool:
    """Check if two colors are perceptually consistent.

    Per D-08: Colors are considered consistent when CIEDE2000 delta_e < 10.

    Args:
        hex1: First color as hex string
        hex2: Second color as hex string
        threshold: Maximum delta_e for consistency (default: 10.0 per D-08)

    Returns:
        True if colors are consistent (delta_e < threshold), False otherwise.

    Example:
        >>> colors_consistent('#FF0000', '#FF1100')  # Similar reds
        True
        >>> colors_consistent('#FF0000', '#00FF00')  # Red vs green
        False
    """
    delta_e = calculate_delta_e_2000(hex1, hex2)
    return delta_e < threshold


class PaletteExtractor(Protocol):
    """Protocol for extracting color palettes from images."""

    def extract(self, image_path: str) -> list[str]:
        """Extract dominant colors from image as hex strings."""
        ...


def extract_palette_from_image(image_path: str) -> list[str]:
    """Extract dominant colors from an image file.

    Uses PIL/Pillow to load the image and extracts colors using
    a simple quantization approach.

    Args:
        image_path: Path to the image file

    Returns:
        List of hex color strings representing dominant colors

    Example:
        >>> colors = extract_palette_from_image('screenshot.png')
        >>> print(f"Extracted {len(colors)} colors: {colors[:3]}")
    """
    from PIL import Image

    try:
        img = Image.open(image_path)
    except IOError:
        return []

    # Convert to RGB if necessary
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    # Simple palette extraction via quantization
    # Reduce to 8x8 grid and get unique colors
    img_small = img.resize((8, 8), Image.Resampling.LANCZOS)
    pixels = list(img_small.getdata())

    # Get unique colors and their counts
    color_counts: dict[tuple[int, int, int], int] = {}
    for r, g, b in pixels:
        # Quantize to reduce noise
        qr = (r // 16) * 16
        qg = (g // 16) * 16
        qb = (b // 16) * 16
        color_counts[(qr, qg, qb)] = color_counts.get((qr, qg, qb), 0) + 1

    # Sort by frequency and convert to hex
    sorted_colors = sorted(color_counts.items(), key=lambda x: -x[1])
    hex_colors = []
    for (r, g, b), _ in sorted_colors[:10]:
        hex_colors.append(f"#{r:02X}{g:02X}{b:02X}")

    return hex_colors
