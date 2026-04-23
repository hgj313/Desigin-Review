# src_v2/infrastructure/ingestion/chunk_repository_impl.py
"""ChromaStore-backed implementation of IChunkRepository."""

from typing import Optional

from src_v2.domain.ingestion.entities import Chunk
from src_v2.domain.ingestion.repositories import IChunkRepository
from src_v2.domain.ingestion.services import IEmbeddingService
from src_v2.domain.shared.value_objects import ChunkId, DocumentId
from src_v2.infrastructure.vectorstore.chroma_store import ChromaStore


class ChunkRepositoryImpl(IChunkRepository):
    """IChunkRepository implementation using ChromaStore + EmbeddingService.

    Automatically computes embeddings for chunks on store.
    """

    def __init__(
        self,
        vector_store: ChromaStore,
        embedding_service: IEmbeddingService,
    ):
        """Initialize with vector store and embedding service.

        Args:
            vector_store: ChromaStore instance for storage.
            embedding_service: Service for computing embeddings.
        """
        self._vector_store = vector_store
        self._embedding_service = embedding_service

    def store_chunk(self, chunk: Chunk) -> None:
        """Persist a chunk with auto-computed embedding.

        Args:
            chunk: Chunk entity (embedding will be computed if missing).
        """
        if chunk.embedding is None:
            chunk.embedding = self._embedding_service.embed_text(chunk.content)

        self._vector_store.store_chunk(chunk)

    def find_similar(
        self, embedding: list[float], k: int
    ) -> list[tuple[Chunk, float]]:
        """Find chunks most similar to a query embedding.

        Args:
            embedding: Query embedding vector.
            k: Number of results to return.

        Returns:
            List of (Chunk, similarity_score) tuples.
        """
        return self._vector_store.similarity_search(embedding, k)

    def find_by_document_id(self, doc_id: DocumentId) -> list[Chunk]:
        """Retrieve all chunks belonging to a document."""
        return self._vector_store.find_by_document_id(doc_id)