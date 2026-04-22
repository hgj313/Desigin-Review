"""Reporting domain service interfaces."""

from typing import Protocol

from src_v2.domain.reporting.entities import Report, TrendRecord
from src_v2.domain.shared.entities import Finding, ReviewResult

__all__ = [
    "IReportGenerationService",
    "ITrendTrackingService",
]


class IReportGenerationService(Protocol):
    """Service for generating review reports."""

    def generate_report(self, review_result: ReviewResult, format: str) -> Report:
        """Generate a report from a review result."""
        ...

    def format_findings(self, findings: list[Finding]) -> str:
        """Format a list of findings into a string representation."""
        ...

    def format_summary(self, score: int, finding_count: int) -> str:
        """Format a summary string from score and finding count."""
        ...


class ITrendTrackingService(Protocol):
    """Service for tracking compliance trends over time."""

    def record_review(self, record: TrendRecord) -> None:
        """Record a review result for trend tracking."""
        ...

    def get_trend_history(self, document_path: str) -> list[TrendRecord]:
        """Retrieve trend history for a document path."""
        ...

    def calculate_trend(self, document_path: str) -> dict:
        """Calculate trend statistics for a document path."""
        ...