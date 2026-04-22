# ROADMAP.md - Design Doc Review Expert Agent | 项目路线图

**Project:** AI-Powered Design Document Review System
**项目：** AI 驱动的设计文档审查系统
**Created:** 2026/04/14
**Granularity:** Coarse (4 phases)
**Parallelization:** Enabled

---

## Overview

A RAG-powered agent that reviews PRD documents and prototype images against company design standards, producing bilingual compliance reports. Built with LangChain + LangGraph, using MiniMax M2.7 for reasoning (OpenAI-compatible, multimodal) and Chroma for vector storage.

**Core Value:** Automate design compliance review at scale. Replace manual, inconsistent reviews with consistent, scalable AI-powered validation.

---

## Phases

- [ ] **Phase 1: Core RAG Pipeline** - Knowledge base foundation with document ingestion, structural chunking, and vector storage
- [ ] **Phase 2: Single-Dimension Agent** - PRD structure validation and bilingual compliance report generation
- [ ] **Phase 3: Multi-Dimensional Extension** - Prototype image review with parallel fan-out across all review dimensions
- [ ] **Phase 4: Polish and Integration** - Versioning, error handling, and workflow cycles

---

## Phase Details

### Phase 1: Core RAG Pipeline

**Goal:** Establish the knowledge base foundation that all subsequent phases depend on

**Depends on:** None (first phase)

**Requirements:** RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, RAG-06, AGT-01, AGT-03

**Success Criteria** (what must be TRUE when phase completes):
1. User can ingest 100+ pages of design standards documents (Markdown/PDF) into Chroma vector store
2. System uses structural chunking that preserves document context (headers, list items)
3. System uses bge-m3 embeddings for bilingual Chinese/English retrieval
4. User can query knowledge base with natural language and retrieve relevant standards
5. System supports hybrid retrieval (BM25 + vector) for precision
6. Retrieved standards include source attribution (document name, section, version)
7. System uses LangGraph for workflow orchestration (not pure LangChain chains)
8. Agent explicitly states "Standard Not Found" when knowledge base has no relevant guidance

**Plans:** TBD

**UI hint:** no

---

### Phase 2: Single-Dimension Agent

**Goal:** Validate agent loop and LangGraph integration with PRD structure validation and compliance reporting

**Depends on:** Phase 1

**Requirements:** PRD-01, PRD-02, PRD-03, PRD-04, RPT-01, RPT-02, RPT-03, RPT-04, RPT-05

**Success Criteria** (what must be TRUE when phase completes):
1. System validates PRD structure (Overview, User Stories, Acceptance Criteria presence)
2. System checks terminology consistency against design standards glossary
3. System validates completeness (all required sections present, no placeholder content)
4. System checks basic formatting (heading hierarchy, bullet consistency)
5. System generates review report with categorized issues (Structure, Terminology, Layout, Accessibility)
6. Each issue includes severity level (Critical / Major / Minor / Suggestion)
7. Each issue includes exact location reference (line number, section name, or image coordinates)
8. System provides specific improvement suggestions for each issue
9. All outputs are bilingual (Chinese and English)

**Plans:** TBD

**UI hint:** no

---

### Phase 3: Multi-Dimensional Extension

**Goal:** Extend proven single-dimension agent to full prototype image review with parallel execution

**Depends on:** Phase 2

**Requirements:** PRD-05, IMG-01, IMG-02, IMG-03, IMG-04, IMG-05, IMG-06, AGT-02, AGT-04, AGT-05

**Success Criteria** (what must be TRUE when phase completes):
1. System detects unstated assumptions in requirements (vague language like "as needed", "etc.")
2. System extracts color palette from prototype images
3. System validates color usage against brand/design token standards from knowledge base
4. System analyzes typography hierarchy (heading vs body vs caption styles)
5. System validates spacing and grid alignment against 8pt/4pt grid standards
6. System performs accessibility contrast checking (WCAG AA compliance)
7. System uses Claude Vision for image analysis (no separate OCR pipeline)
8. Review dimensions execute in parallel (Structure, Terminology, Layout, Accessibility fan-out)
9. System uses LangGraph cycles for re-retrieval when initial findings are inconclusive
10. Knowledge base stores version metadata (version_id, effective_date) to prevent stale standards

**Plans:** TBD

**UI hint:** no

---

### Phase 4: Polish and Integration

**Goal:** Ensure robust, production-ready workflow with error handling, versioning, and cycles

**Depends on:** Phase 3

**Requirements:** None (cross-cutting polish not tied to specific requirements)

**Success Criteria** (what must be TRUE when phase completes):
1. Agent handles ambiguous queries gracefully with structured error responses
2. System prevents hallucination through confidence thresholds and explicit "not found" responses
3. Knowledge base versioning prevents stale standards from being applied
4. LangGraph cycles enable re-retrieval when initial findings are inconclusive
5. End-to-end workflow runs without deadlocks or infinite loops

**Plans:** 3 plans

**Plan list:**
- [ ] 04-01-PLAN.md — Error handling: centralized error handler with retry logic (D-25)
- [ ] 04-02-PLAN.md — Convergence check: findings stability detection across iterations (D-26)
- [ ] 04-03-PLAN.md — Unified workflow: review() entry point, ReviewResponse, confidence zones (D-27 to D-33)

**UI hint:** no

---

## Coverage Validation

### Requirement Mapping

| Phase | Requirements |
|-------|--------------|
| Phase 1: Core RAG Pipeline | RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, RAG-06, AGT-01, AGT-03 |
| Phase 2: Single-Dimension Agent | PRD-01, PRD-02, PRD-03, PRD-04, RPT-01, RPT-02, RPT-03, RPT-04, RPT-05 |
| Phase 3: Multi-Dimensional Extension | PRD-05, IMG-01, IMG-02, IMG-03, IMG-04, IMG-05, IMG-06, AGT-02, AGT-04, AGT-05 |
| Phase 4: Polish and Integration | None (cross-cutting) |

### Coverage Summary

| Metric | Value |
|--------|-------|
| Total v1 requirements | 22 |
| Mapped to phases | 22 |
| Unmapped | 0 |
| Phases | 4 |

### Traceability Matrix

| Requirement | Phase | Status |
|-------------|-------|--------|
| RAG-01 | Phase 1 | Pending |
| RAG-02 | Phase 1 | Pending |
| RAG-03 | Phase 1 | Pending |
| RAG-04 | Phase 1 | Pending |
| RAG-05 | Phase 1 | Pending |
| RAG-06 | Phase 1 | Pending |
| AGT-01 | Phase 1 | Pending |
| AGT-03 | Phase 1 | Pending |
| PRD-01 | Phase 2 | Pending |
| PRD-02 | Phase 2 | Pending |
| PRD-03 | Phase 2 | Pending |
| PRD-04 | Phase 2 | Pending |
| RPT-01 | Phase 2 | Pending |
| RPT-02 | Phase 2 | Pending |
| RPT-03 | Phase 2 | Pending |
| RPT-04 | Phase 2 | Pending |
| RPT-05 | Phase 2 | Pending |
| PRD-05 | Phase 3 | Pending |
| IMG-01 | Phase 3 | Pending |
| IMG-02 | Phase 3 | Pending |
| IMG-03 | Phase 3 | Pending |
| IMG-04 | Phase 3 | Pending |
| IMG-05 | Phase 3 | Pending |
| IMG-06 | Phase 3 | Pending |
| AGT-02 | Phase 3 | Pending |
| AGT-04 | Phase 3 | Pending |
| AGT-05 | Phase 3 | Pending |

**Verification:** All 22 v1 requirements mapped to exactly one phase. No orphans. No duplicates.

---

## Phase Dependencies

```
Phase 1 (Core RAG Pipeline)
    |
    v
Phase 2 (Single-Dimension Agent)
    |
    v
Phase 3 (Multi-Dimensional Extension)
    |
    v
Phase 4 (Polish and Integration)
```

---

*Last updated: 2026/04/17*
