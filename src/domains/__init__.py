"""DDD Bounded Contexts for Design Doc Review Agent.

Domains:
- prd: PRD document review
- prototype: Prototype image review
- report: Compliance report generation
- shared: Shared Kernel (Finding, Severity)
"""

from .prd import PRDDocument, Section
from .prototype import Prototype, Screen, Component
from .report import Report, ReportSummary
from .shared import Finding, Severity, SeverityLevel, ReviewDimension

__all__ = [
    # PRD Domain
    "PRDDocument",
    "Section",
    # Prototype Domain
    "Prototype",
    "Screen",
    "Component",
    # Report Domain
    "Report",
    "ReportSummary",
    # Shared Kernel
    "Finding",
    "Severity",
    "SeverityLevel",
    "ReviewDimension",
]
