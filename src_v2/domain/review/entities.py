"""Review bounded context - PRD and prototype review services."""

from dataclasses import dataclass, field
from typing import Literal

from src_v2.domain.shared.entities import Finding, SeverityLevel

__all__ = [
    "VagueLanguagePattern",
    "CrossReference",
    "ConsistencyIssue",
]


@dataclass
class VagueLanguagePattern:
    """A detected pattern of vague language in a document."""

    pattern: str
    severity: SeverityLevel
    examples: list[str] = field(default_factory=list)


@dataclass
class CrossReference:
    """A reference from one document element to another."""

    source_id: str
    target_id: str
    reference_type: str


@dataclass
class ConsistencyIssue:
    """A detected inconsistency across design elements."""

    issue_type: Literal["color", "typography", "spacing"]
    description: str
    severity: SeverityLevel
    elements: list[str] = field(default_factory=list)
