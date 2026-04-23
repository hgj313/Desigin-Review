"""Shared Kernel - Finding and Severity entities shared across all domains.

This module contains entities that are shared between PRD, Prototype, and Report
bounded contexts. All cross-context communication happens through these entities.

References:
- ARCHITECTURE.md: Shared Kernel pattern
- PITFALLS.md: PP-05 source_context labeling
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class SeverityLevel(Enum):
    """Severity levels for findings, ordered from most to least severe."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

    def __str__(self) -> str:
        return self.name


class ReviewDimension(Enum):
    """Review dimensions that findings can belong to."""
    STRUCTURE = "structure"
    TERMINOLOGY = "terminology"
    LAYOUT = "layout"
    ACCESSIBILITY = "accessibility"


@dataclass
class Severity:
    """Severity level with label and weight for scoring.

    Attributes:
        level: The severity level enum value
        label: Human-readable label (e.g., "严重", "高")
        weight: Numeric weight for compliance score calculation
    """
    level: SeverityLevel
    label: str
    weight: int

    @classmethod
    def from_level(cls, level: SeverityLevel) -> "Severity":
        """Create Severity from level with predefined label and weight."""
        labels = {
            SeverityLevel.CRITICAL: {"zh": "严重", "en": "Critical"},
            SeverityLevel.HIGH: {"zh": "高", "en": "High"},
            SeverityLevel.MEDIUM: {"zh": "中", "en": "Medium"},
            SeverityLevel.LOW: {"zh": "低", "en": "Low"},
        }
        weights = {
            SeverityLevel.CRITICAL: 10,
            SeverityLevel.HIGH: 5,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 1,
        }
        label_data = labels[level]
        return cls(
            level=level,
            label=f"{label_data['zh']}/{label_data['en']}",
            weight=weights[level],
        )


@dataclass
class Finding:
    """A finding representing a violation or issue found during review.

    This is the canonical finding structure shared across all bounded contexts.
    Each finding is tagged with source_context to prevent cross-context pollution.

    Attributes:
        id: Unique identifier for the finding
        source_context: Which domain found this ("prd" or "prototype")
        dimension: Which review dimension (structure, terminology, etc.)
        severity: Severity level of the finding
        rule_id: ID of the violated rule in the knowledge base
        description: Human-readable description of the issue
        location: Where in the document/image the issue is
        suggestion: How to fix the issue
        evidence: Quote or reference from source material
        created_at: When the finding was created
    """
    source_context: str  # "prd" | "prototype"
    dimension: ReviewDimension
    severity: SeverityLevel
    rule_id: str
    description: str
    location: str
    suggestion: str
    evidence: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_context": self.source_context,
            "dimension": self.dimension.value,
            "severity": self.severity.name,
            "severity_label": Severity.from_level(self.severity).label,
            "rule_id": self.rule_id,
            "description": self.description,
            "location": self.location,
            "suggestion": self.suggestion,
            "evidence": self.evidence,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Finding":
        """Create Finding from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            source_context=data["source_context"],
            dimension=ReviewDimension(data["dimension"]),
            severity=SeverityLevel[data["severity"]],
            rule_id=data["rule_id"],
            description=data["description"],
            location=data["location"],
            suggestion=data["suggestion"],
            evidence=data.get("evidence", ""),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
        )
