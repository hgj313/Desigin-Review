"""Hybrid vector + BM25 + graph traversal retrieval.

This module provides the HybridGraphRetriever class that combines:
- Vector similarity search (ChromaStore)
- BM25 keyword search (rank_bm25)
- Graph traversal expansion (StandardKnowledgeGraph)

The combined score uses weighted combination per must_haves:
- alpha (0.4): vector weight
- beta (0.3): BM25 weight
- gamma (0.3): graph weight

References:
- RAG-05: System supports hybrid retrieval (BM25 + vector) for precision
"""

import logging
from typing import List, Tuple, Optional

import numpy as np
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from rank_bm25 import BM25Okapi

from src_v2.infrastructure.kg.knowledge_graph import StandardKnowledgeGraph

logger = logging.getLogger(__name__)


class HybridGraphRetriever:
    """Hybrid BM25 + vector + graph traversal retrieval per RAG-05.

    Combines three retrieval strategies:
    1. Vector similarity (semantic understanding via embeddings)
    2. BM25 keyword matching (exact term matching)
    3. Graph traversal expansion (related standards via relations)

    Alpha/beta/gamma weights control the balance. Default values
    (0.4/0.3/0.3) were chosen as starting points per research.

    Attributes:
        vector_store: ChromaStore instance for vector similarity search.
        embedding_fn: LangChain Embeddings instance for query embedding.
        knowledge_graph: StandardKnowledgeGraph for relation traversal.
        texts: List of document texts for BM25 indexing.
        alpha: Weight for vector scores (default 0.4).
        beta: Weight for BM25 scores (default 0.3).
        gamma: Weight for graph scores (default 0.3).
    """

    def __init__(
        self,
        vector_store,
        embedding_fn: Embeddings,
        knowledge_graph: StandardKnowledgeGraph,
        texts: List[str],
        alpha: float = 0.4,
        beta: float = 0.3,
        gamma: float = 0.3,
    ):
        """Initialize hybrid graph retriever.

        Args:
            vector_store: ChromaStore instance for vector similarity search.
            embedding_fn: LangChain Embeddings instance for query embedding.
            knowledge_graph: StandardKnowledgeGraph for relation traversal.
            texts: List of document texts for BM25 indexing.
            alpha: Weight for vector scores (default 0.4).
            beta: Weight for BM25 scores (default 0.3).
            gamma: Weight for graph scores (default 0.3).
        """
        self.vector_store = vector_store
        self.embedding_fn = embedding_fn
        self.knowledge_graph = knowledge_graph
        self.texts = texts
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        # Initialize BM25 with tokenized texts
        tokenized_texts = self._tokenize(texts)
        self.bm25 = BM25Okapi(tokenized_texts)

        # Pre-encode all texts for faster vector search
        self.text_embeddings = embedding_fn.embed_documents(texts)

        logger.info(
            f"HybridGraphRetriever initialized: {len(texts)} texts, "
            f"alpha={alpha}, beta={beta}, gamma={gamma}"
        )

    def _tokenize(self, texts: List[str]) -> List[List[str]]:
        """Tokenize texts for BM25 indexing.

        Simple whitespace + lowercase tokenization matching the
        existing HybridRetriever approach.

        Args:
            texts: List of text strings to tokenize.

        Returns:
            List of token lists (lowercase, whitespace-split).
        """
        return [[word.lower() for word in text.split()] for text in texts]

    def _get_bm25_scores(self, query: str) -> dict[str, float]:
        """Calculate normalized BM25 scores for all documents.

        Args:
            query: Query string.

        Returns:
            Dict mapping standard_id to normalized BM25 score (0-1 range).
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

        # Build dict with standard_id keys (using index as fallback)
        result = {}
        for idx, score in enumerate(normalized_scores):
            # Use metadata standard_id if available, otherwise use index
            # The index corresponds to document order in texts list
            result[str(idx)] = float(score)

        return result

    def _get_vector_scores(
        self, query_embedding: List[float], k: int
    ) -> dict[str, float]:
        """Calculate vector similarity scores via ChromaStore.

        Args:
            query_embedding: Query embedding vector.
            k: Number of top results to retrieve.

        Returns:
            Dict mapping standard_id to vector similarity score.
        """
        # Get more results initially for better coverage
        vector_results = self.vector_store.similarity_search(
            query_embedding, k=k * 2
        )

        # Build dict with standard_id keys
        result = {}
        for doc, score in vector_results:
            # Extract standard_id from metadata if available
            standard_id = doc.metadata.get("standard_id", None)
            if standard_id is None:
                # Fallback: use index from metadata if available
                standard_id = doc.metadata.get("original_index", None)
            if standard_id is not None:
                result[str(standard_id)] = score

        return result

    def _compute_graph_expansion(
        self, vector_results: List[Tuple[Document, float]]
    ) -> dict[str, float]:
        """Compute graph-based scores via relation traversal.

        For each standard in the top k*2 vector results, fetches
        related standards from the knowledge graph and assigns
        boosted scores based on relation distance.

        Args:
            vector_results: List of (Document, score) tuples from vector search.

        Returns:
            Dict mapping standard_id to graph-based score.
        """
        graph_scores = {}

        for doc, _score in vector_results:
            # Extract standard_id from metadata
            standard_id = doc.metadata.get("standard_id", None)
            if standard_id is None:
                continue

            # Get related IDs from knowledge graph (depth 2 for broader context)
            related_ids = self.knowledge_graph.get_related_ids(standard_id, max_depth=2)

            # Assign scores based on distance
            # Direct relations (depth=1): score = 1.0
            # Relations of relations (depth=2): score = 0.5
            for idx, related_id in enumerate(related_ids):
                # Determine depth based on index position
                # In BFS traversal, first batch is depth=1, second is depth=2
                # We approximate by checking position relative to k*2
                if len(related_ids) > 0:
                    # Simple heuristic: first half is direct, second half is indirect
                    mid = len(related_ids) // 2
                    if idx < mid:
                        depth_score = 1.0
                    else:
                        depth_score = 0.5

                graph_scores[str(related_id)] = graph_scores.get(
                    str(related_id), 0.0
                ) + depth_score

        # Normalize graph scores to 0-1 range
        if graph_scores:
            max_score = max(graph_scores.values())
            if max_score > 0:
                graph_scores = {
                    k: v / max_score for k, v in graph_scores.items()
                }

        return graph_scores

    def retrieve(
        self, query: str, k: int = 5
    ) -> List[Tuple[Document, float]]:
        """Retrieve using hybrid BM25 + vector + graph traversal.

        Combines three retrieval strategies with weighted scoring:
        1. Vector similarity from ChromaStore
        2. BM25 keyword scores
        3. Graph expansion scores from StandardKnowledgeGraph

        Args:
            query: Query string.
            k: Number of results to return (default: 5).

        Returns:
            List of (Document, combined_score) tuples sorted by score descending.
        """
        # Step 1: Get query embedding
        query_embedding = self.embedding_fn.embed_query(query)

        # Step 2: Vector search (get k*2 for better coverage)
        vector_results = self.vector_store.similarity_search(
            query_embedding, k=k * 2
        )

        # Step 3: BM25 scores
        bm25_scores = self._get_bm25_scores(query)

        # Step 4: Graph expansion
        graph_scores = self._compute_graph_expansion(vector_results)

        # Step 5: Build combined scores
        # Collect all standard_ids
        all_ids: set[str] = set()
        for doc, _score in vector_results:
            sid = doc.metadata.get("standard_id")
            if sid:
                all_ids.add(str(sid))
            else:
                sid = doc.metadata.get("original_index")
                if sid is not None:
                    all_ids.add(str(sid))
        all_ids.update(bm25_scores.keys())
        all_ids.update(graph_scores.keys())

        # Compute combined scores
        combined_scores = {}
        for sid in all_ids:
            vec_score = 0.0
            for doc, _score in vector_results:
                doc_sid = doc.metadata.get("standard_id")
                if doc_sid is None:
                    doc_sid = doc.metadata.get("original_index")
                if doc_sid is not None and str(doc_sid) == sid:
                    vec_score = _score
                    break
            bm25_score = bm25_scores.get(sid, 0.0)
            graph_score = graph_scores.get(sid, 0.0)

            combined = (
                self.alpha * vec_score
                + self.beta * bm25_score
                + self.gamma * graph_score
            )
            combined_scores[sid] = combined

        # Step 6: Sort and return top k results
        sorted_ids = sorted(
            combined_scores.items(), key=lambda x: x[1], reverse=True
        )[:k]

        # Build result list by looking up documents
        results = []
        for sid, score in sorted_ids:
            # Try to find the document
            doc = None
            for d, _ in vector_results:
                d_sid = d.metadata.get("standard_id")
                if d_sid is None:
                    d_sid = d.metadata.get("original_index")
                if d_sid is not None and str(d_sid) == sid:
                    doc = d
                    break

            if doc is None:
                # Fallback: try to get from vector store by ID
                doc_id = f"chunk_{self.vector_store.collection_name}_{sid}"
                doc = self.vector_store.get_document_by_id(doc_id)

            if doc is not None:
                results.append((doc, score))

        return results


__all__ = ["HybridGraphRetriever"]
