# tests/integration/test_standard_ingestion_flow.py
"""Test complete flow: ingest standards -> store in ChromaDB -> retrieve."""

import pytest
from src_v2.domain.ingestion.entities import Document, DocumentContentType
from src_v2.domain.ingestion.services import IChunkingService
from src_v2.infrastructure.chunking.adaptive_chunker import AdaptiveChunkingService
from src_v2.infrastructure.embeddings.bge_m3_embedding import BgeM3EmbeddingService
from src_v2.infrastructure.vectorstore.chroma_store import ChromaStore
from src_v2.infrastructure.ingestion.chunk_repository_impl import ChunkRepositoryImpl

@pytest.fixture
def services():
    chunking = AdaptiveChunkingService()
    embedding = BgeM3EmbeddingService()
    vector_store = ChromaStore(collection_name="test_standards")
    repo = ChunkRepositoryImpl(vector_store, embedding)
    yield {"chunking": chunking, "embedding": embedding, "vector_store": vector_store, "repo": repo}
    vector_store.delete_collection()

def test_ingest_and_retrieve_standard(services):
    # 1. Create a standard document
    doc = Document(
        id="std-001",
        content="Spacing standard: margins should be at least 16px on mobile devices",
        content_type=DocumentContentType.SPACING,
        metadata={"category": "mobile", "standard_id": "sp-001"},
    )

    # 2. Chunk the document
    chunks = services["chunking"].chunk_document(doc)
    assert len(chunks) > 0

    # 3. Store chunks with embeddings
    for chunk in chunks:
        services["repo"].store_chunk(chunk)

    # 4. Retrieve by similarity
    query_embedding = services["embedding"].embed_query("mobile spacing requirements")
    results = services["repo"].find_similar(query_embedding, k=1)

    assert len(results) > 0
    assert "spacing" in results[0][0].page_content.lower()

def test_find_by_document_id(services):
    # 1. Create multiple chunks for the same document
    doc = Document(
        id="doc-multi-001",
        content="Color standard: primary color should be #333333 and secondary #666666 for text contrast ratio 4.5:1",
        content_type=DocumentContentType.COLOR,
        metadata={"standard_id": "color-001"},
    )

    # 2. Chunk and store
    chunks = services["chunking"].chunk_document(doc)
    for chunk in chunks:
        services["repo"].store_chunk(chunk)

    # 3. Find by document ID
    from src_v2.domain.shared.value_objects import DocumentId
    results = services["repo"].find_by_document_id(DocumentId("doc-multi-001"))

    assert len(results) > 0
    # All chunks should belong to the same document
    for chunk in results:
        assert chunk.document_id == "doc-multi-001"

def test_similarity_search_ranking(services):
    # Create documents with different content
    docs = [
        Document(
            id="std-color",
            content="Color standard: maintain WCAG AA contrast ratio of 4.5:1 for normal text",
            content_type=DocumentContentType.COLOR,
            metadata={"standard_id": "color-aa"},
        ),
        Document(
            id="std-spacing",
            content="Spacing standard: use 8pt grid system for consistent vertical rhythm",
            content_type=DocumentContentType.SPACING,
            metadata={"standard_id": "spacing-grid"},
        ),
        Document(
            id="std-typo",
            content="Typography standard: heading font size 24px, body text 16px line-height 1.5",
            content_type=DocumentContentType.TYPOGRAPHY,
            metadata={"standard_id": "typo-scale"},
        ),
    ]

    # Store all
    for doc in docs:
        chunks = services["chunking"].chunk_document(doc)
        for chunk in chunks:
            services["repo"].store_chunk(chunk)

    # Query with color-related text
    query_embedding = services["embedding"].embed_query("What color contrast is required for accessibility?")
    results = services["repo"].find_similar(query_embedding, k=3)

    assert len(results) == 3
    # Color standard should rank highest for color-related query
    top_result_content = results[0][0].page_content.lower()
    assert "color" in top_result_content or "contrast" in top_result_content