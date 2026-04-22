"""Reporting domain entities and value objects."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from src_v2.domain.shared.entities import Finding

__all__ = [
    "ReportSeverityBreakdown",
    "Report",
    "TrendRecord",
]


@dataclass(frozen=True)
class ReportSeverityBreakdown:
    """Breakdown of findings by severity level."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


@dataclass
class Report:
    """A generated review report."""

    id: str
    timestamp: datetime
    document_path: str
    document_type: Literal["prd", "prototype"]
    findings: list[Finding]
    compliance_score: int
    summary: str
    severity_breakdown: ReportSeverityBreakdown
    recommendations: list[str] = field(default_factory=list)


@dataclass
class TrendRecord:
    """A single point in time for tracking compliance trends."""

    timestamp: datetime
    document_path: str
    compliance_score: int
    finding_counts: dict[str, int]