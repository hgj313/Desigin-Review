"""Report Domain - Report and Summary entities.

Entities:
- Report: The final compliance report aggregate
- ReportSummary: Summary statistics for the report

References:
- ARCHITECTURE.md: Report Context section
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from src.domains.shared import Finding, SeverityLevel


@dataclass
class ReportSummary:
    """Summary statistics for a compliance report.

    Attributes:
        prd_findings_count: Number of findings from PRD review
        prototype_findings_count: Number of findings from Prototype review
        prototype_analyzed: Whether prototype was included in review
        total_findings: Total findings across all sources
        critical_count: Number of CRITICAL severity findings
        high_count: Number of HIGH severity findings
        medium_count: Number of MEDIUM severity findings
        low_count: Number of LOW severity findings
        compliance_score: Overall compliance score (0-100)
    """
    prd_findings_count: int = 0
    prototype_findings_count: int = 0
    prototype_analyzed: bool = False
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    compliance_score: int = 100

    def calculate_from_findings(self, findings: list[Finding], prototype_analyzed: bool) -> None:
        """Calculate summary statistics from findings list.

        Args:
            findings: List of all findings
            prototype_analyzed: Whether prototype was included in review
        """
        self.prototype_analyzed = prototype_analyzed
        self.prd_findings_count = sum(1 for f in findings if f.source_context == "prd")
        self.prototype_findings_count = sum(1 for f in findings if f.source_context == "prototype")
        self.total_findings = len(findings)

        # Count by severity
        self.critical_count = sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)
        self.high_count = sum(1 for f in findings if f.severity == SeverityLevel.HIGH)
        self.medium_count = sum(1 for f in findings if f.severity == SeverityLevel.MEDIUM)
        self.low_count = sum(1 for f in findings if f.severity == SeverityLevel.LOW)

        # Calculate compliance score (higher = better)
        total_weight = (
            self.critical_count * 10 +
            self.high_count * 5 +
            self.medium_count * 2 +
            self.low_count * 1
        )
        self.compliance_score = max(0, 100 - total_weight)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "prd_findings_count": self.prd_findings_count,
            "prototype_findings_count": self.prototype_findings_count,
            "prototype_analyzed": self.prototype_analyzed,
            "total_findings": self.total_findings,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "compliance_score": self.compliance_score,
        }


@dataclass
class Report:
    """A compliance report generated from review findings.

    Attributes:
        id: Unique report identifier
        timestamp: When the report was generated
        document_path: Path to the reviewed document
        findings: All findings from the review
        summary: Summary statistics
        severity_breakdown: Findings grouped by severity
        language: Report language ("zh" | "en" | "bilingual")
    """
    document_path: str
    findings: list[Finding] = field(default_factory=list)
    summary: ReportSummary = field(default_factory=ReportSummary)
    severity_breakdown: dict = field(default_factory=dict)
    language: str = "bilingual"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def generate(self) -> None:
        """Generate the report by calculating summary and breakdown.

        Call this after adding all findings.
        """
        # Calculate summary
        self.summary.calculate_from_findings(self.findings, self.summary.prototype_analyzed)

        # Group findings by severity
        self.severity_breakdown = {
            "CRITICAL": [f.to_dict() for f in self.findings if f.severity == SeverityLevel.CRITICAL],
            "HIGH": [f.to_dict() for f in self.findings if f.severity == SeverityLevel.HIGH],
            "MEDIUM": [f.to_dict() for f in self.findings if f.severity == SeverityLevel.MEDIUM],
            "LOW": [f.to_dict() for f in self.findings if f.severity == SeverityLevel.LOW],
        }

    def add_findings(self, findings: list[Finding]) -> None:
        """Add findings to the report.

        Args:
            findings: Findings to add
        """
        self.findings.extend(findings)

    def to_dict(self) -> dict:
        """Convert report to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "document_path": self.document_path,
            "summary": self.summary.to_dict(),
            "severity_breakdown": self.severity_breakdown,
            "language": self.language,
            "findings": [f.to_dict() for f in self.findings],
        }
