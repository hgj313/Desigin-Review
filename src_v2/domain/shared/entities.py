"""Shared domain entities - cross-context kernel for DDD bounded contexts."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Literal

__all__ = [
    "Finding",
    "ReviewContext",
    "ReviewResult",
    "ReviewDimension",
    "SeverityLevel",
    "suggestion",
]


class SeverityLevel(IntEnum):
    """Severity level for findings, lower number = more severe."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class ReviewDimension(IntEnum):
    """Dimensions along which a document can be reviewed."""

    STRUCTURE = 1
    TERMINOLOGY = 2
    LAYOUT = 3
    ACCESSIBILITY = 4
    SEMANTIC = 5
    CONSISTENCY = 6


@dataclass
class Finding:
    """A single issue discovered during document review."""

    id: str
    dimension: ReviewDimension
    severity: SeverityLevel
    rule_id: str
    description: str
    location: str
    suggestion: str
    evidence: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReviewContext:
    """Captures the context of a review session."""

    document_id: str
    document_type: Literal["prd", "prototype"]
    review_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    findings: list[Finding] = field(default_factory=list)


@dataclass
class ReviewResult:
    """Outcome of a document review session."""

    context: ReviewContext
    compliance_score: int  # 0-100
    summary: str
    recommendations: list[str] = field(default_factory=list)