"""Service interfaces (Protocols) for the Ingestion bounded context."""

from typing import Protocol

from src_v2.domain.ingestion.entities import Chunk, Document, DocumentContentType


class IChunkingService(Protocol):
    """Splits documents into retrievable chunks."""

    def chunk_document(self, doc: Document) -> list[Chunk]:
        """Split a document into chunks."""
        ...

    def detect_content_type(self, content: str) -> DocumentContentType:
        """Infer content type from text."""
        ...


class IEmbeddingService(Protocol):
    """Generates vector embeddings for text."""

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        ...

    def embed_documents(self, docs: list[Document]) -> list[list[float]]:
        """Generate embeddings for multiple documents in batch."""
        ...