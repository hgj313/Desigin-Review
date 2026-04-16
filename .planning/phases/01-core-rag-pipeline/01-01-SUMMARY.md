---
phase: "01"
plan: "01"
subsystem: ingestion
tags: [langchain, bge-m3, document-loading, chunking, embeddings]

# Dependency graph
requires: []
provides:
  - Document loaders (PDF, MD, HTML, DOCX support)
  - Structural text chunker with header preservation
  - bge-m3 embedding wrapper (1024-dim, batch_size=64)
affects: [phase-01-02, phase-01-03]

# Tech tracking
tech-stack:
  added: [langchain-core, langchain-community, langchain-text-splitters, sentence-transformers, unstructured, pdfplumber, python-docx, markdown]
  patterns: [header-aware chunking, metadata preservation, LangChain Embeddings interface]

key-files:
  created: [src/ingestion/loaders.py, src/ingestion/chunker.py, src/embeddings/bge_m3.py]
  modified: [pyproject.toml]

key-decisions:
  - "Used langchain_core.documents.Document instead of deprecated langchain.schema.Document"
  - "Used langchain_text_splitters.RecursiveCharacterTextSplitter (correct package)"
  - "Created pyproject.toml with hatchling build and [tool.hatch.build.targets.wheel] packages = ['src'] to fix wheel build error"

patterns-established:
  - "Pattern: Format-specific loader selection based on file extension"
  - "Pattern: Header-aware splitting preserves section hierarchy in metadata"
  - "Pattern: Token estimation using char_count // 4 for chunk sizing"

requirements-completed: ["RAG-01", "RAG-02", "RAG-03", "RAG-06"]

# Metrics
duration: 9min
completed: 2026-04-16T07:24:28Z
---

# Phase 01 Plan 01: Document Ingestion Foundation Summary

**Document loaders for multi-format support, structural chunker with header hierarchy preservation, and bge-m3 embedding wrapper for bilingual retrieval**

## Performance

- **Duration:** 9 min
- **Started:** 2026-04-16T07:15:18Z
- **Completed:** 2026-04-16T07:24:28Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Created `src/ingestion/loaders.py` with multi-format document loading (PDF, Markdown, HTML, DOCX)
- Created `src/ingestion/chunker.py` with header-aware structural splitting preserving section hierarchy
- Created `src/embeddings/bge_m3.py` with LangChain-compatible bge-m3 embedding wrapper
- Fixed langchain API changes: `langchain.schema.Document` -> `langchain_core.documents.Document`
- Fixed langchain API changes: `langchain.text_splitter` -> `langchain_text_splitters`
- Created `pyproject.toml` with proper hatchling configuration to enable uv sync

## Task Commits

Each task was committed atomically:

1. **Task 1: Document loaders module** - `e8bb192` (feat)
2. **Task 2: Structural chunker module** - `aef7fa7` (feat)
3. **Task 3: bge-m3 embedding wrapper** - `f4daf2c` (feat)

## Files Created/Modified

- `src/ingestion/loaders.py` - Multi-format document loading (PDF via PDFPlumberLoader, MD/HTML/DOCX via UnstructuredFileLoader)
- `src/ingestion/chunker.py` - Structural text splitter with header preservation, chunk_size=600, overlap=90
- `src/embeddings/bge_m3.py` - bge-m3 embedding wrapper implementing LangChain Embeddings interface
- `pyproject.toml` - Project configuration with dependencies and hatchling wheel configuration

## Decisions Made

- Used `langchain_core.documents.Document` instead of deprecated `langchain.schema.Document`
- Used `langchain_text_splitters.RecursiveCharacterTextSplitter` (correct package for v0.3.x)
- Created `pyproject.toml` with `[tool.hatch.build.targets.wheel]` to fix hatchling wheel build error
- All modules use `__all__` export lists for explicit public API

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **langchain API changes**: `langchain.schema.Document` was deprecated in LangChain 1.x. Fixed by using `langchain_core.documents.Document` instead.
- **langchain text_splitter location**: `langchain.text_splitter` module moved to separate package `langchain_text_splitters`. Fixed by using correct import.
- **hatchling wheel build error**: `pyproject.toml` without explicit package configuration caused hatchling to fail with "Unable to determine which files to ship". Fixed by adding `[tool.hatch.build.targets.wheel]` with `packages = ["src"]`.

## Next Phase Readiness

All three modules are ready for integration in Plan 02 (vector store setup) and Plan 03 (workflow orchestration):
- Loaders can feed documents into the chunker
- Chunker produces chunks with proper metadata for embedding
- Embeddings wrapper is ready to generate vectors for the vector store

---
*Phase: 01-core-rag-pipeline*
*Completed: 2026-04-16*
