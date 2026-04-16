# Phase 01: Core RAG Pipeline - Research

**Researched:** 2026/04/16
**Domain:** RAG pipeline implementation (document ingestion, structural chunking, embedding pipeline, vector storage)
**Confidence:** MEDIUM

## Summary

Phase 1 establishes the knowledge base foundation for the design document review system. This involves building a RAG pipeline that can ingest 100+ page design standards documents (Markdown/PDF/HTML/DOCX), chunk them structurally preserving header hierarchy, embed them with bge-m3 for bilingual Chinese/English retrieval, and store in Chroma with hybrid BM25+vector search. The pipeline uses LangGraph for workflow orchestration, not pure LangChain chains.

**Primary recommendation:** Use LangChain's `RecursiveCharacterTextSplitter` with custom header-aware splitting for structural chunking (D-01, D-02, D-03). Use `sentence-transformers` to load bge-m3 for embeddings (D-04, D-05). Use Chroma for vector storage with BM25 reranking via `rank_bm25` library for hybrid retrieval (RAG-05). Implement "Standard Not Found" as an explicit behavior when retrieval confidence is below threshold (D-12, AGT-03).

## User Constraints (from CONTEXT.md)

### Locked Decisions
| Decision | Value |
|----------|-------|
| D-01 | Chunk size: 500-800 tokens |
| D-02 | Overlap: 15-20% |
| D-03 | Split method: Header + Paragraph |
| D-04 | Embedding model: bge-m3 (1024 dimensions) |
| D-05 | Batch size: 64 |
| D-06 | Support all formats: Markdown, PDF, HTML, DOCX |
| D-07 | Use `unstructured` for multi-format parsing |
| D-08 | Use `pdfplumber` for enhanced PDF text extraction |
| D-09 | Embedded images: treat as text references only |
| D-10 | All outputs must be bilingual (Chinese/English) |
| D-11 | Embeddings must support Chinese/English cross-lingual retrieval |
| D-12 | Explicitly state "Standard Not Found" when no relevant guidance |

### Claude's Discretion
- Choose between LangChain's built-in `RecursiveCharacterTextSplitter` vs. building custom header-aware splitter
- Choose BM25 library implementation (LangChain has BM25, or standalone `rank_bm25`)
- Choose how to structure LangGraph workflow (nodes, edges, state schema)

### Deferred Ideas (OUT OF SCOPE)
- OCR for embedded images in PDFs (Phase 3)
- Image similarity search (Phase 3+)

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RAG-01 | User can ingest 100+ pages of design standards documents (Markdown/PDF) into Chroma vector store | `unstructured.IngestionAPI` for multi-format; Chroma `add_documents` API; batch processing |
| RAG-02 | System uses structural chunking (split on headers, list items) to preserve document context | `RecursiveCharacterTextSplitter` with `separators` configuration; header metadata preservation |
| RAG-03 | System uses bge-m3 embeddings for bilingual Chinese/English retrieval | `sentence-transformers.SentenceTransformer('BAAI/bge-m3')`; 1024-dim output |
| RAG-04 | User can query knowledge base with natural language and retrieve relevant standards | Chroma `similarity_search` with query embedding; LangChain `VectorStore` abstraction |
| RAG-05 | System supports hybrid retrieval (BM25 + vector) for precision | `rank_bm25` library for BM25; combined score reranking |
| RAG-06 | Retrieved standards include source attribution (document name, section, version) | Chroma metadata with `document_name`, `section`, `version_id`, `effective_date` |
| AGT-01 | System uses LangGraph for workflow orchestration (not pure LangChain chains) | `langgraph.graph.StateGraph` with TypedDict state; workflow.compile() |
| AGT-03 | Agent explicitly states "Standard Not Found" when knowledge base has no relevant guidance | Retrieval threshold check; explicit fallback response |

## Standard Stack

### Core Dependencies
| Library | Recommended Version | Purpose | Source |
|---------|---------------------|---------|--------|
| langchain | ^0.3.x | RAG abstractions (document loaders, text splitters, vector stores, prompts) | [ASSUMED: CLAUDE.md] |
| langgraph | ^0.2.x | Workflow orchestration (StateGraph, nodes, edges) | [ASSUMED: CLAUDE.md] |
| chromadb | latest (pip) | Local vector database | [ASSUMED: npm showed 3.4.3 JS; Python version varies] |
| sentence-transformers | latest | bge-m3 embedding model loading | [ASSUMED: standard Python ML package] |

### Document Processing
| Library | Purpose | When to Use |
|---------|---------|-------------|
| unstructured | Multi-format document parsing (PDF, DOCX, HTML, MD) | Primary document loader |
| pdfplumber | Enhanced PDF text extraction (tables, precise layout) | When unstructured fails on PDFs |
| python-docx | DOCX text extraction | When unstructured insufficient |
| markdown | Markdown parsing | Extract header hierarchy from MD files |

### Hybrid Retrieval
| Library | Purpose | When to Use |
|---------|---------|-------------|
| rank_bm25 | BM25 keyword search | Hybrid retrieval scoring |

**Installation:**
```bash
uv add langchain langgraph langchain-community
uv add chromadb sentence-transformers
uv add unstructured pdfplumber python-docx markdown
uv add rank-bm25
```

**Version verification (pending - packages not installed):**
```bash
uv pip show langchain langgraph chromadb | grep -E "^Name:|^Version:"
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── ingestion/              # Document processing pipeline
│   ├── loaders.py           # Format-specific loaders (PDF, MD, DOCX, HTML)
│   ├── chunker.py           # Structural text splitting
│   └── pipeline.py          # End-to-end ingestion orchestrator
├── embeddings/
│   └── bge_m3.py            # bge-m3 embedding model wrapper
├── vectorstore/
│   └── chroma_store.py      # Chroma collection management
├── retrieval/
│   ├── hybrid_search.py     # BM25 + vector hybrid retrieval
│   └── query_router.py      # Query processing
├── workflow/
│   ├── state.py             # LangGraph ReviewState TypedDict
│   ├── nodes.py             # Workflow nodes
│   └── graph.py             # StateGraph compilation
└── prompts/
    └── templates.py         # Prompt templates
```

### Pattern 1: Structural Chunking with Header Preservation

**What:** Split documents on header boundaries (h1, h2, h3) and paragraph breaks, preserving header hierarchy as chunk metadata.

**When to use:** Phase 1 RAG-02 requirement for preserving document context.

**Implementation approach:**
```python
# Source: [ASSUMED - LangChain RecursiveCharacterTextSplitter docs]
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    separators=["##", "#", "\n\n", "\n", ". ", " ", ""],
    chunk_size=600,  # D-01: 500-800 tokens
    chunk_overlap=90,  # D-02: 15-20% of 600
    length_function=token_count,
    add_start_index=True,
)
```

**Header-aware chunking variant:**
```python
# For Markdown with clear header structure:
def chunk_by_headers(document: str, metadata: dict) -> list[Document]:
    """Split on ## headers, preserve header hierarchy as metadata."""
    sections = document.split("\n## ")
    chunks = []
    for i, section in enumerate(sections):
        if i == 0 and not section.startswith("#"):
            # First section without header
            chunks.extend(text_splitter.split_text(section))
        else:
            header = section.split("\n")[0]
            content = "\n".join(section.split("\n")[1:])
            for chunk in text_splitter.split_text(content):
                chunks.append(Document(
                    page_content=chunk,
                    metadata={
                        **metadata,
                        "section": header.strip("# ").strip(),
                        "chunk_index": i,
                    }
                ))
    return chunks
```

### Pattern 2: Hybrid BM25 + Vector Retrieval

**What:** Combine BM25 keyword matching with semantic vector similarity for precise retrieval.

**When to use:** RAG-05 requirement for hybrid retrieval.

**Implementation:**
```python
# Source: [ASSUMED - rank_bm25 + LangChain integration pattern]
from rank_bm25 import BM25Okapi
import chromadb

class HybridRetriever:
    def __init__(self, texts: list[str], embedding_fn, collection):
        self.texts = texts
        self.embedding_fn = embedding_fn
        self.collection = collection
        self.bm25 = BM25Okapi(texts)

    def search(self, query: str, k: int = 5, alpha: float = 0.5):
        # BM25 scores
        bm25_scores = self.bm25.get_scores(query.split()).tolist()

        # Vector similarity
        query_embedding = self.embedding_fn([query])
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=k
        )

        # Combined scoring (Reciprocal Rank Fusion or linear combination)
        combined_scores = []
        for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
            vector_score = 1 / (1 + distance)
            bm25_score = bm25_scores[int(doc_id)] if int(doc_id) < len(bm25_scores) else 0
            combined_scores.append((doc_id, alpha * vector_score + (1 - alpha) * bm25_score))

        return sorted(combined_scores, key=lambda x: x[1], reverse=True)[:k]
```

### Pattern 3: LangGraph Workflow for Ingestion Pipeline

**What:** Use LangGraph StateGraph to orchestrate the ingestion workflow with explicit state passing.

**When to use:** AGT-01 requirement (LangGraph for workflow orchestration).

**Implementation:**
```python
# Source: [ASSUMED - LangGraph StateGraph pattern]
from langgraph.graph import StateGraph, END
from typing import TypedDict

class IngestionState(TypedDict):
    file_path: str
    document_text: str
    chunks: list[Document]
    embeddings: list[list[float]]
    collection_name: str
    status: str

def create_ingestion_graph():
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

# Nodes use LangChain internally
def load_document_node(state: IngestionState) -> IngestionState:
    from langchain_community.document_loaders import UnstructuredFileLoader
    loader = UnstructuredFileLoader(state["file_path"])
    docs = loader.load()
    return {"document_text": docs[0].page_content, "status": "loaded"}
```

### Pattern 4: Chroma Metadata for Source Attribution

**What:** Store document metadata (name, section, version) in Chroma for retrieval result attribution.

**When to use:** RAG-06 requirement for source attribution.

**Implementation:**
```python
# Source: [ASSUMED - Chroma metadata pattern]
from langchain.schema import Document

def create_chunk_with_metadata(content: str, doc_info: dict) -> Document:
    return Document(
        page_content=content,
        metadata={
            "document_name": doc_info["name"],
            "document_version": doc_info["version"],
            "effective_date": doc_info["effective_date"],
            "section": doc_info.get("section", ""),
            "subsection": doc_info.get("subsection", ""),
            "page_number": doc_info.get("page", 0),
            "source_file": doc_info["file_path"],
        }
    )

# Query and preserve metadata
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    include=["documents", "metadatas", "distances"]
)

for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print(f"Standard: {doc}")
    print(f"Source: {meta['document_name']} / {meta['section']} (v{meta['document_version']})")
```

### Pattern 5: "Standard Not Found" Behavior

**What:** Explicit check after retrieval; if no high-confidence results, return "Standard Not Found" instead of hallucinating.

**When to use:** D-12 and AGT-03 requirement.

**Implementation:**
```python
# Source: [ASSUMED - confidence threshold pattern from PITFALLS.md]
def retrieve_with_not_found(query: str, threshold: float = 0.7) -> dict:
    results = hybrid_retriever.search(query, k=5)

    if not results or results[0][1] < threshold:
        return {
            "found": False,
            "response": "Standard Not Found",
            "response_zh": "未找到相关标准",
            "message": "Knowledge base has no relevant guidance for this query."
        }

    return {
        "found": True,
        "results": results,
        "standards": [format_standard(r) for r in results]
    }
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Document parsing | Custom PDF/DOCX/HTML parsers | `unstructured` library | Handles 10+ formats, battle-tested, updates with format changes |
| Header detection | Regex for Markdown headers | `markdown` library or `unstructured` | Correctly handles edge cases (code blocks, escaped characters) |
| BM25 implementation | Custom TF-IDF | `rank_bm25` library | Optimized, handles edge cases, well-tested |
| Embedding model | Custom sentence transformer | `sentence-transformers` with `BAAI/bge-m3` | Optimized inference, easy dimension control |
| Vector store | Direct Chroma API | LangChain `VectorStore` abstraction | Swappable backends, consistent interface |

**Key insight:** Document parsing and embedding models are solved problems. Use battle-tested libraries rather than building custom solutions that will fail on edge cases.

## Common Pitfalls

### Pitfall 1: Semantic Chunking Destroys Document Structure

**What goes wrong:** Fixed-size chunking splits mid-sentence, mid-header, mid-list. Retrieved chunks lack context.

**Why it happens:** `RecursiveCharacterTextSplitter` with only character separators doesn't understand document structure.

**How to avoid:**
- Use `separators=["\n## ", "\n# ", "\n\n", "\n", ". ", " "]` to split on headers first
- Preserve header hierarchy in chunk metadata
- For PDFs, prefer `pdfplumber` over `unstructured` when tables are involved

**Warning signs:** Retrieved chunks starting mid-sentence, missing context about which section they belong to

### Pitfall 2: Embedding Dimension Mismatch with Chroma

**What goes wrong:** bge-m3 outputs 1024-dim vectors but Chroma expects different dimension.

**Why it happens:** Chroma requires explicit dimension specification at collection creation.

**How to avoid:**
```python
# Explicit dimension from model
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-m3')
embedding = model.encode("test")
dimension = len(embedding)  # Should be 1024

collection = client.create_collection(
    name="design_standards",
    metadata={"hnsw:space": "cosine"},
    get_or_create=True
)
# Note: Chroma auto-detects dimension on first add if not specified
```

### Pitfall 3: BM25 Tokenization Mismatch with Embeddings

**What goes wrong:** BM25 uses raw tokenization (whitespace split) but embeddings use subword tokenization. Results don't align.

**Why it happens:** Inconsistent preprocessing between BM25 and vector retrieval produces different relevance rankings.

**How to avoid:**
- Use same text preprocessing for both BM25 and embedding
- Consider using embeddings for final reranking rather than raw BM25 scores
- Test hybrid retrieval with domain-specific queries

### Pitfall 4: No Version Filtering at Query Time

**What goes wrong:** Old superseded standards retrieved alongside current ones.

**Why it happens:** All versions stored with same metadata; no effective date filtering.

**How to avoid:**
- Store `effective_date` and `superseded_date` in metadata
- Filter at query time: only retrieve chunks where `effective_date <= query_date AND (superseded_date IS NULL OR superseded_date > query_date)`
- Phase 3+ requirement (AGT-05) but design schema now

### Pitfall 5: Hybrid Retrieval Alpha Tuning

**What goes wrong:** Hardcoded alpha=0.5 for BM25/vector balance; wrong for domain queries.

**Why it happens:** Domain terminology queries may need more BM25 (keyword match) vs semantic queries need more vector similarity.

**How to avoid:**
- Make alpha configurable
- Start with alpha=0.3 (vector-heavy) for semantic queries
- Consider query-type-dependent alpha (keyword queries -> higher BM25 weight)

## Code Examples

### Document Loading (unstructured + pdfplumber)

```python
# Source: [ASSUMED - unstructured + pdfplumber integration]
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_community.document_loaders import PDFPlumberLoader

def load_document(file_path: str) -> list[Document]:
    """Load document with format-appropriate loader."""
    if file_path.endswith(".pdf"):
        # Try unstructured first, fall back to pdfplumber for tables
        try:
            loader = UnstructuredFileLoader(file_path)
            docs = loader.load()
        except Exception:
            loader = PDFPlumberLoader(file_path)
            docs = loader.load()
    elif file_path.endswith((".docx", ".html", ".md")):
        loader = UnstructuredFileLoader(file_path)
        docs = loader.load()
    else:
        raise ValueError(f"Unsupported format: {file_path}")

    # Add source file metadata
    for doc in docs:
        doc.metadata["source_file"] = file_path

    return docs
```

### Embedding Generation (bge-m3)

```python
# Source: [ASSUMED - sentence-transformers bge-m3 usage]
from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings

class BGE_M3_Embeddings(Embeddings):
    def __init__(self, model_name: str = "BAAI/bge-m3", batch_size: int = 64):
        self.model = SentenceTransformer(model_name)
        self.batch_size = batch_size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(
            texts,
            batch_size=self.batch_size,  # D-05: batch size 64
            show_progress_bar=True,
            normalize_embeddings=True
        ).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode(
            text,
            normalize_embeddings=True
        ).tolist()

# Usage
embeddings = BGE_M3_Embeddings(batch_size=64)  # D-05
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="design_standards"
)
```

### Chroma Collection with Metadata

```python
# Source: [ASSUMED - Chroma metadata indexing]
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="design_standards",
    metadata={
        "description": "Design standards knowledge base",
        "version": "1.0"
    }
)

# Add with metadata for source attribution
collection.add(
    documents=[doc.page_content for doc in chunks],
    embeddings=[embeddings.embed_documents([doc.page_content])[0] for doc in chunks],
    metadatas=[doc.metadata for doc in chunks],
    ids=[f"chunk_{i}" for i in range(len(chunks))]
)
```

### Query with Attribution

```python
# Source: [ASSUMED - Chroma query with metadata]
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    include=["documents", "metadatas", "distances"]
)

attributed_results = []
for doc, meta, distance in zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0]
):
    attributed_results.append({
        "content": doc,
        "source": {
            "document": meta.get("document_name", "Unknown"),
            "section": meta.get("section", "Unknown"),
            "version": meta.get("document_version", "Unknown"),
            "effective_date": meta.get("effective_date", "Unknown"),
            "relevance_score": 1 / (1 + distance)
        }
    })
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Fixed-size chunking (512 chars) | Structural chunking (header + paragraph) | Industry RAG best practices 2024+ | Better context preservation |
| Single vector retrieval | Hybrid BM25 + vector | 2024+ | More precise retrieval for domain terminology |
| Generic embeddings (OpenAI) | Domain-specific bge-m3 | 2024+ | Better Chinese/English bilingual support |
| LangChain chains | LangGraph StateGraph | 2024+ | Complex workflows with cycles, better state management |

**Deprecated/outdated:**
- `CharacterTextSplitter` (naive chunking) - use `RecursiveCharacterTextSplitter`
- Pure vector retrieval without BM25 reranking - use hybrid for precision
- LangChain `AgentExecutor` for complex workflows - use LangGraph

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | LangChain ^0.3.x, LangGraph ^0.2.x versions are current | Standard Stack | Breaking changes may exist; verify before install |
| A2 | `sentence-transformers` loads bge-m3 with 1024-dim output | Standard Stack | Model dimension mismatch with Chroma could cause errors |
| A3 | `unstructured` handles PDF/DOCX/HTML/MD formats reliably | Document Processing | May need format-specific loaders for edge cases |
| A4 | BM25 + vector hybrid with alpha=0.5 is good starting point | Hybrid Retrieval | May need tuning for design domain queries |
| A5 | Chroma `get_or_create` auto-detects embedding dimensions | Chroma Setup | May need explicit dimension parameter |
| A6 | LangGraph `StateGraph` with TypedDict is the right pattern | LangGraph Workflow | Other patterns may be cleaner for ingestion pipeline |

**If this table is empty:** All claims in this research were verified or cited - no user confirmation needed.

## Open Questions

1. **BM25 library choice**
   - What we know: `rank_bm25` is the standard Python BM25 library
   - What's unclear: Whether LangChain has built-in BM25 worth using instead
   - Recommendation: Start with `rank_bm25` for explicit control; switch to LangChain BM25 if integration is cleaner

2. **Token counting for chunk size**
   - What we know: D-01 specifies 500-800 tokens
   - What's unclear: Which tokenization method (tiktoken, HuggingFace tokenizer, or approximate char-based)
   - Recommendation: Use `tiktoken` for OpenAI-compatible tokenization; approximate with 4 chars/token if not available

3. **Chroma vs Qdrant for 100+ pages**
   - What we know: CLAUDE.md recommends Chroma for learning project
   - What's unclear: Performance at 100+ page scale
   - Recommendation: Start with Chroma; migrate to Qdrant if retrieval latency unacceptable

## Environment Availability

> Step 2.6: SKIPPED (no external dependencies beyond Python packages - all tools are local)

**Analysis:** Phase 1 involves only Python package installation and local file processing. No external services (PostgreSQL, Redis, Docker, etc.) required. All dependencies are pip-installable Python packages.

## Security Domain

> Not applicable - Phase 1 is pure RAG pipeline construction; no user input processing or authentication involved yet.

Phase 1 security concerns (for later phases):
- **Input validation**: Sanitize file paths and document content before ingestion
- **Metadata injection**: Validate chunk metadata before storage to prevent injection attacks
- **Query injection**: Validate natural language queries before vector search

## Sources

### Primary (HIGH confidence)
- None verified via Context7/WebFetch due to tool restrictions

### Secondary (MEDIUM confidence)
- [ASSUMED] LangChain `RecursiveCharacterTextSplitter` and `VectorStore` API patterns from training data
- [ASSUMED] `sentence-transformers` bge-m3 loading and embedding generation from model card knowledge
- [ASSUMED] Chroma Python client API for `add_documents`, `query` from documentation patterns

### Tertiary (LOW confidence)
- [ASSUMED] LangChain ^0.3.x, LangGraph ^0.2.x version recommendations from CLAUDE.md (training data)
- [ASSUMED] `rank_bm25` library API and integration pattern

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - training data recommendations, packages not yet installed
- Architecture: MEDIUM - standard RAG patterns, LangGraph pattern well-established
- Pitfalls: MEDIUM - documented from domain expertise, not verified against current docs

**Research date:** 2026/04/16
**Valid until:** 2026/05/16 (30 days - standard library versions change slowly)
