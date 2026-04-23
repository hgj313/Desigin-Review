"""Cross-reference validation using bge-m3 embeddings.

Per D-03: Semantic embedding matching for cross-reference validation
Per D-04: Fixed threshold 0.7 for similarity matching
Per D-05: "Standard Not Found" pattern when below threshold
"""

from __future__ import annotations

__all__ = ["CrossReferenceValidator"]

import re
import uuid
from datetime import datetime
from typing import Protocol

import numpy as np
from scipy.spatial.distance import cosine

from src_v2.domain.ingestion.entities import Document, Standard
from src_v2.domain.shared.entities import Finding, ReviewDimension, SeverityLevel


class IEmbeddingFn(Protocol):
    """Protocol for embedding function (bge-m3)."""

    def embed_query(self, text: str) -> np.ndarray:
        """Embed a single text query.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array
        """
        ...


class IRetriever(Protocol):
    """Protocol for retriever (HybridGraphRetriever)."""

    def retrieve(self, query: str, k: int = 5) -> list[tuple[Document, float]]:
        """Retrieve documents using hybrid search.

        Args:
            query: Query text
            k: Number of results to return

        Returns:
            List of (Document, score) tuples
        """
        ...


class CrossReferenceValidator:
    """Validates cross-references between user stories and design specifications.

    Uses bge-m3 embeddings for semantic similarity per D-03.
    Fixed threshold 0.7 for association per D-04.
    "Standard Not Found" pattern when below threshold per D-05.
    """

    def __init__(self, embedding_fn: IEmbeddingFn, retriever: IRetriever | None = None):
        """Initialize CrossReferenceValidator.

        Args:
            embedding_fn: bge-m3 embedding function for semantic matching
            retriever: Optional HybridGraphRetriever for graph-based retrieval
        """
        self._embedding_fn = embedding_fn
        self._retriever = retriever

    def validate_reference_similarity(
        self, story_text: str, standard_text: str
    ) -> tuple[float, bool]:
        """Calculate similarity between user story and design spec.

        Args:
            story_text: User story text
            standard_text: Design specification text

        Returns:
            Tuple of (similarity_score, is_associated)
            is_associated is True if similarity >= 0.7 per D-04
        """
        vec1 = self._embedding_fn.embed_query(story_text)
        vec2 = self._embedding_fn.embed_query(standard_text)

        # Cosine similarity: 1 - cosine distance
        similarity = 1 - cosine(vec1, vec2)
        is_associated = similarity >= 0.7

        return float(similarity), is_associated

    def validate_references(
        self, doc: Document, standards: list[Standard]
    ) -> list[Finding]:
        """Validate cross-references between user stories and design specs.

        For each user story in the document:
        - Retrieve related standards using HybridGraphRetriever
        - Calculate embedding similarity with each retrieved standard
        - If max_similarity >= 0.7: reference is valid (no Finding)
        - If max_similarity < 0.7: Create "Standard Not Found" Finding per D-05

        Args:
            doc: Document to validate
            standards: List of design standards to check against

        Returns:
            List of Finding objects for missing or invalid references
        """
        findings = []

        user_stories = self._extract_user_stories(doc.content)

        for story_text in user_stories:
            max_similarity = 0.0
            related_spec_id = None

            # If retriever is available, use it to find related standards
            if self._retriever:
                results = self._retriever.retrieve(story_text, k=5)
                for retrieved_doc, score in results:
                    similarity, _ = self.validate_reference_similarity(
                        story_text, retrieved_doc.content
                    )
                    if similarity > max_similarity:
                        max_similarity = similarity
                        related_spec_id = retrieved_doc.id

            # Also check against provided standards list
            for standard in standards:
                similarity, _ = self.validate_reference_similarity(
                    story_text, standard.content
                )
                if similarity > max_similarity:
                    max_similarity = similarity
                    related_spec_id = standard.id

            # Check threshold
            if max_similarity < 0.7:
                findings.append(
                    Finding(
                        id=str(uuid.uuid4()),
                        dimension=ReviewDimension.SEMANTIC,
                        severity=SeverityLevel.HIGH,
                        rule_id="prd-crossref-001",
                        description="User story may lack design specification",
                        location="document",
                        suggestion="Consider referencing design standard for this requirement",
                        evidence=f"Max similarity: {max_similarity:.2f} < 0.7",
                        created_at=datetime.now(),
                    )
                )

        return findings

    def _extract_user_stories(self, content: str) -> list[str]:
        """Extract user story text blocks from document content.

        Splits content by "## User Story" or "### User Story" headers.

        Args:
            content: Document content

        Returns:
            List of user story text blocks
        """
        # Split by User Story headers
        pattern = r"##\s*User\s*Story|###\s*User\s*Story"
        parts = re.split(pattern, content, flags=re.IGNORECASE)

        user_stories = []
        for part in parts[1:]:  # Skip content before first header
            # Get text until next header or end
            next_header = re.search(r"##\s*\w", part)
            if next_header:
                story_text = part[: next_header.start()].strip()
            else:
                story_text = part.strip()

            if story_text:
                user_stories.append(story_text)

        return user_stories