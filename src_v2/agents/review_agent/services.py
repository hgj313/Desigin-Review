"""Report generation service implementation for aggregating findings into reports."""
import uuid
from datetime import datetime
from typing import Literal

from src_v2.domain.reporting.entities import Report, ReportSeverityBreakdown
from src_v2.domain.reporting.services import IReportGenerationService
from src_v2.domain.shared.entities import Finding, SeverityLevel, ReviewResult, ReviewContext

__all__ = ["ReportGenerationServiceImpl"]


class ReportGenerationServiceImpl(IReportGenerationService):
    """Implementation of report generation service.

    Aggregates findings from PRD and prototype reviews into a Report entity.
    Calculates compliance score and severity breakdown per findings.
    """

    def generate_report(self, review_result: ReviewResult, format: str) -> Report:
        """Generate a report from review result.

        Args:
            review_result: ReviewResult containing context, score, and recommendations
            format: Output format (currently unused, always returns Report entity)

        Returns:
            Report entity with aggregated findings
        """
        findings = review_result.context.findings

        # Calculate severity breakdown
        severity_breakdown = self._calculate_severity_breakdown(findings)

        # Generate summary
        summary = self.format_summary(review_result.compliance_score, len(findings))

        return Report(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            document_path=review_result.context.document_id,
            document_type=review_result.context.document_type,
            findings=findings,
            compliance_score=review_result.compliance_score,
            summary=summary,
            severity_breakdown=severity_breakdown,
            recommendations=review_result.recommendations,
        )

    def _calculate_severity_breakdown(self, findings: list[Finding]) -> ReportSeverityBreakdown:
        """Calculate severity breakdown from findings.

        Args:
            findings: List of Finding objects

        Returns:
            ReportSeverityBreakdown with counts per severity
        """
        # Count findings per severity (accumulators are mutable)
        critical = high = medium = low = 0
        for f in findings:
            if f.severity == SeverityLevel.CRITICAL:
                critical += 1
            elif f.severity == SeverityLevel.HIGH:
                high += 1
            elif f.severity == SeverityLevel.MEDIUM:
                medium += 1
            elif f.severity == SeverityLevel.LOW:
                low += 1
        return ReportSeverityBreakdown(
            critical=critical,
            high=high,
            medium=medium,
            low=low,
        )

    def format_findings(self, findings: list[Finding]) -> str:
        """Format findings as a human-readable string.

        Args:
            findings: List of Finding objects

        Returns:
            Formatted string representation of findings
        """
        if not findings:
            return "No findings to report."

        lines = []
        for f in findings:
            severity_name = f.severity.name
            lines.append(f"[{severity_name}] {f.description}")
            lines.append(f"  Location: {f.location}")
            lines.append(f"  Suggestion: {f.suggestion}")
            lines.append("")
        return "\n".join(lines)

    def format_summary(self, score: int, finding_count: int) -> str:
        """Format a summary string from score and finding count.

        Args:
            score: Compliance score (0-100)
            finding_count: Number of findings

        Returns:
            Formatted summary string
        """
        if finding_count == 0:
            return f"Compliance score: {score}/100. No issues found."

        return f"Compliance score: {score}/100. {finding_count} issue(s) found."
