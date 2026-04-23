"""Aggregation service for multi-image review findings.

Per D-07: Take-most-severe aggregation strategy.
Groups findings by (dimension, rule_id) and keeps only the most severe.
"""

from __future__ import annotations

__all__ = [
    "aggregate_findings_by_severity",
    "take_most_severe",
    "detect_visual_consistency",
]

from typing import Callable

from src_v2.domain.ingestion.entities import Document
from src_v2.domain.review.entities import ConsistencyIssue
from src_v2.domain.shared.entities import Finding, SeverityLevel


def take_most_severe(findings: list[Finding]) -> Finding | None:
    """Return the Finding with the lowest severity value (most severe).

    Per D-07: Take-most-severe strategy.
    SeverityLevel.CRITICAL (1) < HIGH (2) < MEDIUM (3) < LOW (4)
    Lower number = more severe.

    Args:
        findings: List of Finding objects

    Returns:
        The most severe Finding, or None if findings is empty
    """
    if not findings:
        return None

    return min(findings, key=lambda f: f.severity.value)


def aggregate_findings_by_severity(findings: list[Finding]) -> list[Finding]:
    """Group findings by (dimension, rule_id) and keep only the most severe.

    Per D-07: Take-most-severe aggregation.
    Multiple findings for the same rule_id within the same dimension
    are consolidated to a single Finding (the most severe).

    Args:
        findings: List of Finding objects to aggregate

    Returns:
        Aggregated list of Findings (one per dimension+rule_id combination)
    """
    # Group by (dimension, rule_id)
    groups: dict[tuple, list[Finding]] = {}

    for f in findings:
        key = (f.dimension, f.rule_id)
        if key not in groups:
            groups[key] = []
        groups[key].append(f)

    # For each group, keep only the most severe
    aggregated = []
    for group_findings in groups.values():
        most_severe = take_most_severe(group_findings)
        if most_severe:
            aggregated.append(most_severe)

    return aggregated


def detect_visual_consistency(
    screens: list[Document],
    color_validator: Callable | None = None,
    typography_validator: Callable | None = None,
    spacing_validator: Callable | None = None,
) -> list[ConsistencyIssue]:
    """Detect visual inconsistencies across prototype screens.

    This is a convenience function that orchestrates multi-screen analysis.
    Calls color, typography, and spacing validators, then aggregates findings
    using the take-most-severe strategy per D-07.

    Args:
        screens: List of prototype screen Documents
        color_validator: Callable that returns color Findings
        typography_validator: Callable that returns typography Findings
        spacing_validator: Callable that returns spacing Findings

    Returns:
        List of ConsistencyIssue objects
    """
    all_findings: list[Finding] = []

    # Collect findings from all validators
    if color_validator:
        all_findings.extend(color_validator(screens))

    if typography_validator:
        all_findings.extend(typography_validator(screens))

    if spacing_validator:
        all_findings.extend(spacing_validator(screens))

    # Aggregate by severity (take-most-severe per D-07)
    aggregated = aggregate_findings_by_severity(all_findings)

    # Convert to ConsistencyIssue
    issues = []
    for f in aggregated:
        # Map rule_id to issue_type
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