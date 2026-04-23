# tests/infrastructure/test_chroma_store.py
import pytest
from src_v2.infrastructure.vectorstore.chroma_store import ChromaStore
from src_v2.domain.ingestion.entities import Chunk, DocumentContentType
from src_v2.domain.shared.value_objects import ChunkId, DocumentId

@pytest.fixture
def chroma_store():
    store = ChromaStore(collection_name="test_collection")
    yield store
    store.delete_collection()

def test_store_and_retrieve_chunk(chroma_store):
    chunk = Chunk(
        id=ChunkId("chunk-001"),
        document_id=DocumentId("doc-001"),
        content="This is a test chunk about spacing standards",
        content_type=DocumentContentType.SPACING,
        metadata={"standard_id": "sp-001"},
        embedding=[0.1] * 384,
    )
    chroma_store.store_chunk(chunk)

    results = chroma_store.similarity_search([0.1] * 384, k=1)
    assert len(results) == 1
    assert results[0][0].page_content == "This is a test chunk about spacing standards"

def test_find_by_document_id(chroma_store):
    chunk = Chunk(
        id=ChunkId("chunk-002"),
        document_id=DocumentId("doc-002"),
        content="Color standard content",
        content_type=DocumentContentType.COLOR,
        metadata={},
        embedding=[0.2] * 384,
    )
    chroma_store.store_chunk(chunk)

    results = chroma_store.find_by_document_id(DocumentId("doc-002"))
    assert len(results) == 1
    assert results[0].id == "chunk-002"