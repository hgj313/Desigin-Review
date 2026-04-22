"""Reporting bounded context — report generation and trend tracking."""

from src_v2.domain.reporting.entities import (
    Report,
    ReportSeverityBreakdown,
    TrendRecord,
)
from src_v2.domain.reporting.repositories import (
    IReportRepository,
    ITrendRepository,
)
from src_v2.domain.reporting.services import (
    IReportGenerationService,
    ITrendTrackingService,
)

__all__ = [
    # entities
    "Report",
    "ReportSeverityBreakdown",
    "TrendRecord",
    # service interfaces
    "IReportGenerationService",
    "ITrendTrackingService",
    # repository interfaces
    "IReportRepository",
    "ITrendRepository",
]