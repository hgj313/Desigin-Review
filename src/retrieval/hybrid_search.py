"""Hybrid BM25 + vector retrieval for precision.

This module provides the HybridRetriever class that combines keyword
matching (BM25) with semantic similarity (vector) per RAG-05.

References:
- RAG-05: System supports hybrid retrieval (BM25 + vector) for precision
"""

import logging
from typing import List, Tuple, Optional

import numpy as np
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from rank_bm25 import BM25Okapi


logger = logging.getLogger(__name__)


class HybridRetriever:
    """Hybrid BM25 + vector retrieval per RAG-05.

    Combines keyword matching (BM25) with semantic similarity (vector).
    Alpha controls balance: alpha=0.5 means equal weight.
    alpha=0.7 favors vector, alpha=0.3 favors BM25.

    Attributes:
        texts: List of document texts for BM25 indexing.
        embedding_fn: LangChain Embeddings instance for query embedding.
        collection: Chroma collection for vector search.
        alpha: Weight for vector scores (default 0.5, equal weight).
    """

    def __init__(
        self,
        texts: List[str],
        embedding_fn: Embeddings,
        collection,
        alpha: float = 0.5,
    ):
        """Initialize hybrid retriever.

        Args:
            texts: List of document texts for BM25 indexing.
            embedding_fn: LangChain Embeddings instance for query embedding.
            collection: Chroma collection for vector search.
            alpha: Weight for vector scores (0.5 = equal weight, default).
        """
        self.texts = texts
        self.embedding_fn = embedding_fn
        self.collection = collection
        self.alpha = alpha

        # Initialize BM25 with tokenized texts
        tokenized_texts = self._tokenize(texts)
        self.bm25 = BM25Okapi(tokenized_texts)

        # Pre-encode all texts for faster vector search
        self.text_embeddings = embedding_fn.embed_documents(texts)

        logger.info(
            f"HybridRetriever initialized: {len(texts)} texts, alpha={alpha}"
        )

    def _tokenize(self, texts: List[str]) -> List[List[str]]:
        """Tokenize texts for BM25 indexing.

        Simple whitespace + lowercase tokenization.

        Args:
            texts: List of text strings to tokenize.

        Returns:
            List of token lists (lowercase, whitespace-split).
        """
        return [[word.lower() for word in text.split()] for text in texts]

    def _get_bm25_scores(self, query: str) -> np.ndarray:
        """Calculate normalized BM25 scores for all documents.

        Args:
            query: Query string.

        Returns:
            Normalized BM25 scores (0-1 range) as numpy array.
        """
        # Tokenize query
        tokenized_query = [word.lower() for word in query.split()]

        # Get raw BM25 scores
        scores = self.bm25.get_scores(tokenized_query)

        # Normalize to 0-1 range using max normalization
        max_score = np.max(scores)
        if max_score > 0:
            normalized_scores = scores / max_score
        else:
            normalized_scores = scores

        return normalized_scores

    def _get_vector_scores(self, query_embedding: List[float]) -> np.ndarray:
        """Calculate cosine similarity between query and all document embeddings.

        Args:
            query_embedding: Query embedding vector.

        Returns:
            Cosine similarity scores as numpy array.
        """
        # Calculate cosine similarity
        # query_embedding: (embedding_dim,)
        # text_embeddings: (num_docs, embedding_dim)
        query_vec = np.array(query_embedding).reshape(1, -1)
        doc_vecs = np.array(self.text_embeddings)

        # Cosine similarity = dot product of normalized vectors
        # Since bge-m3 normalizes embeddings, simple dot product works
        similarities = np.dot(doc_vecs, query_vec.T).flatten()

        return similarities

    def search(
        self, query: str, k: int = 5
    ) -> List[Tuple[Document, float]]:
        """Search using hybrid BM25 + vector retrieval.

        Combines BM25 keyword scores with vector similarity scores
        using the configured alpha weight.

        Args:
            query: Query string.
            k: Number of results to return (default: 5).

        Returns:
            List of (Document, combined_score) tuples sorted by score descending.
        """
        # Get BM25 scores
        bm25_scores = self._get_bm25_scores(query)

        # Get query embedding
        query_embedding = self.embedding_fn.embed_query(query)

        # Get vector scores
        vector_scores = self._get_vector_scores(query_embedding)

        # Combine scores: alpha * vector + (1 - alpha) * bm25
        combined_scores = self.alpha * vector_scores + (1 - self.alpha) * bm25_scores

        # Get top-k indices
        top_k_indices = np.argsort(combined_scores)[-k:][::-1]

        # Fetch documents from collection and build result list
        results = []
        for idx in top_k_indices:
            # Generate the document ID (same as in ChromaStore.add_documents)
            doc_id = f"chunk_{self.collection.name}_{idx}"

            # Fetch from collection
            doc_results = self.collection.get(ids=[doc_id])

            if doc_results["documents"]:
                doc = Document(
                    page_content=doc_results["documents"][0],
                    metadata=doc_results["metadatas"][0]
                    if doc_results.get("metadatas")
                    else {},
                )
                results.append((doc, float(combined_scores[idx])))

        return results

    def search_with_filter(
        self,
        query: str,
        k: int = 5,
        filter: Optional[dict] = None,
    ) -> List[Tuple[Document, float]]:
        """Search with metadata filter (vector portion only).

        Note: BM25 cannot be filtered, only the vector portion respects
        the metadata filter.

        Args:
            query: Query string.
            k: Number of results to return (default: 5).
            filter: Optional Chroma where filter dictionary.

        Returns:
            List of (Document, combined_score) tuples sorted by score descending.
        """
        # Get BM25 scores (cannot be filtered)
        bm25_scores = self._get_bm25_scores(query)

        # Get query embedding
        query_embedding = self.embedding_fn.embed_query(query)

        # Vector search with filter
        vector_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter,
            include=["documents", "metadatas", "distances"],
        )

        # Build result list with combined scores
        results = []
        if vector_results["documents"] and len(vector_results["documents"]) > 0:
            for i, (doc_text, metadata, distance) in enumerate(
                zip(
                    vector_results["documents"][0],
                    vector_results["metadatas"][0],
                    vector_results["distances"][0],
                )
            ):
                # Get vector score
                vector_score = 1 / (1 + distance)

                # We need to find the BM25 score for this document
                # Extract original index from metadata if available
                original_idx = metadata.get("original_index", i)

                # Calculate combined score
                bm25_score = (
                    bm25_scores[original_idx] if original_idx < len(bm25_scores) else 0
                )
                combined_score = self.alpha * vector_score + (1 - self.alpha) * bm25_score

                doc = Document(page_content=doc_text, metadata=metadata)
                results.append((doc, float(combined_score)))

        # Sort by combined score
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:k]


def create_hybrid_retriever(
    collection,
    embedding_fn: Embeddings,
    alpha: float = 0.5,
) -> HybridRetriever:
    """Create HybridRetriever from a Chroma collection.

    Fetches all documents from the collection and initializes
    the hybrid retriever with pre-computed embeddings.

    Args:
        collection: Chroma collection.
        embedding_fn: LangChain Embeddings instance.
        alpha: Weight for vector scores (default 0.5, equal weight).

    Returns:
        Configured HybridRetriever instance.
    """
    # Fetch all documents from collection
    all_docs = collection.get()

    if not all_docs["documents"]:
        raise ValueError("Collection is empty - no documents to index")

    # Extract texts and preserve index for later retrieval
    texts = []
    for i, doc_text in enumerate(all_docs["documents"]):
        texts.append(doc_text)

    # Create hybrid retriever
    retriever = HybridRetriever(
        texts=texts,
        embedding_fn=embedding_fn,
        collection=collection,
        alpha=alpha,
    )

    logger.info(
        f"Created HybridRetriever from collection with {len(texts)} documents"
    )

    return retriever


__all__ = ["HybridRetriever", "create_hybrid_retriever"]
