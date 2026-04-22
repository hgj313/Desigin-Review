"""Shared kernel exports — entities and value objects visible across bounded contexts."""

from src_v2.domain.shared.entities import (
    Finding,
    ReviewContext,
    ReviewDimension,
    ReviewResult,
    SeverityLevel,
)
from src_v2.domain.shared.value_objects import ChunkId, DocumentId, StandardId

__all__ = [
    # entities
    "Finding",
    "ReviewContext",
    "ReviewDimension",
    "ReviewResult",
    "SeverityLevel",
    # value objects
    "ChunkId",
    "DocumentId",
    "StandardId",
]