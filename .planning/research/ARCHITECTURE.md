# Architecture Patterns: RAG-Powered Agent System | 架构模式：RAG驱动的 Agent 系统

**Project:** Design Doc Review Expert Agent
**项目：** 设计文档审查专家 Agent
**Researched:** 2026/04/14
**Updated:** 2026/04/16 (LLM switch: Claude → MiniMax)
**Confidence:** MEDIUM-HIGH (standard RAG patterns: HIGH; LangChain/LangGraph specifics: MEDIUM - web search blocked)

## Executive Summary

A RAG-powered agent system for design document review consists of two main subsystems: a **RAG Pipeline** (ingestion side) and an **Agent Workflow** (query/response side). LangChain provides the retrieval and embedding infrastructure; LangGraph provides stateful workflow orchestration with cycles and human-in-the-loop checkpoints.

The recommended architecture separates concerns clearly:
- **Ingestion Pipeline**: Document processing, chunking, embedding, vector storage
- **Agent Workflow**: Query routing, retrieval, multi-dimensional review coordination, report generation
- **State Management**: LangGraph state carries context through review stages

---

## Architecture Overview

```
+------------------------------------------------------------------+
|                        DESIGN DOC REVIEW AGENT                    |
+------------------------------------------------------------------+
|                                                                   |
|  +-------------------+         +-------------------+              |
|  |   INGESTION       |         |   AGENT WORKFLOW   |              |
|  |   PIPELINE         |         |                    |              |
|  +-------------------+         +-------------------+              |
|           |                            ^                          |
|           v                            |                          |
|  +-------------------+         +-------------------+              |
|  |  VECTOR STORE     |<------->|  LangGraph        |              |
|  |  (Knowledge Base) |         |  Orchestrator     |              |
|  +-------------------+         +-------------------+              |
|                                       ^                            |
|                                       |                            |
|  +-------------------+         +-------------------+              |
|  |  LLM (Reasoning)  |         |  Review Nodes     |              |
|  |                   |         |  - Structure      |              |
|  |                   |         |  - Terminology    |              |
|  |                   |         |  - Layout         |              |
|  |                   |         |  - Accessibility  |              |
|  +-------------------+         +-------------------+              |
|                                                                   |
+------------------------------------------------------------------+
```

---

## Component Boundaries

### 1. Ingestion Pipeline Components

| Component | Responsibility | Input | Output | Technology Options |
|-----------|----------------|-------|--------|-------------------|
| **Document Loader** | Load raw documents (PDF, DOCX, MD) | File path/URL | Raw text + metadata | LangChain document loaders, Unstructured |
| **Text Splitter** | Chunk documents into semantic units | Raw text | Chunks with metadata | RecursiveCharacterTextSplitter, TokenTextSplitter |
| **Embedding Model** | Convert text to vectors | Text chunks | 1536-dim vectors (OpenAI) or 384-1024 (other) | OpenAI embeddings, sentence-transformers, BGE |
| **Vector Store** | Store and retrieve embeddings | Vectors + chunks | Retrieved chunks | Chroma (local), Pinecone, Qdrant, FAISS |

### 2. Agent Workflow Components

| Component | Responsibility | Input | Output |
|-----------|---------------|-------|--------|
| **Query Router** | Route user query to appropriate review dimension(s) | User query | Selected review dimensions |
| **Retrieval Node** | Fetch relevant knowledge base chunks | Query + dimensions | Context chunks |
| **Review Nodes** | Execute dimension-specific review logic | Context + document | Finding arrays |
| **Synthesis Node** | Aggregate findings into compliance report | All findings | Final report |

### 3. LangGraph State Schema

```python
class ReviewState(TypedDict):
    # User input
    prd_content: str
    prototype_images: list[str]  # Base64 or URLs

    # Intermediate results
    retrieved_context: dict[str, list[Document]]  # keyed by dimension
    structure_findings: list[Finding]
    terminology_findings: list[Finding]
    layout_findings: list[Finding]
    accessibility_findings: list[Finding]

    # Output
    compliance_report: str
    severity_summary: dict[str, int]
```

---

## Data Flow

### Ingestion Flow (One-Time Setup)

```
Design Standards Docs
        |
        v
Document Loader --> Raw Text + Metadata
        |
        v
Text Splitter --> Chunks (500-1000 tokens each, 20% overlap)
        |
        v
Embedding Model --> Vectors (1536-dim for OpenAI text-embedding-3-small)
        |
        v
Vector Store --> Indexed chunks with metadata filters
```

**Key decisions for your 100+ page knowledge base:**
- **Chunk size**: 500-800 tokens with 15-20% overlap
- **Embedding model**: `text-embedding-3-small` (cost-effective, 1536 dimensions) or `bge-m3` (multilingual, 1024 dimensions)
- **Index strategy**: Create separate collections per review dimension (structure, terminology, layout, accessibility) for targeted retrieval

### Agent Query Flow

```
User Query (PRD text + prototype images)
        |
        v
+---------------------+
|  LangGraph Agent    |
+---------------------+
        |
        v
Query Router --> Identifies which dimensions to check
        |
        v
Retrieval --> Fetches dimension-specific context from vector store
        |
        v
Review Nodes (parallel) --> Structure, Terminology, Layout, Accessibility
        |                  |
        |                  +--> Each node: Retrieve context --> LLM analyze --> Findings
        |
        v
Synthesis Node --> Aggregate findings, generate compliance report
        |
        v
Compliance Report (Chinese + English)
```

---

## LangChain and LangGraph Integration

**Relationship: Complementary, not competing**

| Concern | Technology | Role |
|---------|------------|------|
| Retrieval infrastructure | LangChain | Document loaders, text splitters, embedding models, vector store clients |
| Embeddings & vector operations | LangChain | `Embeddings`, `VectorStore` abstractions |
| Workflow orchestration | LangGraph | State management, node routing, cycles, checkpoints |
| LLM calls | Both | LangChain `ChatModel`, or directly via LangGraph nodes |
| Prompt templates | LangChain | `PromptTemplate`, `ChatPromptTemplate` |

### Integration Pattern

```python
# LangGraph defines the workflow
from langgraph.graph import StateGraph, END

workflow = StateGraph(ReviewState)

# Add nodes - each node can use LangChain components internally
workflow.add_node("route_query", route_query_node)
workflow.add_node("retrieve", retrieval_node)  # Uses LangChain vector store
workflow.add_node("review_structure", structure_review_node)  # Uses LangChain LLM
workflow.add_node("review_terminology", terminology_review_node)
workflow.add_node("review_layout", layout_review_node)
workflow.add_node("review_accessibility", accessibility_review_node)
workflow.add_node("synthesize", synthesis_node)

# Define edges
workflow.add_edge("route_query", "retrieve")
workflow.add_edge("retrieve", "review_structure")
workflow.add_edge("review_structure", "review_terminology")
workflow.add_edge("review_terminology", "review_layout")
workflow.add_edge("review_layout", "review_accessibility")
workflow.add_edge("review_accessibility", "synthesize")
workflow.add_edge("synthesize", END)

# Compile with LangChain components for LLM/embedding
app = workflow.compile()
```

### Key Integration Points

1. **Vector Store**: LangChain's `VectorStore` abstraction wraps Chroma, Pinecone, etc.
   ```python
   from langchain_community.vectorstores import Chroma
   vectorstore = Chroma(embedding_function=embeddings)
   ```

2. **LLM in Nodes**: Each review node uses LangChain's `ChatModel` for analysis
   ```python
   from langchain_openai import ChatOpenAI
   llm = ChatOpenAI(model="gpt-4o")
   ```

3. **Prompt Templates**: LangChain prompts used within LangGraph nodes
   ```python
   from langchain.prompts import ChatPromptTemplate
   structure_prompt = ChatPromptTemplate.from_messages([...])
   ```

---

## Image Prototype Handling

### Pipeline for Visual Review

Images require a separate processing path from text:

```
Prototype Images (PNG/JPG)
        |
        v
Image Encoder --> Vision-enabled LLM or specialized VLM
        |
        v
Vision Analysis Node --> Extract layout, color, typography findings
        |
        v
Findings normalized to same schema as text reviews
```

### Options for Image Processing | 图像处理选项

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **MiniMax Image Understanding** | OpenAI-compatible, multimodal, free tier | Limited to MiniMax ecosystem | **Best for this project** |
| **Claude Vision** | High quality, no extra infrastructure | Requires API key | If MiniMax insufficient |
| **LLaVA + open-source** | Local, no API cost | Lower quality | Future phase |
| **GPT-4V** | Good quality, well-documented | Higher cost | Alternative |

### Integration with Review Workflow

```python
# Vision node in LangGraph
def review_layout_node(state: ReviewState) -> ReviewState:
    prototype_images = state["prototype_images"]

    findings = []
    for image_data in prototype_images:
        analysis = vision_llm.invoke([
            {"type": "image_url", "image_url": image_data},
            {"type": "text", "text": "Analyze layout against design standards..."}
        ])
        findings.append(parse_layout_findings(analysis))

    return {"layout_findings": findings}
```

---

## Multi-Dimensional Review Coordination

### Review Dimensions

| Dimension | Focus | Knowledge Base Queries |
|-----------|-------|----------------------|
| **Structure** | PRD organization, completeness, section flow | Design standards for PRD templates, required sections |
| **Terminology** | Consistent use of design terms | Glossary of design terms, approved terminology list |
| **Layout** | Visual hierarchy, spacing, alignment (from images) | Layout specifications, grid systems |
| **Accessibility** | WCAG compliance, contrast, font sizes | Accessibility guidelines, color contrast requirements |

### Coordination Patterns

**Pattern 1: Sequential (Simple, Clear Dependencies)**
```
Structure --> Terminology --> Layout --> Accessibility --> Synthesize
```
- Use when each dimension depends on previous findings
- Example: Terminology review may flag missing sections found in structure review

**Pattern 2: Parallel + Merge (Fast, Independent Dimensions)**
```
                    +--> Structure --+
                    |                |
Query --> Retrieve -+--> Terminology -+--> Synthesize
                    |                |
                    +--> Layout ----+
                    |
                    +--> Accessibility
```
- Use when dimensions are independent
- LangGraph `Send` for fan-out, collects results before synthesize

**Pattern 3: Conditional (Routing-Based)**
```
Query --> Route --> [Full Review] or [Quick Review] or [Specific Dimension Only]
```
- Use when user specifies scope
- Query router decides which paths to execute

### Recommendation for Design Doc Review

**Use Pattern 2 (Parallel) for initial build** because:
- All dimensions are independent in review logic
- Faster execution (parallel LLM calls)
- Easy to add/remove dimensions

```python
# Fan-out pattern in LangGraph
from langgraph.constants import Send

def retrieve_node(state: ReviewState) -> list[Send]:
    return [
        Send("review_structure", {"context": state["retrieved_context"]["structure"]}),
        Send("review_terminology", {"context": state["retrieved_context"]["terminology"]}),
        Send("review_layout", {"context": state["retrieved_context"]["layout"]}),
        Send("review_accessibility", {"context": state["retrieved_context"]["accessibility"]}),
    ]

workflow.add_node("retrieve", retrieve_node)
workflow.add_edge("retrieve", [review_nodes])  # Fan-out to all review nodes
```

---

## Build Order Implications

### Phase 1: Core RAG Pipeline (No Agent Yet)

**Why first:** Establishes the knowledge base foundation that agent depends on

| Step | Component | Dependencies | Validation |
|------|-----------|--------------|------------|
| 1.1 | Document loader + text splitter | None | Load 10 sample pages, verify chunks |
| 1.2 | Embedding pipeline | 1.1 | Verify vector quality, similarity search |
| 1.3 | Vector store setup | 1.2 | Query returns relevant context |
| 1.4 | Knowledge base population | 1.3 | 100+ pages indexed, retrieval < 2s |

### Phase 2: Single-Dimension Agent (Structure Review Only)

**Why second:** Validate agent loop before multi-dimensional complexity

| Step | Component | Dependencies | Validation |
|------|-----------|--------------|------------|
| 2.1 | Basic LangGraph workflow | Phase 1 | Graph compiles, state flows |
| 2.2 | Single review node (structure) | 2.1 | LLM returns structured findings |
| 2.3 | Simple report generation | 2.2 | Report contains findings + suggestions |

### Phase 3: Multi-Dimensional Extension

**Why third:** Extend proven single-dimension to full coverage

| Step | Component | Dependencies | Validation |
|------|-----------|--------------|------------|
| 3.1 | Add terminology node | Phase 2 | Parallel execution works |
| 3.2 | Add layout node (with vision) | 3.1 | Image processing pipeline |
| 3.3 | Add accessibility node | 3.2 | All four dimensions reporting |
| 3.4 | Synthesis node refinement | 3.3 | Bilingual report generation |

### Phase 4: Polish and Integration

**Why last:** Features that depend on full system being working

| Step | Component | Dependencies | Validation |
|------|-----------|--------------|------------|
| 4.1 | Query routing optimization | Phase 3 | Routes correctly to dimensions |
| 4.2 | Error handling and retry | 4.1 | Graceful degradation |
| 4.3 | Performance optimization | 4.2 | < 30s end-to-end review |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Monolithic Agent
**What:** One LLM call does everything (load docs, review, report)
**Why bad:** No retrieval grounding, hallucinations, undebuggable
**Instead:** RAG + focused review nodes

### Anti-Pattern 2: Skipping Vector Store Indexing Strategy
**What:** Single index for all content, filter at query time
**Why bad:** 100+ pages with mixed content degrades retrieval precision
**Instead:** Separate collections or metadata tagging per dimension

### Anti-Pattern 3: Synchronous Sequential Processing
**What:** Each review dimension waits for previous to complete
**Why bad:** 4x slower than parallel, no parallel LLM utilization
**Instead:** LangGraph fan-out with `Send`

### Anti-Pattern 4: Hardcoding Review Criteria
**What:** Embedding standards directly in LLM prompts
**Why bad:** Standards change, hard to maintain, no versioning
**Instead:** Standards in vector store, retrieved at query time

---

## Scalability Considerations

| Scale | 100 Pages | 1,000 Pages | 10,000 Pages |
|-------|-----------|-------------|-------------|
| **Chunks** | ~200-500 | ~2,000-5,000 | ~20,000-50,000 |
| **Vector DB** | Chroma (local) fine | Chroma or Qdrant | Pinecone or Qdrant (cloud) |
| **Retrieval latency** | < 500ms | < 1s | < 2s with proper indexing |
| **LLM calls per review** | 4-8 | 4-8 | 4-8 (no change) |

**For learning project:** Start with Chroma (local) + 100 pages, migrate to cloud vector DB when needed.

---

## Key Architecture Decisions Summary | 关键架构决策总结

| Decision | Recommended | Rationale |
|----------|-------------|-----------|
| **Workflow orchestration** | LangGraph | Stateful, supports cycles, better than LangChain's LinearAgent |
| **Retrieval infrastructure** | LangChain | Mature abstractions, easy vector store integration |
| **Review execution** | Parallel fan-out | Independent dimensions, faster |
| **Image handling** | MiniMax Image Understanding | OpenAI-compatible, multimodal, free tier |
| **Vector store** | Chroma (initial) | Local, easy setup, learning-friendly |
| **State management** | LangGraph `TypedDict` | Type-safe, explicit, debuggable |
| **LLM** | MiniMax M2.7 | OpenAI-compatible API, no Claude key needed |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| RAG Pipeline Architecture | HIGH | Standard patterns, widely documented |
| LangGraph Workflow Patterns | HIGH | Well-documented in official tutorials |
| LangChain Integration Points | MEDIUM | Official docs, but web search blocked for verification |
| Image Processing Pipeline | MEDIUM | Standard multimodal patterns, VLM options may change |
| Build Order | HIGH | Proven phase structure for RAG projects |

---

## Sources | 参考资料

- LangGraph Documentation: https://python.langchain.com/docs/langgraph (official, but fetch blocked)
- LangChain RAG Tutorials: https://python.langchain.com/docs/tutorials/rag/ (official, but fetch blocked)
- Agentic RAG Patterns: https://python.langchain.com/docs/tutorials/agentic_rag/ (official, but fetch blocked)
- Multi-modal RAG Survey (2024): Academic patterns, not vendor-specific
- MiniMax API: https://platform.minimaxi.com/docs (verified 2026/04/16 - supports image understanding)

**Note:** Web search was blocked during research. All LangChain/LangGraph specifics are based on training data (6-18 months stale). Recommend verifying integration patterns against current official docs before implementation.
