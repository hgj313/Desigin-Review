# Research Summary: Design Doc Review Expert Agent

**Project:** AI-Powered Design Document Review System
**Synthesized:** 2026/04/14
**Confidence:** MEDIUM (based on established patterns; web search unavailable for verification)

---

## Executive Summary

This project builds an AI-powered design document review agent that combines RAG-based knowledge retrieval with a stateful multi-dimensional review workflow. The system reviews PRDs and prototypes against a company design standards knowledge base, producing bilingual compliance reports.

**Recommended approach:** Build a RAG-powered agent using LangChain for retrieval infrastructure and LangGraph for workflow orchestration. Use Claude 3.5 Sonnet for reasoning with Chroma as the local vector database and bge-m3 for bilingual embeddings. The agent performs reviews across four dimensions (Structure, Terminology, Layout, Accessibility) using parallel execution via LangGraph fan-out patterns.

**Key risks:** Hallucination when standards are silent (prevent with explicit "not found" responses), semantic chunking destroying document context (use structural chunking), embedding mismatch with domain vocabulary (fine-tune or use domain-adapted models), and iterative review needs being missed by linear pipelines (use LangGraph cycles).

**Phase ordering:** Phase 1 establishes the RAG pipeline foundation. Phase 2 builds a single-dimension agent to validate the loop. Phase 3 extends to multi-dimensional review. Phase 4 adds polish and integration.

---

## Key Findings

### Stack Recommendations (from STACK.md)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Framework** | LangChain ^0.3.x + LangGraph ^0.2.x | Required per project constraints; complementary |
| **Language** | Python 3.11+ | Native LangChain/LangGraph support |
| **Vector DB** | Chroma (local) | Zero setup, learning-friendly, swappable to Qdrant/Pinecone later |
| **LLM** | Claude 3.5 Sonnet | Best reasoning for compliance checking, cost-effective, strong bilingual |
| **Embeddings** | bge-m3 | Open source, bilingual Chinese/English, self-hostable |
| **Image Handling** | Claude Vision (multimodal) | No separate pipeline needed for MVP |

**Verification required before implementation:** Check current versions with `pip show langchain langgraph chromadb`.

### Feature Priorities (from FEATURES.md)

**Phase 1 MVP (Must-Have):**
1. PRD Structure Validation - most impactful, low complexity
2. Terminology Checking - clear value, simple implementation
3. Completeness Validation - essential for review workflow
4. RAG Semantic Search - core knowledge base capability
5. Color Palette Extraction - immediate visual feedback
6. Issue Categorization + Severity - core reporting
7. Bilingual Output - project requirement

**Phase 2+ (Should-Have Differentiators):**
- Cross-reference validation (high complexity, requires doc linking)
- Semantic completeness analysis (expensive LLM calls)
- Cross-screen pattern matching (needs multi-image handling)
- Trend tracking (requires historical data first)

**Avoid (Anti-Features):**
- Full grammar/spell checking (not the tool's job)
- Pixel-perfect comparison (too rigid)
- Automatic "fix" suggestions (overreach)

### Architecture Patterns (from ARCHITECTURE.md)

**Two main subsystems:**
1. **Ingestion Pipeline**: Document loading, structural chunking (500-800 tokens, 15-20% overlap), embedding generation, vector storage
2. **Agent Workflow**: Query routing, retrieval, multi-dimensional review coordination, report synthesis

**LangGraph State Schema:**
```python
ReviewState = {
    prd_content: str,
    prototype_images: list[str],
    retrieved_context: dict[str, list[Document]],  # keyed by dimension
    structure_findings: list[Finding],
    terminology_findings: list[Finding],
    layout_findings: list[Finding],
    accessibility_findings: list[Finding],
    compliance_report: str,
    severity_summary: dict[str, int]
}
```

**Execution pattern:** Parallel fan-out to all review dimensions (Structure, Terminology, Layout, Accessibility), then merge and synthesize. This is faster than sequential processing and dimensions are independent in review logic.

### Critical Pitfalls (from PITFALLS.md)

| Pitfall | Impact | Prevention |
|---------|--------|------------|
| **Semantic chunking destroys document context** | Agent retrieves fragments without conditionals | Use structural chunking (split on headers, list items, table rows) |
| **Embedding model mismatch with domain vocabulary** | Design terms like "8pt grid" retrieve poorly | Fine-tune on design corpus OR use domain-adapted models; test with domain terminology |
| **Agent hallucinates compliance when standards silent** | False positives, credibility damage | Explicit "Standard Not Found" response; confidence thresholds |
| **Linear pipeline misses iterative review needs** | Incomplete reviews, missed cross-dependencies | LangGraph cycles allowing re-retrieval based on partial findings |
| **Knowledge base staleness** | Outdated standards applied | Version metadata (version_id, effective_date, superseded_date) |

**Phase-specific warnings:**
- Phase 1: Invest in structural chunking early (re-chunking later is costly)
- Phase 2: Implement hallucination guardrails from day 1
- Phase 3: Design versioning schema before ingesting first doc
- Phase 4: Build visual validation layer for OCR (do not trust OCR alone)
- Phase 5: Create terminology glossary before bilingual output

---

## Implications for Roadmap

### Suggested Phase Structure

**Phase 1: Core RAG Pipeline**
- *Rationale:* Establishes the knowledge base foundation that all subsequent phases depend on. No agent can function without retrieval infrastructure.
- *Delivers:* Document loader, structural chunker, embedding pipeline, Chroma vector store, 100+ pages indexed
- *Features from FEATURES.md:* RAG Semantic Search (base)
- *Must avoid:* Pitfall 1 (semantic chunking) - use structural chunking from day one

**Phase 2: Single-Dimension Agent (Structure)**
- *Rationale:* Validate agent loop and LangGraph integration before adding multi-dimensional complexity.
- *Delivers:* Basic LangGraph workflow, single review node, simple report generation
- *Features from FEATURES.md:* PRD Structure Validation, Issue Categorization
- *Must avoid:* Pitfall 3 (hallucination) - implement "standard not found" guardrails

**Phase 3: Multi-Dimensional Extension**
- *Rationale:* Extend proven single-dimension to full coverage with parallel execution.
- *Delivers:* Terminology node, Layout node (with vision), Accessibility node, synthesis node, bilingual output
- *Features from FEATURES.md:* Terminology Checking, Completeness Validation, Color Palette Extraction, Bilingual Output
- *Must avoid:* Pitfall 4 (linear pipeline) - implement parallel fan-out pattern

**Phase 4: Polish and Integration**
- *Rationale:* Features that depend on full system working end-to-end.
- *Delivers:* Query routing optimization, error handling, performance tuning, versioning
- *Features from FEATURES.md:* Severity Scoring, Action Item Generation, Review Summary Dashboard
- *Must avoid:* Pitfall 5 (staleness) - implement knowledge base versioning

**Phase 5+ (Future):**
- Cross-reference validation, semantic completeness analysis, trend tracking, knowledge graph hybrid

### Research Flags

| Phase | Needs Deeper Research | Notes |
|-------|----------------------|-------|
| Phase 1 | Verify bge-m3 vs voyage-multilingual | Bilingual retrieval quality untested |
| Phase 2 | Confirm Claude 3.5 Sonnet reasoning quality | For compliance checking specifically |
| Phase 4 | Prototype OCR + vision validation | Image review pitfalls poorly documented |
| Cross-cutting | Current LangChain/LangGraph version compatibility | Breaking changes common |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| **Stack** | MEDIUM | Established patterns; web search unavailable for version verification |
| **Features** | MEDIUM | Well-documented patterns; specific taxonomy may vary by company |
| **Architecture** | MEDIUM-HIGH | Standard RAG patterns: HIGH; LangChain/LangGraph specifics: MEDIUM |
| **Pitfalls** | MEDIUM | Domain expertise; some gaps (Chinese RAG, knowledge base versioning) |

### Gaps to Address

- [ ] Verify current LangChain/LangGraph versions (breaking changes common in 0.3.x)
- [ ] Benchmark bge-m3 vs voyage-multilingual for Chinese/English bilingual retrieval
- [ ] Test Chroma at 100+ page scale (may need Qdrant migration path)
- [ ] Validate chunking strategy against actual design standards document structure
- [ ] Confirm Claude 3.5 Sonnet vision vs GPT-4o for prototype review
- [ ] Research PRD schema standards (Jira, Confluence templates)

---

## Sources

- STACK.md: Training data based recommendations (web search unavailable)
- FEATURES.md: Established best practices from code review tool ecosystem, Figma plugins, Frontitude patterns
- ARCHITECTURE.md: Standard RAG patterns, LangChain/LangGraph official documentation
- PITFALLS.md: Academic literature on RAG pitfalls, industry post-mortems, LangChain/LangGraph documentation

**Overall confidence: MEDIUM** - All recommendations based on established patterns but external verification was blocked. Recommend validating key decisions (stack versions, embedding model benchmarks, chunking strategy) before implementation.
