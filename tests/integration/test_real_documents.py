#!/usr/bin/env python3
"""Test ingestion and retrieval with real documents."""

import sys
sys.path.insert(0, ".")

from src_v2.domain.ingestion.entities import Document, DocumentContentType
from src_v2.infrastructure.chunking.adaptive_chunker import AdaptiveChunkingService
from src_v2.infrastructure.embeddings.bge_m3_embedding import BgeM3EmbeddingService
from src_v2.infrastructure.vectorstore.chroma_store import ChromaStore
from src_v2.infrastructure.ingestion.chunk_repository_impl import ChunkRepositoryImpl

def load_doc(path: str) -> str:
    """Load document content."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def test_prd_ingestion():
    """Test ingesting PRD document."""
    print("=" * 60)
    print("Testing PRD Document Ingestion")
    print("=" * 60)

    prd_path = "Prd-test/吉盛园林里程碑看板需求文档.md"
    prd_content = load_doc(prd_path)
    print(f"\n[*] Loaded PRD: {prd_path}")
    print(f"    Content length: {len(prd_content)} chars")

    chunking = AdaptiveChunkingService()
    embedding = BgeM3EmbeddingService()
    vector_store = ChromaStore(collection_name="prd_test")
    repo = ChunkRepositoryImpl(vector_store, embedding)

    doc = Document(
        id="prd-001",
        content=prd_content,
        content_type=DocumentContentType.GENERAL,
        metadata={"source": prd_path, "title": "吉盛园林里程碑看板"},
    )

    print("\n[*] Chunking document...")
    chunks = chunking.chunk_document(doc)
    print(f"    Created {len(chunks)} chunks")

    print("\n[*] Storing chunks in vector database...")
    for chunk in chunks:
        repo.store_chunk(chunk)
    print(f"    Stored {len(chunks)} chunks")

    print("\n[*] Testing similarity search...")

    query1 = "项目经理筛选功能"
    emb1 = embedding.embed_query(query1)
    results1 = repo.find_similar(emb1, k=2)
    print(f"\n    Query: '{query1}'")
    for i, (doc, score) in enumerate(results1):
        print(f"    [{i+1}] Score: {score:.4f} | {doc.page_content[:80]}...")

    query2 = "里程碑完成率计算方式"
    emb2 = embedding.embed_query(query2)
    results2 = repo.find_similar(emb2, k=2)
    print(f"\n    Query: '{query2}'")
    for i, (doc, score) in enumerate(results2):
        print(f"    [{i+1}] Score: {score:.4f} | {doc.page_content[:80]}...")

    vector_store.delete_collection()
    print("\n[+] PRD ingestion test completed!")

def test_design_standard_ingestion():
    """Test ingesting design standard document."""
    print("\n" + "=" * 60)
    print("Testing Design Standard Ingestion")
    print("=" * 60)

    standard_path = "Design-Reference/产品设计标准文档V2.０--25年持续更新.md"
    standard_content = load_doc(standard_path)
    print(f"\n[*] Loaded Design Standard: {standard_path}")
    print(f"    Content length: {len(standard_content)} chars")

    chunking = AdaptiveChunkingService()
    embedding = BgeM3EmbeddingService()
    vector_store = ChromaStore(collection_name="design_standards_test")
    repo = ChunkRepositoryImpl(vector_store, embedding)

    doc = Document(
        id="standard-001",
        content=standard_content,
        content_type=DocumentContentType.SPACING,
        metadata={"source": standard_path, "title": "产品设计标准文档V2.0"},
    )

    print("\n[*] Chunking document...")
    chunks = chunking.chunk_document(doc)
    print(f"    Created {len(chunks)} chunks")

    print("\n[*] Storing chunks in vector database...")
    for chunk in chunks:
        repo.store_chunk(chunk)
    print(f"    Stored {len(chunks)} chunks")

    print("\n[*] Testing similarity search...")

    query1 = "移动端间距要求"
    emb1 = embedding.embed_query(query1)
    results1 = repo.find_similar(emb1, k=2)
    print(f"\n    Query: '{query1}'")
    for i, (doc, score) in enumerate(results1):
        print(f"    [{i+1}] Score: {score:.4f} | {doc.page_content[:80]}...")

    query2 = "颜色对比度 WCAG"
    emb2 = embedding.embed_query(query2)
    results2 = repo.find_similar(emb2, k=2)
    print(f"\n    Query: '{query2}'")
    for i, (doc, score) in enumerate(results2):
        print(f"    [{i+1}] Score: {score:.4f} | {doc.page_content[:80]}...")

    vector_store.delete_collection()
    print("\n[+] Design standard ingestion test completed!")

if __name__ == "__main__":
    test_prd_ingestion()
    test_design_standard_ingestion()
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)