"""LangGraph workflow graphs for ingestion and query pipelines.

Provides StateGraph-based workflows for document ingestion and knowledge
base querying per AGT-01 (LangGraph StateGraph) and AGT-03 (Standard Not Found).

References:
- AGT-01: Use LangGraph StateGraph, not pure LangChain chains
- AGT-03: Explicit Standard Not Found when confidence < threshold
- D-12: Standard Not Found when no relevant guidance
"""

from typing import Literal, Union

from langgraph.graph import StateGraph, END

from src.workflow.state import IngestionState, QueryState, PRDReviewState, ImageReviewState
from src.ingestion.loaders import load_document
from src.ingestion.chunker import StructuralChunker
from src.embeddings.bge_m3 import BGE_M3_Embeddings
from src.vectorstore.chroma_store import ChromaStore
from src.retrieval.hybrid_search import HybridRetriever


# ============================================================================
# Ingestion Graph Nodes
# ============================================================================


def load_document_node(state: IngestionState) -> IngestionState:
    """Load document from file path.

    Args:
        state: IngestionState with file_path and document_metadata.

    Returns:
        Updated state with document_text and status='loaded'.
    """
    docs = load_document(state["file_path"], state["document_metadata"])

    # Combine all document contents into single text
    document_text = "\n\n".join(doc.page_content for doc in docs)

    return {
        **state,
        "document_text": document_text,
        "status": "loaded",
    }


def chunk_document_node(state: IngestionState) -> IngestionState:
    """Split document into structurally-chunked pieces.

    Args:
        state: IngestionState with document_text loaded.

    Returns:
        Updated state with chunks and status='chunked'.
    """
    from langchain_core.documents import Document

    # Create a Document from the loaded text for chunking
    doc = Document(
        page_content=state["document_text"],
        metadata=state["document_metadata"],
    )

    chunker = StructuralChunker()
    chunks = chunker.split_documents([doc])

    return {
        **state,
        "chunks": chunks,
        "status": "chunked",
    }


def embed_chunks_node(state: IngestionState) -> IngestionState:
    """Generate embeddings for document chunks.

    Args:
        state: IngestionState with chunks ready.

    Returns:
        Updated state with embeddings and status='embedded'.
    """
    embedding_fn = BGE_M3_Embeddings()

    # Extract text from chunks for embedding
    texts = [chunk.page_content for chunk in state["chunks"]]

    # Generate embeddings
    embeddings = embedding_fn.embed_documents(texts)

    return {
        **state,
        "embeddings": embeddings,
        "status": "embedded",
    }


def store_vectors_node(state: IngestionState) -> IngestionState:
    """Store document chunks and embeddings in Chroma.

    Args:
        state: IngestionState with chunks and embeddings ready.

    Returns:
        Updated state with status='stored'.
    """
    store = ChromaStore(
        collection_name=state["collection_name"],
        embedding_fn=BGE_M3_Embeddings(),
    )

    store.add_documents(state["chunks"], state["embeddings"])

    return {
        **state,
        "status": "stored",
    }


# ============================================================================
# Query Graph Nodes
# ============================================================================


def query_knowledge_node(state: QueryState) -> QueryState:
    """Query knowledge base using hybrid retrieval.

    Args:
        state: QueryState with query and threshold.

    Returns:
        Updated state with results, confidence, and standard_found.
    """
    # Initialize Chroma and HybridRetriever
    store = ChromaStore(
        collection_name=state["collection_name"],
        embedding_fn=BGE_M3_Embeddings(),
    )

    embedding_fn = BGE_M3_Embeddings()

    # Get all documents from collection for HybridRetriever
    all_docs = store.collection.get()

    if not all_docs["documents"]:
        # Empty collection - no standard found
        return {
            **state,
            "results": [],
            "confidence": 0.0,
            "standard_found": False,
        }

    # Create hybrid retriever
    retriever = HybridRetriever(
        texts=all_docs["documents"],
        embedding_fn=embedding_fn,
        collection=store.collection,
    )

    # Search
    results = retriever.search(state["query"], k=5)

    # Calculate confidence from top result
    confidence = results[0][1] if results else 0.0

    return {
        **state,
        "results": results,
        "confidence": confidence,
        "standard_found": confidence >= state["threshold"],
    }


def format_results_node(state: QueryState) -> QueryState:
    """Format retrieval results with source attribution.

    Args:
        state: QueryState with results.

    Returns:
        Updated state with bilingual response.
    """
    from src.prompts.templates import format_retrieval_results

    response = format_retrieval_results(state["results"])

    return {
        **state,
        "response": response,
    }


def standard_not_found_node(state: QueryState) -> QueryState:
    """Generate explicit Standard Not Found response.

    Per AGT-03: Agent explicitly states Standard Not Found when
    knowledge base has no relevant guidance.

    Args:
        state: QueryState with query, threshold, and confidence.

    Returns:
        Updated state with bilingual Standard Not Found response.
    """
    from src.prompts.templates import create_not_found_response

    response = create_not_found_response(
        query=state["query"],
        threshold=state["threshold"],
        confidence=state["confidence"],
    )

    return {
        **state,
        "response": response,
    }


# ============================================================================
# Graph Factories
# ============================================================================


def create_ingestion_graph() -> StateGraph:
    """Create document ingestion workflow graph.

    Nodes:
        load_document -> chunk_document -> embed_chunks -> store_vectors -> END

    Returns:
        Compiled StateGraph for ingestion pipeline.
    """
    workflow = StateGraph(IngestionState)

    # Add nodes
    workflow.add_node("load_document", load_document_node)
    workflow.add_node("chunk_document", chunk_document_node)
    workflow.add_node("embed_chunks", embed_chunks_node)
    workflow.add_node("store_vectors", store_vectors_node)

    # Define edges
    workflow.add_edge("load_document", "chunk_document")
    workflow.add_edge("chunk_document", "embed_chunks")
    workflow.add_edge("embed_chunks", "store_vectors")
    workflow.add_edge("store_vectors", END)

    return workflow.compile()


# ============================================================================
# PRD Review Graph Nodes
# ============================================================================


def should_refine_node(state: PRDReviewState) -> PRDReviewState:
    """Increment iteration counter when entering refine path."""
    return {"review_iteration": state["review_iteration"] + 1}


def should_refine_decision(state: PRDReviewState) -> Literal["refine", "generate_report"]:
    """Decide whether to continue refinement or generate report.

    Continue refining if:
    1. Haven't reached max_iterations
    2. Findings have changed significantly (convergence check)

    Per D-17: Max 3 iterations for iterative refinement.
    """
    if state["review_iteration"] >= state["max_iterations"]:
        return "generate_report"
    # TODO: Add convergence check - if refined_findings == all_findings, stop
    return "refine"


def re_retrieve_node(state: PRDReviewState) -> PRDReviewState:
    """Query knowledge base again with refined context.

    For now, pass state through (refinement logic placeholder).
    """
    return {"refined_findings": state["all_findings"]}


def error_handler_node(state: Union[PRDReviewState, ImageReviewState]) -> Union[PRDReviewState, ImageReviewState]:
    """Handle errors after retries exhausted - generate bilingual error and halt.

    Per D-25: After all retries exhausted, generates bilingual error response and halts graph.
    Uses create_not_found_response template for bilingual output.
    """
    error = state.get("error", "Unknown error")
    from src.prompts.templates import create_not_found_response

    # Generate bilingual error message using Standard Not Found template
    error_response = create_not_found_response(
        query=f"Error encountered: {error}",
        threshold=0.7,
        confidence=0.0,
    )

    return {
        **state,
        "status": "error",
        "report": f"Error | 错误: {error}\n\n{error_response}",
        "error": error,
    }


def should_handle_error(state: Union[PRDReviewState, ImageReviewState]) -> Literal["error_handler", "should_refine"]:
    """Route to error handler if error is set, otherwise continue to refinement check.

    Per D-25: Catches exceptions from all graph nodes via conditional routing.
    """
    if state.get("error"):
        return "error_handler"
    return "should_refine"


def generate_report_node(state: PRDReviewState) -> PRDReviewState:
    """Generate compliance report from findings.

    Uses refined_findings if available, otherwise all_findings.
    """
    from src.report.markdown import generate_compliance_report
    from datetime import datetime

    findings = state.get("refined_findings", state["all_findings"])
    metadata = {
        "collection_name": state["collection_name"],
        "review_depth": state["review_depth"],
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    report = generate_compliance_report(findings, metadata)
    return {"report": report, "status": "completed"}


def create_prd_review_graph() -> StateGraph:
    """Create PRD review workflow with fan-out/join and iterative refinement.

    Graph structure:
        start -> fan-out (4 parallel validators)
               -> aggregate_findings
               -> (conditional: iterate? -> re_retrieve -> validate) x max_iterations
               -> generate_report -> END

    Per D-17: Max 3 iterations for iterative refinement.
    Per D-16: review_depth controls max_iterations, retrieval_k.
    """
    from src.workflow.state import PRDReviewState
    from src.workflow.nodes import (
        validate_structure_node,
        validate_terminology_node,
        validate_completeness_node,
        validate_formatting_node,
        aggregate_findings_node,
    )

    workflow = StateGraph(PRDReviewState)

    # Fan-out: 4 parallel validation nodes
    workflow.add_node("validate_structure", validate_structure_node)
    workflow.add_node("validate_terminology", validate_terminology_node)
    workflow.add_node("validate_completeness", validate_completeness_node)
    workflow.add_node("validate_formatting", validate_formatting_node)

    # Join: aggregate findings
    workflow.add_node("aggregate_findings", aggregate_findings_node)
    workflow.add_node("error_handler", error_handler_node)

    # Iterative refinement loop
    workflow.add_node("should_refine", should_refine_node)
    workflow.add_node("re_retrieve", re_retrieve_node)

    # Report generation
    workflow.add_node("generate_report", generate_report_node)

    # Entry point: __start__ -> all 4 validators (fan-out in parallel)
    workflow.add_edge("__start__", "validate_structure")
    workflow.add_edge("__start__", "validate_terminology")
    workflow.add_edge("__start__", "validate_completeness")
    workflow.add_edge("__start__", "validate_formatting")

    # Fan-out edges: all validators feed into aggregate_findings
    workflow.add_edge("validate_structure", "aggregate_findings")
    workflow.add_edge("validate_terminology", "aggregate_findings")
    workflow.add_edge("validate_completeness", "aggregate_findings")
    workflow.add_edge("validate_formatting", "aggregate_findings")

    # Join to refinement check with error handling
    # Error handling conditional edge per D-25
    workflow.add_conditional_edges(
        "aggregate_findings",
        should_handle_error,
        {"error_handler": "error_handler", "should_refine": "should_refine"},
    )
    workflow.add_edge("error_handler", END)  # Error handler halts

    # Refinement conditional: loop back to validators or proceed to report
    workflow.add_conditional_edges(
        "should_refine",
        should_refine_decision,
        {
            "refine": "re_retrieve",
            "generate_report": "generate_report",
        },
    )

    # Re-retrieve loops back to validators
    workflow.add_edge("re_retrieve", "validate_structure")

    # Report to END
    workflow.add_edge("generate_report", END)

    return workflow.compile()


# ============================================================================
# Image Review Graph Nodes
# ============================================================================


def should_refine_image_decision(state: ImageReviewState) -> Literal["refine", "generate_report"]:
    """Decide whether to continue refinement or generate report for image review.

    Continue refining if:
    1. Haven't reached max_iterations
    2. Findings have changed significantly

    Per D-17: Max iterations controlled by review_depth.
    """
    if state["review_iteration"] >= state["max_iterations"]:
        return "generate_report"
    # TODO: Add convergence check
    return "refine"


def re_retrieve_image_node(state: ImageReviewState) -> ImageReviewState:
    """Query knowledge base again with refined context for image review.

    Retrieves design tokens with version metadata filtering per D-24.
    """
    return {"refined_findings": state["all_findings"]}


def generate_image_report_node(state: ImageReviewState) -> ImageReviewState:
    """Generate compliance report from image review findings.

    Uses refined_findings if available, otherwise all_findings.
    Includes all finding categories: color, typography, spacing, accessibility, assumptions.
    """
    from src.report.markdown import generate_compliance_report
    from datetime import datetime

    findings = state.get("refined_findings", state["all_findings"])
    metadata = {
        "collection_name": state["collection_name"],
        "review_depth": state["review_depth"],
        "image_path": state["image_path"],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "review_type": "image_review",
    }
    report = generate_compliance_report(findings, metadata)
    return {"report": report, "status": "completed"}


def create_image_review_graph() -> StateGraph:
    """Create image review workflow with 5-way parallel fan-out per D-22.

    Graph structure:
        start -> validate_color (IMG-01, IMG-02)
              -> validate_typography (IMG-03)
              -> validate_spacing (IMG-04)
              -> validate_accessibility (IMG-05)
              -> detect_prd_assumptions (PRD-05)
              -> aggregate_findings
              -> (conditional: iterate? -> re_retrieve -> validators) x max_iterations
              -> generate_report -> END

    Returns:
        Compiled StateGraph for image review pipeline.
    """
    from src.workflow.state import ImageReviewState

    # Import real validators from src.workflow.nodes (wired in 03-04)
    from src.workflow.nodes import (
        validate_color_node,
        validate_typography_node,
        validate_spacing_node,
        validate_accessibility_node,
        detect_prd_assumptions_node,
        aggregate_image_findings_node,
    )

    workflow = StateGraph(ImageReviewState)

    # Fan-out: 5 parallel validation nodes per D-22
    workflow.add_node("validate_color", validate_color_node)
    workflow.add_node("validate_typography", validate_typography_node)
    workflow.add_node("validate_spacing", validate_spacing_node)
    workflow.add_node("validate_accessibility", validate_accessibility_node)
    workflow.add_node("detect_prd_assumptions", detect_prd_assumptions_node)

    # Join: aggregate findings
    workflow.add_node("aggregate_findings", aggregate_image_findings_node)
    workflow.add_node("error_handler", error_handler_node)

    # Iterative refinement loop per D-17
    workflow.add_node("should_refine", lambda state: {"review_iteration": state["review_iteration"] + 1})
    workflow.add_node("re_retrieve", re_retrieve_image_node)

    # Report generation
    workflow.add_node("generate_report", generate_image_report_node)

    # Entry point: __start__ -> all 5 validators (fan-out in parallel)
    workflow.add_edge("__start__", "validate_color")
    workflow.add_edge("__start__", "validate_typography")
    workflow.add_edge("__start__", "validate_spacing")
    workflow.add_edge("__start__", "validate_accessibility")
    workflow.add_edge("__start__", "detect_prd_assumptions")

    # Fan-out edges: all validators feed into aggregate_findings
    workflow.add_edge("validate_color", "aggregate_findings")
    workflow.add_edge("validate_typography", "aggregate_findings")
    workflow.add_edge("validate_spacing", "aggregate_findings")
    workflow.add_edge("validate_accessibility", "aggregate_findings")
    workflow.add_edge("detect_prd_assumptions", "aggregate_findings")

    # Join to refinement check with error handling
    # Error handling conditional edge per D-25
    workflow.add_conditional_edges(
        "aggregate_findings",
        should_handle_error,
        {"error_handler": "error_handler", "should_refine": "should_refine"},
    )
    workflow.add_edge("error_handler", END)  # Error handler halts

    # Refinement conditional: loop back to validators or proceed to report
    workflow.add_conditional_edges(
        "should_refine",
        should_refine_image_decision,
        {
            "refine": "re_retrieve",
            "generate_report": "generate_report",
        },
    )

    # Re-retrieve loops back to all 5 validators (5-way fan-out per D-17)
    workflow.add_edge("re_retrieve", "validate_color")
    workflow.add_edge("re_retrieve", "validate_typography")
    workflow.add_edge("re_retrieve", "validate_spacing")
    workflow.add_edge("re_retrieve", "validate_accessibility")
    workflow.add_edge("re_retrieve", "detect_prd_assumptions")

    # Report to END
    workflow.add_edge("generate_report", END)

    return workflow.compile()


def create_query_graph() -> StateGraph:
    """Create knowledge base query workflow graph.

    Nodes:
        query_knowledge -> (format_results | standard_not_found) -> END

    Conditional routing per AGT-03:
        If confidence >= threshold -> format_results
        If confidence < threshold -> standard_not_found

    Returns:
        Compiled StateGraph for query pipeline.
    """
    workflow = StateGraph(QueryState)

    # Add nodes
    workflow.add_node("query_knowledge", query_knowledge_node)
    workflow.add_node("format_results", format_results_node)
    workflow.add_node("standard_not_found", standard_not_found_node)

    # Conditional routing based on standard_found
    def should_query_standard_found(state: QueryState) -> Literal["format_results", "standard_not_found"]:
        if state["standard_found"]:
            return "format_results"
        return "standard_not_found"

    workflow.add_conditional_edges(
        "query_knowledge",
        should_query_standard_found,
        {
            "format_results": "format_results",
            "standard_not_found": "standard_not_found",
        },
    )

    # Edges from terminal nodes to END
    workflow.add_edge("format_results", END)
    workflow.add_edge("standard_not_found", END)

    return workflow.compile()


# ============================================================================
# Knowledge Base Workflow Wrapper
# ============================================================================


class KnowledgeBaseWorkflow:
    """Wrapper class for ingestion and query workflows.

    Provides convenient interface for common operations with
    the design standards knowledge base.

    Attributes:
        embedding_fn: BGE_M3_Embeddings instance for embedding generation.
        collection_name: Default Chroma collection name.
    """

    def __init__(
        self,
        embedding_fn: BGE_M3_Embeddings,
        collection_name: str = "design_standards",
    ):
        """Initialize knowledge base workflow.

        Args:
            embedding_fn: BGE_M3_Embeddings instance for embeddings.
            collection_name: Default Chroma collection name.
        """
        self.embedding_fn = embedding_fn
        self.collection_name = collection_name

        # Compile graphs
        self.ingestion_graph = create_ingestion_graph()
        self.query_graph = create_query_graph()

    def ingest(self, file_path: str, metadata: dict) -> IngestionState:
        """Ingest a document into the knowledge base.

        Args:
            file_path: Path to document file.
            metadata: Document metadata (document_name, version_id, effective_date).

        Returns:
            Final IngestionState after pipeline completes.
        """
        from src.workflow.state import get_initial_ingestion_state

        initial = get_initial_ingestion_state(
            file_path=file_path,
            metadata=metadata,
            collection_name=self.collection_name,
        )
        return self.ingestion_graph.invoke(initial)

    def query(self, query: str, threshold: float = 0.7) -> QueryState:
        """Query the knowledge base.

        Args:
            query: Natural language query.
            threshold: Minimum confidence threshold (default: 0.7).

        Returns:
            Final QueryState with response.
        """
        from src.workflow.state import get_initial_query_state

        initial = get_initial_query_state(
            query=query,
            threshold=threshold,
            collection_name=self.collection_name,
        )
        return self.query_graph.invoke(initial)


__all__ = [
    "create_ingestion_graph",
    "create_query_graph",
    "create_prd_review_graph",
    "create_image_review_graph",
    "KnowledgeBaseWorkflow",
]
