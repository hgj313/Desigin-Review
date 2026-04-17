"""LangGraph state definitions for workflow orchestration.

Defines TypedDict state schemas for document ingestion and knowledge base
query workflows per AGT-01 (LangGraph StateGraph with TypedDict).

References:
- AGT-01: Use TypedDict for LangGraph state, not arbitrary dicts
"""

from typing import TypedDict, Optional

from langchain_core.documents import Document


class IngestionState(TypedDict):
    """State for document ingestion workflow.

    Tracks the pipeline from document loading through vector storage.

    Attributes:
        file_path: Path to document being ingested.
        document_metadata: Metadata dict with document_name, version_id, effective_date.
        document_text: Raw document text after loading.
        chunks: Chunked documents from structural splitter.
        embeddings: Generated embedding vectors (1024-dimensional).
        collection_name: Target Chroma collection name.
        status: Current status: pending, loaded, chunked, embedded, stored, error.
        error: Error message if status is error.
    """

    file_path: str
    document_metadata: dict
    document_text: str
    chunks: list[Document]
    embeddings: list[list[float]]
    collection_name: str
    status: str
    error: Optional[str]


class QueryState(TypedDict):
    """State for knowledge base query workflow.

    Tracks query execution and response generation.

    Attributes:
        query: User's natural language query.
        results: Retrieved documents with similarity scores as (Document, float) tuples.
        response: Formatted response to user (Chinese + English).
        standard_found: Whether relevant standard was found (confidence >= threshold).
        confidence: Confidence score of top result (0.0 to 1.0).
        threshold: Minimum confidence threshold for standard_found (default 0.7).
        collection_name: Collection to query.
    """

    query: str
    results: list[tuple[Document, float]]
    response: str
    standard_found: bool
    confidence: float
    threshold: float
    collection_name: str


class ReviewState(TypedDict):
    """Base state for review workflows (extended in later phases).

    Provides common fields for all review workflow types.
    Later phases will extend this with review-specific fields.

    Attributes:
        status: Current workflow status.
        error: Error message if status is error.
    """

    status: str
    error: Optional[str]


def get_initial_ingestion_state(
    file_path: str,
    metadata: dict,
    collection_name: str = "design_standards",
) -> IngestionState:
    """Create initial state for document ingestion workflow.

    Args:
        file_path: Path to document being ingested.
        metadata: Metadata dict with document_name, version_id, effective_date.
        collection_name: Target Chroma collection name (default: design_standards).

    Returns:
        IngestionState dict with initial values.
    """
    return IngestionState(
        file_path=file_path,
        document_metadata=metadata,
        document_text="",
        chunks=[],
        embeddings=[],
        collection_name=collection_name,
        status="pending",
        error=None,
    )


def get_initial_query_state(
    query: str,
    threshold: float = 0.7,
    collection_name: str = "design_standards",
) -> QueryState:
    """Create initial state for knowledge base query workflow.

    Args:
        query: User's natural language query.
        threshold: Minimum confidence threshold (default: 0.7).
        collection_name: Collection to query (default: design_standards).

    Returns:
        QueryState dict with initial values.
    """
    return QueryState(
        query=query,
        results=[],
        response="",
        standard_found=False,
        confidence=0.0,
        threshold=threshold,
        collection_name=collection_name,
    )


__all__ = [
    "IngestionState",
    "QueryState",
    "ReviewState",
    "get_initial_ingestion_state",
    "get_initial_query_state",
]
