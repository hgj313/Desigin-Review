"""LangGraph state definitions for workflow orchestration.

Defines TypedDict state schemas for document ingestion and knowledge base
query workflows per AGT-01 (LangGraph StateGraph with TypedDict).

References:
- AGT-01: Use TypedDict for LangGraph state, not arbitrary dicts
"""

from typing import TypedDict, Optional, Literal, List
from pydantic import BaseModel

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


class Finding(BaseModel):
    """Single review finding with location and severity per RPT-02, RPT-03, RPT-04.

    Attributes:
        issue_type: Type of issue (structure/terminology/completeness/formatting).
        severity: Severity level (Critical/Major/Minor/Suggestion).
        location: Line number, section name, or coordinates.
        description_en: English description of the finding.
        description_zh: Chinese description of the finding.
        suggestion_en: English improvement suggestion.
        suggestion_zh: Chinese improvement suggestion.
    """

    issue_type: str  # structure, terminology, completeness, formatting
    severity: Literal["Critical", "Major", "Minor", "Suggestion"]
    location: str  # line number, section name, or coordinates
    description_en: str
    description_zh: str
    suggestion_en: Optional[str] = None
    suggestion_zh: Optional[str] = None


class PRDReviewState(TypedDict):
    """State for PRD review workflow.

    Tracks parallel validation of PRD documents against design standards.

    Attributes:
        prd_text: Raw PRD document text.
        collection_name: Chroma collection name for knowledge base.
        review_depth: Validation thoroughness (fast/balanced/thorough).
        max_iterations: Maximum refinement iterations.
        review_iteration: Current iteration count.
        structure_findings: Findings from structure validation.
        terminology_findings: Findings from terminology validation.
        completeness_findings: Findings from completeness validation.
        formatting_findings: Findings from formatting validation.
        all_findings: Aggregated findings from all validators.
        refined_findings: Findings after iterative refinement.
        report: Generated compliance report.
        status: Current workflow status.
        error: Error message if status is error.
    """

    prd_text: str
    collection_name: str
    review_depth: Literal["fast", "balanced", "thorough"]
    max_iterations: int
    review_iteration: int
    structure_findings: List[Finding]
    terminology_findings: List[Finding]
    completeness_findings: List[Finding]
    formatting_findings: List[Finding]
    all_findings: List[Finding]
    refined_findings: Optional[List[Finding]] = None
    report: Optional[str] = None
    status: str
    error: Optional[str]


def get_initial_prd_review_state(
    prd_text: str,
    collection_name: str = "design_standards",
    review_depth: str = "balanced",
) -> PRDReviewState:
    """Create initial state for PRD review workflow.

    Args:
        prd_text: Raw PRD document text.
        collection_name: Chroma collection name (default: design_standards).
        review_depth: Validation thoroughness (default: balanced).
            - fast: max_iterations=1, retrieval_k=3
            - balanced: max_iterations=2, retrieval_k=5
            - thorough: max_iterations=3, retrieval_k=10

    Returns:
        PRDReviewState dict with initial values.
    """
    depth_config = {
        "fast": {"max_iterations": 1},
        "balanced": {"max_iterations": 2},
        "thorough": {"max_iterations": 3},
    }
    config = depth_config.get(review_depth, depth_config["balanced"])

    return PRDReviewState(
        prd_text=prd_text,
        collection_name=collection_name,
        review_depth=review_depth,
        max_iterations=config["max_iterations"],
        review_iteration=0,
        structure_findings=[],
        terminology_findings=[],
        completeness_findings=[],
        formatting_findings=[],
        all_findings=[],
        refined_findings=None,
        report=None,
        status="pending",
        error=None,
    )


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


def get_initial_image_review_state(
    prd_text: str,
    image_path: str,
    collection_name: str = "design_standards",
    review_depth: str = "balanced",
) -> "ImageReviewState":
    """Create initial state for image review workflow.

    Args:
        prd_text: Raw PRD document text.
        image_path: Path to prototype image file.
        collection_name: Chroma collection name (default: design_standards).
        review_depth: Validation thoroughness (default: balanced).
            - fast: max_iterations=1
            - balanced: max_iterations=2
            - thorough: max_iterations=3

    Returns:
        ImageReviewState dict with initial values.
    """
    depth_config = {
        "fast": {"max_iterations": 1},
        "balanced": {"max_iterations": 2},
        "thorough": {"max_iterations": 3},
    }
    config = depth_config.get(review_depth, depth_config["balanced"])

    # Get initial PRD review state
    prd_state = get_initial_prd_review_state(
        prd_text=prd_text,
        collection_name=collection_name,
        review_depth=review_depth,
    )

    # Convert to ImageReviewState with image-specific fields
    return ImageReviewState(
        **prd_state,
        image_path=image_path,
        image_analysis=None,
        color_findings=[],
        typography_findings=[],
        spacing_findings=[],
        accessibility_findings=[],
        assumption_findings=[],
        design_tokens=[],
    )


class ImageReviewState(PRDReviewState):
    """State for image review workflow.

    Extends PRDReviewState with image-specific fields per D-19.

    Additional Attributes:
        image_path: Path to prototype image being reviewed.
        image_analysis: Cached analysis from MiniMax Vision API.
        color_findings: Findings from color palette validation (IMG-01, IMG-02).
        typography_findings: Findings from typography analysis (IMG-03).
        spacing_findings: Findings from spacing/grid validation (IMG-04).
        accessibility_findings: Findings from WCAG contrast check (IMG-05).
        assumption_findings: Findings from vague language detection (PRD-05).
        design_tokens: Retrieved brand/design token standards with version metadata.
    """

    image_path: str
    image_analysis: Optional[dict] = None
    color_findings: List["Finding"] = []
    typography_findings: List["Finding"] = []
    spacing_findings: List["Finding"] = []
    accessibility_findings: List["Finding"] = []
    assumption_findings: List["Finding"] = []
    design_tokens: List[dict] = []


__all__ = [
    "IngestionState",
    "QueryState",
    "ReviewState",
    "Finding",
    "PRDReviewState",
    "ImageReviewState",
    "get_initial_ingestion_state",
    "get_initial_query_state",
    "get_initial_prd_review_state",
    "get_initial_image_review_state",
]
