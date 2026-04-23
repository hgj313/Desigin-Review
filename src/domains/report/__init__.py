"""Report Domain - Compliance report bounded context.

Entities:
- Report: The final compliance report aggregate
- ReportSummary: Summary statistics for the report

Services:
- SeverityCalculator: Calculates severity from violation impact
- FindingAggregator: Aggregates findings from PRD and Prototype
- BilingualReportFormatter: Formats reports in Chinese/English
"""

from .entities import Report, ReportSummary
from .services import (
    SeverityCalculator,
    FindingAggregator,
    BilingualReportFormatter,
)

__all__ = [
    "Report",
    "ReportSummary",
    "SeverityCalculator",
    "FindingAggregator",
    "BilingualReportFormatter",
]
