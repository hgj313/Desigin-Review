"""Aggregation service implementing take-most-severe per D-07."""

from __future__ import annotations

__all__ = [
    "aggregate_findings_by_severity",
    "take_most_severe",
    "detect_visual_consistency",
]

from src_v2.domain.ingestion.entities import Document
from src_v2.domain.review.entities import ConsistencyIssue
from src_v2.domain.shared.entities import Finding, SeverityLevel


def take_most_severe(findings: list[Finding]) -> Finding | None:
    """Return the Finding with lowest severity value (most severe).

    Per D-07: Take-most-severe aggregation strategy.
    SeverityLevel.CRITICAL (1) < HIGH (2) < MEDIUM (3) < LOW (4)
    """
    if not findings:
        return None

    return min(findings, key=lambda f: f.severity.value)


def aggregate_findings_by_severity(findings: list[Finding]) -> list[Finding]:
    """Aggregate findings by (dimension, rule_id), keeping most severe per group.

    Per D-07: Take-most-severe aggregation strategy.
    """
    if not findings:
        return []

    groups: dict = {}
    for finding in findings:
        key = (finding.dimension, finding.rule_id)
        if key not in groups:
            groups[key] = []
        groups[key].append(finding)

    aggregated = []
    for key, group_findings in groups.items():
        most_severe = take_most_severe(group_findings)
        if most_severe:
            aggregated.append(most_severe)

    return aggregated


def detect_visual_consistency(screens: list[Document]) -> list[ConsistencyIssue]:
    """Detect visual inconsistencies across prototype screens.

    Convenience function using PrototypeReviewerService with take-most-severe.
    """
    from src_v2.domain.review.services.prototype_reviewer import (
        PrototypeReviewerService,
    )

    reviewer = PrototypeReviewerService()
    return reviewer.detect_visual_consistency(screens)
