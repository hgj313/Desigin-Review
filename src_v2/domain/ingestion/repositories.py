"""Repository interfaces (Protocols) for the Ingestion bounded context."""

from typing import Protocol

from src_v2.domain.ingestion.entities import Chunk, Document, Standard
from src_v2.domain.shared.value_objects import ChunkId, DocumentId, StandardId
from src_v2.domain.ingestion.entities import DocumentContentType


class IDocumentRepository(Protocol):
    """Stores and retrieves documents."""

    def store(self, document: Document) -> None:
        """Persist a document."""
        ...

    def find_by_id(self, id: DocumentId) -> Document | None:
        """Retrieve a document by ID."""
        ...

    def find_all(self) -> list[Document]:
        """Retrieve all documents."""
        ...


class IChunkRepository(Protocol):
    """Stores and retrieves document chunks with embeddings."""

    def store_chunk(self, chunk: Chunk, embedding: list[float]) -> None:
        """Persist a chunk with its embedding vector."""
        ...

    def find_similar(self, embedding: list[float], k: int) -> list[tuple[Chunk, float]]:
        """Find chunks most similar to a query embedding."""
        ...

    def find_by_document_id(self, doc_id: DocumentId) -> list[Chunk]:
        """Retrieve all chunks belonging to a document."""
        ...


class IStandardRepository(Protocol):
    """Stores and retrieves design standards."""

    def store_standard(self, standard: Standard) -> None:
        """Persist a design standard."""
        ...

    def find_by_id(self, id: StandardId) -> Standard | None:
        """Retrieve a standard by ID."""
        ...

    def find_by_content_type(self, content_type: DocumentContentType) -> list[Standard]:
        """Retrieve all standards of a given content type."""
        ...

    def find_related(self, standard_id: StandardId, depth: int) -> list[StandardId]:
        """Traverse standard relations up to a given depth."""
        ...