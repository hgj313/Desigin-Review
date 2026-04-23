# src_v2/infrastructure/vectorstore/chroma_store.py
"""ChromaDB-backed vector store implementation."""

import logging
from typing import Optional

import chromadb
from chromadb.config import Settings
from langchain_core.documents import Document

from src_v2.domain.ingestion.entities import Chunk, DocumentContentType
from src_v2.domain.ingestion.repositories import IChunkRepository
from src_v2.domain.shared.value_objects import ChunkId, DocumentId

logger = logging.getLogger(__name__)


class ChromaStore(IChunkRepository):
    """ChromaDB implementation of IChunkRepository.

    Stores chunks with embeddings and supports similarity search.
    Collection persists to disk at chroma_db/ directory.
    """

    def __init__(
        self,
        collection_name: str = "design_standards",
        persist_directory: str = "chroma_db",
    ):
        """Initialize ChromaDB client and collection.

        Args:
            collection_name: Name of the collection to use.
            persist_directory: Directory for persistent storage.
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(f"ChromaStore initialized: collection={collection_name}")

    def store_chunk(self, chunk: Chunk) -> None:
        """Persist a chunk with its embedding vector.

        Args:
            chunk: Chunk entity with embedding pre-computed.
        """
        if chunk.embedding is None:
            raise ValueError(f"Chunk {chunk.id} has no embedding")

        doc = Document(
            page_content=chunk.content,
            metadata={
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "content_type": chunk.content_type.value,
                "standard_id": chunk.metadata.get("standard_id", ""),
            },
        )

        self._collection.upsert(
            ids=[str(chunk.id)],
            embeddings=[chunk.embedding],
            documents=[doc.page_content],
            metadatas=[doc.metadata],
        )

        logger.debug(f"Stored chunk {chunk.id}")

    def similarity_search(
        self, embedding: list[float], k: int = 5
    ) -> list[tuple[Document, float]]:
        """Find chunks most similar to a query embedding.

        Args:
            embedding: Query embedding vector.
            k: Number of results to return.

        Returns:
            List of (Document, score) tuples sorted by similarity.
        """
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=k,
        )

        documents = []
        for i in range(len(results["ids"][0])):
            doc = Document(
                page_content=results["documents"][0][i],
                metadata=results["metadatas"][0][i] or {},
            )
            distance = results["distances"][0][i]
            # Convert cosine distance to similarity score
            score = 1.0 - distance
            documents.append((doc, score))

        return documents

    def find_by_document_id(self, doc_id: DocumentId) -> list[Chunk]:
        """Retrieve all chunks belonging to a document.

        Args:
            doc_id: Document identifier.

        Returns:
            List of Chunk entities.
        """
        results = self._collection.get(
            where={"document_id": str(doc_id)},
        )

        chunks = []
        for i in range(len(results["ids"])):
            chunk = Chunk(
                id=ChunkId(results["ids"][i]),
                document_id=DocumentId(results["metadatas"][i]["document_id"]),
                content=results["documents"][i],
                content_type=DocumentContentType(results["metadatas"][i]["content_type"]),
                metadata={"standard_id": results["metadatas"][i].get("standard_id", "")},
            )
            chunks.append(chunk)

        return chunks

    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        """Retrieve a document by its chunk ID.

        Args:
            doc_id: Document/chunk identifier.

        Returns:
            Document if found, None otherwise.
        """
        results = self._collection.get(ids=[doc_id])

        if not results["ids"]:
            return None

        return Document(
            page_content=results["documents"][0],
            metadata=results["metadatas"][0] or {},
        )

    def delete_collection(self) -> None:
        """Delete the collection and all its data."""
        self._client.delete_collection(self.collection_name)
        logger.info(f"Deleted collection {self.collection_name}")