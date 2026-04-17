"""LangGraph workflow graphs for ingestion and query pipelines.

Provides StateGraph-based workflows for document ingestion and knowledge
base querying per AGT-01 (LangGraph StateGraph) and AGT-03 (Standard Not Found).

References:
- AGT-01: Use LangGraph StateGraph, not pure LangChain chains
- AGT-03: Explicit Standard Not Found when confidence < threshold
- D-12: Standard Not Found when no relevant guidance
"""

from typing import Literal

from langgraph.graph import StateGraph, END

from src.workflow.state import IngestionState, QueryState
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
    "KnowledgeBaseWorkflow",
]
