"""Prototype Reviewer Service - Visual consistency validation for prototype screens.

Per D-08: CIEDE2000 ΔE < 10 threshold for color consistency
Per D-09: Typography consistency (same family AND weight)
Per D-10: Spacing consistency (relative error < 15%)
"""

from __future__ import annotations

__all__ = ["PrototypeReviewerService"]

import re
import uuid
from datetime import datetime
from typing import Protocol

from src_v2.domain.ingestion.entities import Document, Standard
from src_v2.domain.review.entities import ConsistencyIssue
from src_v2.domain.shared.entities import Finding, ReviewDimension, SeverityLevel

try:
    from src_v2.infrastructure.color.ciede2000 import calculate_delta_e_2000, colors_consistent
except ImportError:
    # Fallback if ciede2000 not yet available
    calculate_delta_e_2000 = None
    colors_consistent = None


class IVisionClient(Protocol):
    """Protocol for vision client (MiniMax Vision API)."""

    def extract_colors(self, image_path: str) -> list[str]:
        """Extract color palette from image as hex strings."""
        ...

    def extract_typography(self, image_path: str) -> dict:
        """Extract typography info: family, weight, size."""
        ...

    def extract_spacing(self, image_path: str) -> dict:
        """Extract spacing values: margins, padding, gaps."""
        ...


class IEmbeddingFn(Protocol):
    """Protocol for embedding function (bge-m3)."""

    def embed_query(self, text: str) -> list[float]:
        """Embed a single text query."""
        ...


class IPrototypeReviewerService(Protocol):
    """Protocol for prototype visual review operations."""

    def detect_visual_consistency(self, screens: list[Document]) -> list[ConsistencyIssue]:
        """Detect inconsistencies across prototype screens."""
        ...

    def validate_color_consistency(
        self, screens: list[Document], standards: list[Standard]
    ) -> list[Finding]:
        """Validate color usage consistency against design standards."""
        ...

    def validate_typography_consistency(
        self, screens: list[Document], standards: list[Standard]
    ) -> list[Finding]:
        """Validate typography consistency against design standards."""
        ...

    def validate_spacing_consistency(
        self, screens: list[Document], standards: list[Standard]
    ) -> list[Finding]:
        """Validate spacing consistency against design standards."""
        ...


class PrototypeReviewerService:
    """Prototype Reviewer Service for visual consistency validation.

    Validates:
    - Color consistency using CIEDE2000 ΔE < 10 threshold (D-08)
    - Typography consistency (same family AND weight) (D-09)
    - Spacing consistency (relative error < 15%) (D-10)

    Color severity:
    - ΔE >= 20: HIGH
    - ΔE >= 10: MEDIUM

    Typography severity: HIGH (font inconsistency is major issue)

    Spacing severity: MEDIUM (15% tolerance allows variation)
    """

    def __init__(self, vision_client: IVisionClient | None = None, embedding_fn: IEmbeddingFn | None = None):
        """Initialize PrototypeReviewerService.

        Args:
            vision_client: MiniMax Vision API client for image analysis
            embedding_fn: bge-m3 embedding function for cross-screen matching
        """
        self._vision = vision_client
        self._embedding = embedding_fn

    def detect_visual_consistency(self, screens: list[Document]) -> list[ConsistencyIssue]:
        """Detect visual inconsistencies across prototype screens.

        Orchestrates multi-screen analysis by calling:
        - validate_color_consistency
        - validate_typography_consistency
        - validate_spacing_consistency

        Args:
            screens: List of prototype screen Documents

        Returns:
            List of ConsistencyIssue objects
        """
        findings = []

        # Run all validation methods
        findings.extend(self.validate_color_consistency(screens, []))
        findings.extend(self.validate_typography_consistency(screens, []))
        findings.extend(self.validate_spacing_consistency(screens, []))

        # Convert findings to consistency issues
        issues = []
        for f in findings:
            issue_type_map = {
                "proto-color-001": "color",
                "proto-typography-001": "typography",
                "proto-spacing-001": "spacing",
            }
            issue_type = issue_type_map.get(f.rule_id, "spacing")

            issue = ConsistencyIssue(
                issue_type=issue_type,
                description=f.description,
                severity=f.severity,
                elements=[f.location],
            )
            issues.append(issue)

        return issues

    def validate_color_consistency(
        self, screens: list[Document], standards: list[Standard]
    ) -> list[Finding]:
        """Validate color usage consistency against design standards.

        Per D-08: CIEDE2000 ΔE < 10 is consistent, >= 10 is inconsistent.
        Severity:
        - ΔE >= 20: HIGH
        - ΔE >= 10: MEDIUM

        Args:
            screens: List of prototype screen Documents
            standards: List of design standards (unused for color validation)

        Returns:
            List of Finding objects for color inconsistencies
        """
        if calculate_delta_e_2000 is None:
            return []

        findings = []

        if len(screens) < 2:
            return findings

        # Extract color palettes from all screens
        palettes = []
        for screen in screens:
            if self._vision:
                colors = self._vision.extract_colors(screen.content)
            else:
                colors = self._extract_colors_from_text(screen.content)
            palettes.append(colors)

        # Compare colors across all screen pairs
        for i in range(len(screens)):
            for j in range(i + 1, len(screens)):
                screen_i_colors = palettes[i]
                screen_j_colors = palettes[j]

                if not screen_i_colors or not screen_j_colors:
                    continue

                # Compare dominant colors (first color from each palette)
                delta_e = calculate_delta_e_2000(
                    screen_i_colors[0],
                    screen_j_colors[0]
                )

                if delta_e >= 10:
                    severity = SeverityLevel.HIGH if delta_e >= 20 else SeverityLevel.MEDIUM

                    findings.append(
                        Finding(
                            id=str(uuid.uuid4()),
                            dimension=ReviewDimension.CONSISTENCY,
                            severity=severity,
                            rule_id="proto-color-001",
                            description="Color inconsistency detected across screens",
                            location=f"Screen {i+1} vs Screen {j+1}",
                            suggestion="Ensure consistent color usage per design system",
                            evidence=f"ΔE = {delta_e:.1f}",
                            created_at=datetime.now(),
                        )
                    )

        return findings

    def validate_typography_consistency(
        self, screens: list[Document], standards: list[Standard]
    ) -> list[Finding]:
        """Validate typography consistency against design standards.

        Per D-09: Font family AND weight must match EXACTLY.
        Different font family = HIGH severity Finding.

        Args:
            screens: List of prototype screen Documents
            standards: List of design standards (unused for typography validation)

        Returns:
            List of Finding objects for typography inconsistencies
        """
        findings = []

        if len(screens) < 2:
            return findings

        # Extract typography from all screens
        typography_list = []
        for screen in screens:
            if self._vision:
                typo = self._vision.extract_typography(screen.content)
            else:
                typo = self._extract_typography_from_text(screen.content)
            typography_list.append(typo)

        # Compare typography across all screen pairs
        for i in range(len(screens)):
            for j in range(i + 1, len(screens)):
                typo_i = typography_list[i]
                typo_j = typography_list[j]

                # Check font family (must match exactly)
                if typo_i.get("family") != typo_j.get("family"):
                    findings.append(
                        Finding(
                            id=str(uuid.uuid4()),
                            dimension=ReviewDimension.CONSISTENCY,
                            severity=SeverityLevel.HIGH,
                            rule_id="proto-typography-001",
                            description=f"Typography inconsistency: {typo_i.get('family', 'Unknown')} vs {typo_j.get('family', 'Unknown')}",
                            location=f"Screen {i+1} vs Screen {j+1}",
                            suggestion="Use consistent font family and weight across screens",
                            evidence=f"family: {typo_i.get('family', 'None')} vs {typo_j.get('family', 'None')}, weight: {typo_i.get('weight', 'None')} vs {typo_j.get('weight', 'None')}",
                            created_at=datetime.now(),
                        )
                    )
                    continue

                # Check font weight (must match exactly)
                if typo_i.get("weight") != typo_j.get("weight"):
                    findings.append(
                        Finding(
                            id=str(uuid.uuid4()),
                            dimension=ReviewDimension.CONSISTENCY,
                            severity=SeverityLevel.HIGH,
                            rule_id="proto-typography-001",
                            description=f"Typography inconsistency: weight mismatch",
                            location=f"Screen {i+1} vs Screen {j+1}",
                            suggestion="Use consistent font family and weight across screens",
                            evidence=f"family: {typo_i.get('family', 'None')} vs {typo_j.get('family', 'None')}, weight: {typo_i.get('weight', 'None')} vs {typo_j.get('weight', 'None')}",
                            created_at=datetime.now(),
                        )
                    )

        return findings

    def validate_spacing_consistency(
        self, screens: list[Document], standards: list[Standard]
    ) -> list[Finding]:
        """Validate spacing consistency against design standards.

        Per D-10: Relative error >= 0.15 (15%) is inconsistent.
        Spacing beyond 15% relative error = MEDIUM severity.

        Args:
            screens: List of prototype screen Documents
            standards: List of design standards (unused for spacing validation)

        Returns:
            List of Finding objects for spacing inconsistencies
        """
        findings = []

        if len(screens) < 2:
            return findings

        # Extract spacing from all screens
        spacing_list = []
        for screen in screens:
            if self._vision:
                spacing = self._vision.extract_spacing(screen.content)
            else:
                spacing = self._extract_spacing_from_text(screen.content)
            spacing_list.append(spacing)

        # Compare spacing across all screen pairs
        for i in range(len(screens)):
            for j in range(i + 1, len(screens)):
                space_i = spacing_list[i]
                space_j = spacing_list[j]

                # Compare key spacing values
                for key in ["margin", "padding", "gap"]:
                    val_i = space_i.get(key, 0)
                    val_j = space_j.get(key, 0)

                    if val_i == 0 or val_j == 0:
                        continue

                    relative_error = abs(val_i - val_j) / max(val_i, val_j)

                    if relative_error >= 0.15:
                        findings.append(
                            Finding(
                                id=str(uuid.uuid4()),
                                dimension=ReviewDimension.CONSISTENCY,
                                severity=SeverityLevel.MEDIUM,
                                rule_id="proto-spacing-001",
                                description="Spacing inconsistency detected",
                                location=f"Screen {i+1} vs Screen {j+1}",
                                suggestion="Ensure consistent spacing per 8pt grid system",
                                evidence=f"relative_error: {relative_error:.1%}",
                                created_at=datetime.now(),
                            )
                        )

        return findings

    def _extract_colors_from_text(self, content: str) -> list[str]:
        """Fallback extraction of colors from text (when vision API unavailable)."""
        hex_pattern = r"#[0-9A-Fa-f]{6}"
        return re.findall(hex_pattern, content)

    def _extract_typography_from_text(self, content: str) -> dict:
        """Fallback extraction of typography from text."""
        # Simple parsing - in production would use MiniMax Vision
        return {"family": "Unknown", "weight": "Unknown", "size": 0}

    def _extract_spacing_from_text(self, content: str) -> dict:
        """Fallback extraction of spacing from text."""
        # Simple parsing - in production would use MiniMax Vision
        return {"margin": 0, "padding": 0, "gap": 0}