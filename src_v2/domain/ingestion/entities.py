"""Domain entities for the Ingestion bounded context."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from src_v2.domain.shared.value_objects import ChunkId, DocumentId, StandardId


class DocumentContentType(Enum):
    """Content classification for ingested documents."""

    SPACING = "spacing"
    COLOR = "color"
    TYPOGRAPHY = "typography"
    ACCESSIBILITY = "accessibility"
    GENERAL = "general"


@dataclass
class Document:
    """A design document that can be chunked and embedded."""

    id: DocumentId
    content: str
    content_type: DocumentContentType
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Chunk:
    """A chunk of a document, ready for embedding and retrieval."""

    id: ChunkId
    document_id: DocumentId
    content: str
    content_type: DocumentContentType
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list[float]] = None


@dataclass
class Standard:
    """A design standard against which documents can be reviewed."""

    id: StandardId
    content: str
    content_type: DocumentContentType
    category: str
    metadata: dict = field(default_factory=dict)
    relations: list[str] = field(default_factory=list)