"""Review bounded context - service interfaces (Protocols)."""

from typing import Protocol

from src_v2.domain.ingestion.entities import Document, Standard
from src_v2.domain.ingestion.repositories import IStandardRepository
from src_v2.domain.review.entities import ConsistencyIssue
from src_v2.domain.shared.entities import Finding, ReviewResult

__all__ = [
    "IPRDReviewerService",
    "IPrototypeReviewerService",
    "IReviewAggregationService",
]


class IPRDReviewerService(Protocol):
    """Protocol for PRD document review operations."""

    def detect_vague_language(self, doc: Document) -> list[Finding]:
        """Detect vague or ambiguous language patterns in a PRD."""
        ...

    def validate_cross_references(
        self, doc: Document, standards: list[Standard]
    ) -> list[Finding]:
        """Validate that cross-references in the document are valid."""
        ...

    def analyze_semantic_completeness(self, doc: Document) -> list[Finding]:
        """Analyze whether the document covers all required semantic elements."""
        ...

    def calculate_semantic_score(self, doc: Document) -> int:
        """Calculate a semantic completeness score (0-100)."""
        ...


class IPrototypeReviewerService(Protocol):
    """Protocol for prototype review operations."""

    def detect_visual_consistency(self, screens: list[Document]) -> list[ConsistencyIssue]:
        """Detect visual inconsistencies across prototype screens."""
        ...

    def validate_color_consistency(
        self, screens: list[Document], standards: list[Standard]
    ) -> list[Finding]:
        """Validate color usage consistency against design standards."""
        ...

    def validate_typography_consistency(
        self, screens: list[Document], standards: list[Standard]
    ) -> list[Finding]:
        """Validate typography consistency against design standards."""
        ...

    def validate_spacing_consistency(
        self, screens: list[Document], standards: list[Standard]
    ) -> list[Finding]:
        """Validate spacing consistency against design standards."""
        ...


class IReviewAggregationService(Protocol):
    """Protocol for aggregating and scoring review findings."""

    def aggregate_findings(self, findings: list[Finding]) -> ReviewResult:
        """Aggregate multiple findings into a consolidated review result."""
        ...

    def calculate_compliance_score(self, findings: list[Finding]) -> int:
        """Calculate a compliance score (0-100) from a list of findings."""
        ...
