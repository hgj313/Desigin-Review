"""Value objects providing type-safe identifiers across bounded contexts."""

from typing import NewType

__all__ = [
    "ChunkId",
    "DocumentId",
    "StandardId",
]

# NewType definitions for type safety — these are not plain str but have no behavior
StandardId = NewType("StandardId", str)
DocumentId = NewType("DocumentId", str)
ChunkId = NewType("ChunkId", str)