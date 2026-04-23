"""Prototype Domain Services - Vision analysis and layout validation.

Services:
- VisionAnalyzer: Analyzes prototype images using MiniMax Vision API
- LayoutValidator: Validates spacing and grid alignment
- AccessibilityChecker: Checks WCAG accessibility compliance

References:
- ARCHITECTURE.md: Prototype Context Services section
- FEATURES.md: Prototype validation tools
"""

from typing import Optional
import os

from src.domains.prototype.entities import Prototype, Screen, Component
from src.domains.shared import Finding, SeverityLevel, ReviewDimension


class VisionAnalyzer:
    """Analyzes prototype images using MiniMax Vision API.

    Extracts:
    - Color palette
    - Typography hierarchy
    - Spacing/grid system
    - Component layout
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Vision analyzer.

        Args:
            api_key: MiniMax API key. Defaults to env MINIMAX_API_KEY.
        """
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY")

    def analyze(self, prototype: Prototype, analysis_type: str = "full") -> dict:
        """Analyze prototype images.

        Args:
            prototype: Prototype to analyze
            analysis_type: Type of analysis - "full", "color", "typography", "spacing", "accessibility"

        Returns:
            Dict with analysis results
        """
        from src.image.minimax_vision import MiniMaxVisionClient

        client = MiniMaxVisionClient(api_key=self.api_key)
        results = []

        for image_path in prototype.image_paths:
            if not os.path.exists(image_path):
                results.append({"error": f"File not found: {image_path}"})
                continue

            try:
                analysis = client.analyze_ui_image(image_path, analysis_type)
                results.append({
                    "image_path": image_path,
                    "analysis_type": analysis_type,
                    "raw_response": analysis.get("raw_response", ""),
                })
            except Exception as e:
                results.append({"error": str(e), "image_path": image_path})

        return {
            "analysis_type": analysis_type,
            "results": results,
            "prototype_analyzed": bool(results),
        }

    def extract_color_palette(self, prototype: Prototype) -> list[dict]:
        """Extract color palette from prototype.

        Args:
            prototype: Prototype to analyze

        Returns:
            List of color dicts with hex, rgb, usage
        """
        analysis = self.analyze(prototype, analysis_type="color")
        # Parse raw response into structured format
        # For now, return raw - will be parsed in validator
        colors = []
        for result in analysis.get("results", []):
            if "raw_response" in result:
                colors.append({"raw": result["raw_response"]})
        return colors

    def analyze_typography(self, prototype: Prototype) -> list[dict]:
        """Analyze typography hierarchy.

        Args:
            prototype: Prototype to analyze

        Returns:
            List of typography elements
        """
        analysis = self.analyze(prototype, analysis_type="typography")
        typography = []
        for result in analysis.get("results", []):
            if "raw_response" in result:
                typography.append({"raw": result["raw_response"]})
        return typography

    def measure_spacing(self, prototype: Prototype) -> list[dict]:
        """Measure spacing and grid alignment.

        Args:
            prototype: Prototype to analyze

        Returns:
            List of spacing measurements
        """
        analysis = self.analyze(prototype, analysis_type="spacing")
        spacing = []
        for result in analysis.get("results", []):
            if "raw_response" in result:
                spacing.append({"raw": result["raw_response"]})
        return spacing


class LayoutValidator:
    """Validates layout against design standards.

    Checks:
    - 8pt grid alignment
    - Consistent spacing
    - Component alignment
    """

    GRID_SIZE = 8  # 8pt grid system

    def validate(self, prototype: Prototype, standards: Optional[list[str]] = None) -> list[Finding]:
        """Validate prototype layout.

        Args:
            prototype: Prototype to validate
            standards: Optional layout standards

        Returns:
            List of findings
        """
        findings = []

        # Analyze with Vision
        analyzer = VisionAnalyzer()
        spacing_results = analyzer.measure_spacing(prototype)

        # Check grid alignment
        findings.extend(self._check_grid_alignment(spacing_results))

        # Check spacing consistency
        findings.extend(self._check_spacing_consistency(spacing_results))

        return findings

    def _check_grid_alignment(self, spacing_results: list[dict]) -> list[Finding]:
        """Check if spacing aligns to 8pt grid."""
        findings = []

        for result in spacing_results:
            raw = result.get("raw", "")
            # Simplified check - full impl would parse actual measurements
            if "8pt" in raw or "8 pt" in raw:
                continue  # Properly aligned

            # Check for non-8pt spacing
            findings.append(Finding(
                source_context="prototype",
                dimension=ReviewDimension.LAYOUT,
                severity=SeverityLevel.MEDIUM,
                rule_id="proto-layout-001",
                description="Spacing may not align to 8pt grid",
                location="Prototype layout",
                suggestion="Ensure all spacing uses multiples of 8pt (e.g., 8, 16, 24, 32)",
                evidence=raw[:200] if raw else "No grid alignment detected",
            ))

        return findings

    def _check_spacing_consistency(self, spacing_results: list[dict]) -> list[Finding]:
        """Check for consistent spacing between elements."""
        findings = []

        # This is a simplified check - full implementation would
        # compare actual measurements across the prototype
        return findings


class AccessibilityChecker:
    """Checks accessibility compliance against WCAG guidelines.

    Validates:
    - Color contrast ratios
    - Text size minimums
    - Touch target sizes
    """

    MIN_CONTRAST_RATIO = 4.5  # WCAG AA requirement
    MIN_TEXT_SIZE = 12  # pixels
    MIN_TOUCH_TARGET = 44  # pixels (WCAG 2.1)

    def validate(self, prototype: Prototype, standards: Optional[list[str]] = None) -> list[Finding]:
        """Validate prototype accessibility.

        Args:
            prototype: Prototype to validate
            standards: Optional accessibility standards

        Returns:
            List of findings
        """
        findings = []

        # Analyze with Vision
        analyzer = VisionAnalyzer()
        accessibility_results = analyzer.analyze(prototype, analysis_type="accessibility")

        # Check contrast
        findings.extend(self._check_contrast(accessibility_results))

        # Check text sizing
        findings.extend(self._check_text_size(accessibility_results))

        return findings

    def _check_contrast(self, accessibility_results: dict) -> list[Finding]:
        """Check color contrast compliance."""
        findings = []

        for result in accessibility_results.get("results", []):
            raw = result.get("raw", "")
            # Simplified - full implementation would parse actual contrast ratios
            if "contrast" in raw.lower() or "对比度" in raw:
                if "fail" in raw.lower() or "不足" in raw:
                    findings.append(Finding(
                        source_context="prototype",
                        dimension=ReviewDimension.ACCESSIBILITY,
                        severity=SeverityLevel.HIGH,
                        rule_id="proto-a11y-001",
                        description="Color contrast may be insufficient",
                        location="Prototype accessibility",
                        suggestion="Ensure text/background contrast ratio is at least 4.5:1 (WCAG AA)",
                    ))

        return findings

    def _check_text_size(self, accessibility_results: dict) -> list[Finding]:
        """Check minimum text size compliance."""
        findings = []

        for result in accessibility_results.get("results", []):
            raw = result.get("raw", "")
            # Simplified - would parse actual font sizes
            if "small" in raw.lower() or "小" in raw:
                findings.append(Finding(
                    source_context="prototype",
                    dimension=ReviewDimension.ACCESSIBILITY,
                    severity=SeverityLevel.MEDIUM,
                    rule_id="proto-a11y-002",
                    description="Text size may be too small for accessibility",
                    location="Prototype typography",
                    suggestion="Ensure body text is at least 12px, preferably 14px or larger",
                ))

        return findings
