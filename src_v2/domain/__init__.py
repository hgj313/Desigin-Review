"""v2.0 Domain Layer

This module contains the core domain logic for the Design Doc Review Agent.
Organized into three bounded contexts:

- ingestion: Document摄取, chunking, embedding
- review: PRD and prototype review
- reporting: Report generation and trend tracking

Plus a shared kernel for cross-context entities:
- shared: Finding, Severity, ReviewContext

All services and repositories are defined as Protocol interfaces.
Implementations belong in infrastructure layer.
"""

from src_v2.domain.shared.entities import (
    Finding,
    ReviewContext,
    ReviewDimension,
    ReviewResult,
    SeverityLevel,
)
from src_v2.domain.shared.value_objects import ChunkId, DocumentId, StandardId

from src_v2.domain.ingestion.entities import (
    Chunk,
    Document,
    DocumentContentType,
    Standard,
)

from src_v2.domain.review.entities import (
    ConsistencyIssue,
    CrossReference,
    VagueLanguagePattern,
)

from src_v2.domain.reporting.entities import (
    Report,
    ReportSeverityBreakdown,
    TrendRecord,
)

__all__ = [
    # shared kernel
    "Finding",
    "ReviewContext",
    "ReviewDimension",
    "ReviewResult",
    "SeverityLevel",
    "ChunkId",
    "DocumentId",
    "StandardId",
    # ingestion
    "Chunk",
    "Document",
    "DocumentContentType",
    "Standard",
    # review
    "VagueLanguagePattern",
    "CrossReference",
    "ConsistencyIssue",
    # reporting
    "Report",
    "ReportSeverityBreakdown",
    "TrendRecord",
]