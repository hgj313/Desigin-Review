"""Chroma vector store with metadata for source attribution.

This module provides the ChromaStore class for managing Chroma collections
with full metadata support for source attribution (RAG-06).

References:
- RAG-04: User can query knowledge base with natural language
- RAG-06: Retrieved standards include source attribution
"""

import logging
from typing import Optional

import chromadb
from chromadb.config import Settings
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


# Required metadata fields per RAG-06
REQUIRED_METADATA_FIELDS = [
    "document_name",
    "section",
    "version_id",
    "effective_date",
]

logger = logging.getLogger(__name__)


class ChromaStore:
    """Chroma vector store with metadata for source attribution.

    Provides persistent Chroma collection management with validation
    of required metadata fields for source attribution.

    Attributes:
        collection_name: Name of the Chroma collection.
        persist_directory: Directory for persistent storage.
        embedding_fn: LangChain Embeddings instance for query embedding.
    """

    def __init__(
        self,
        collection_name: str = "design_standards",
        persist_directory: str = "./chroma_db",
        embedding_fn: Optional[Embeddings] = None,
    ):
        """Initialize Chroma client and collection.

        Args:
            collection_name: Name of the collection (default: "design_standards").
            persist_directory: Directory for persistent Chroma storage.
            embedding_fn: Optional LangChain Embeddings instance for query embedding.
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_fn = embedding_fn

        # Create PersistentClient
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create collection with metadata
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Design standards knowledge base"},
        )

        logger.info(
            f"ChromaStore initialized: collection={collection_name}, "
            f"persist_directory={persist_directory}, "
            f"count={self.collection.count()}"
        )

    def add_documents(
        self, documents: list[Document], embeddings: list[list[float]]
    ) -> None:
        """Add documents with embeddings to collection.

        Validates that each document has required metadata fields:
        - document_name: Name of the source document
        - section: Section/subsection within document
        - version_id: Document version (e.g., "1.0", "2.1")
        - effective_date: When this version became effective

        Args:
            documents: List of LangChain Documents to add.
            embeddings: List of embedding vectors (1024-dimensional).

        Raises:
            ValueError: If document count doesn't match embedding count.
            ValueError: If any document is missing required metadata fields.
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Document count ({len(documents)}) must match "
                f"embedding count ({len(embeddings)})"
            )

        # Validate metadata for each document
        for i, doc in enumerate(documents):
            missing_fields = [
                field
                for field in REQUIRED_METADATA_FIELDS
                if field not in doc.metadata
            ]
            if missing_fields:
                raise ValueError(
                    f"Document {i} missing required metadata fields: {missing_fields}"
                )

        # Generate IDs for documents
        ids = [f"chunk_{self.collection_name}_{i}" for i in range(len(documents))]

        # Extract metadata
        metadatas = [doc.metadata for doc in documents]

        # Extract document contents
        texts = [doc.page_content for doc in documents]

        # Add to collection
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        logger.info(f"Added {len(documents)} documents to collection {self.collection_name}")

    def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter: Optional[dict] = None,
    ) -> list[tuple[Document, float]]:
        """Search for similar documents.

        Args:
            query_embedding: Query embedding vector (1024-dimensional).
            k: Number of results to return (default: 5).
            filter: Optional Chroma where filter dictionary.

        Returns:
            List of (Document, score) tuples sorted by similarity score descending.
            Score is calculated as 1 / (1 + distance) for cosine similarity.
        """
        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter,
            include=["documents", "metadatas", "distances"],
        )

        # Convert to Document objects with scores
        documents_with_scores = []
        if results["documents"] and len(results["documents"]) > 0:
            for doc_text, metadata, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                # Convert distance to similarity score (1 / (1 + distance))
                # Chroma uses cosine distance, so lower is better
                score = 1 / (1 + distance)

                doc = Document(page_content=doc_text, metadata=metadata)
                documents_with_scores.append((doc, score))

        return documents_with_scores

    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        """Get a document by its ID.

        Args:
            doc_id: Document ID (e.g., "chunk_design_standards_0").

        Returns:
            Document object if found, None otherwise.
        """
        results = self.collection.get(ids=[doc_id])

        if results["documents"] and len(results["documents"]) > 0:
            return Document(
                page_content=results["documents"][0],
                metadata=results["metadatas"][0] if results["metadatas"] else {},
            )

        return None

    def delete_collection(self) -> None:
        """Delete the collection from the database."""
        self.client.delete_collection(name=self.collection_name)
        logger.info(f"Deleted collection {self.collection_name}")

    def get_collection_stats(self) -> dict:
        """Return collection statistics.

        Returns:
            Dictionary with collection name, document count, and persist directory.
        """
        return {
            "name": self.collection_name,
            "count": self.collection.count(),
            "persist_directory": self.persist_directory,
        }


def create_chroma_store(
    collection_name: str = "design_standards",
    persist_directory: str = "./chroma_db",
    embedding_fn: Optional[Embeddings] = None,
) -> ChromaStore:
    """Convenience constructor for ChromaStore.

    Args:
        collection_name: Name of the collection (default: "design_standards").
        persist_directory: Directory for persistent Chroma storage.
        embedding_fn: Optional LangChain Embeddings instance for query embedding.

    Returns:
        Configured ChromaStore instance.
    """
    return ChromaStore(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_fn=embedding_fn,
    )


__all__ = ["ChromaStore", "create_chroma_store"]
