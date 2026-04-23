# tests/infrastructure/test_bge_m3_embedding.py
import pytest
from src_v2.infrastructure.embeddings.bge_m3_embedding import BgeM3EmbeddingService

@pytest.fixture
def embedding_service():
    return BgeM3EmbeddingService()

def test_embed_text(embedding_service):
    embedding = embedding_service.embed_query("Spacing standard for mobile")
    assert isinstance(embedding, list)
    assert len(embedding) == 1024  # bge-m3 embedding dimension
    assert all(isinstance(x, float) for x in embedding)

def test_embed_documents(embedding_service):
    texts = [
        "Color contrast ratio should be 4.5:1",
        "Typography scale for headings",
    ]
    embeddings = embedding_service.embed_documents(texts)
    assert len(embeddings) == 2
    assert all(len(e) == 1024 for e in embeddings)