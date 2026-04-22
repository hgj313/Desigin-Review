"""Reporting domain repository interfaces."""

from typing import Protocol

from src_v2.domain.reporting.entities import Report, TrendRecord

__all__ = [
    "IReportRepository",
    "ITrendRepository",
]


class IReportRepository(Protocol):
    """Repository interface for report persistence."""

    def store(self, report: Report) -> None:
        """Store a report."""
        ...

    def find_by_id(self, id: str) -> Report | None:
        """Find a report by its ID."""
        ...

    def find_by_document_path(self, path: str) -> list[Report]:
        """Find all reports for a given document path."""
        ...

    def find_latest(self, path: str) -> Report | None:
        """Find the most recent report for a document path."""
        ...


class ITrendRepository(Protocol):
    """Repository interface for trend record persistence."""

    def store_trend(self, trend: TrendRecord) -> None:
        """Store a trend record."""
        ...

    def get_trends_by_path(self, path: str) -> list[TrendRecord]:
        """Retrieve all trend records for a document path."""
        ...