# Technology Stack

**Project:** Design Doc Review Expert Agent
**Researched:** 2026/04/14
**Confidence:** LOW-MEDIUM (web search unavailable; verify versions with `npm show` before use)

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **LangChain** | ^0.3.x | RAG/Retrieval framework | Required per project constraints; strong retrieval abstractions |
| **LangGraph** | ^0.2.x | Workflow orchestration | Required per project constraints; superior for complex stateful workflows |
| **Python** | 3.11+ | Primary language | LangChain/LangGraph native; rich ML/embedding ecosystem |

**Rationale:** The project explicitly specifies LangChain + LangGraph. They are complementary: LangChain provides retrieval components (embeddings, vector stores, document loaders), while LangGraph handles the agentic workflow state machine. Do NOT choose between them - use both.

### Vector Database

| Technology | Purpose | Pros | Cons | Recommended For |
|------------|---------|------|------|-----------------|
| **Chroma** | Local vector DB | Zero setup, easy LocalAI integration, free, great for learning | Not production-scalable, single-node only | **Learning project - RECOMMENDED** |
| **Qdrant** | Vector search | Good performance, cloud or self-hosted, Rust-based | More complex setup than Chroma | When outgrowing Chroma |
| **Pinecone** | Managed vector DB | Fully managed, scalable, good SDK | Cost, vendor lock-in, less learning value | Production with team |
| **Weaviate** | Vector search | Good built-in modules, hybrid search | Resource-heavy | Complex multi-modal |

**Recommendation:** **Chroma** for learning project because:
1. Zero infrastructure complexity
2. Works locally without API keys
3. Python-native API aligns with LangChain
4. Sufficient for 100+ page knowledge base
5. Easy to swap later for Qdrant/Pinecone when scaling

**Verification command:**
```bash
pip show chromadb  # Check current version
```

### LLM Choices

| Provider | Model | Pros | Cons | Document Review Fit |
|----------|-------|------|------|---------------------|
| **Anthropic** | Claude 3.5 Sonnet | Excellent reasoning, cost-effective, strong instruction following | API cost (but lower than GPT-4) | **Best for structured review tasks** |
| **OpenAI** | GPT-4o | Multimodal natively (images), good all-around | Higher cost, may be overkill for text-only | Good if prototyping image review |
| **Local** | Llama 3.1 70B / Mixtral | Privacy, no API cost | Requires GPU, quality gap, setup complexity | Only if privacy critical |

**Recommendation:** **Claude 3.5 Sonnet** for this project because:
1. Best-in-class reasoning for compliance checking
2. Cost-effective for document review (not image-heavy at MVP)
3. Strong Chinese/English bilingual support
4. Lower cost than GPT-4o for text-first workloads
5. Easy migration path: keep API-based for learning

**If image review is primary concern:** Consider GPT-4o for native multimodal (no separate vision model needed).

**Verification:**
```bash
pip show langchain-anthropic  # Check LangChain integration version
```

### Embedding Models

| Model | Purpose | Why |
|-------|---------|-----|
| **text-embedding-3-small** | General text embedding | Good quality, low cost, OpenAI hosted |
| **bge-m3** | Bilingual (Chinese/English) | Specifically designed for multilingual, open source |
| **voyage-multilingual-2** | Multilingual retrieval | Optimized for RAG, supports 10+ languages |

**Recommendation:** **bge-m3** for bilingual requirements because:
1. Open source, no API cost for embeddings
2. Specifically trained for Chinese/English
3. Self-hostable (privacy + control)
4. Compatible with LangChain embedding interface

**Verification:**
```bash
pip show sentence-transformers  # For bge-m3
```

### Image Handling for Prototype Review

| Approach | Tool | Complexity | Notes |
|----------|------|------------|-------|
| **Multimodal LLM** | Claude 3.5 Sonnet (vision) / GPT-4o | Low | Direct image input, no embedding needed |
| **Image Embedding + RAG** | CLIP (OpenAI) / image-chroma | Medium | For similarity search across prototype database |
| **Visual Comparison** | Custom pipeline | High | Extract colors, layout, compare against design tokens |

**Recommendation for MVP:** Use **Claude 3.5 Sonnet with vision capability** because:
1. No separate image embedding pipeline needed
2. Natural language description of prototype issues
3. Integrated into existing LLM workflow
4. Lower complexity than building separate image RAG

**Advanced (Phase 2+):** Add CLIP-based image embedding for:
- Finding similar past prototypes
- Design consistency across screens
- Visual style clustering

### Supporting Libraries

| Library | Purpose | When to Use |
|---------|---------|-------------|
| **langchain-community** | Third-party integrations | Chroma, OpenAI, Anthropic loaders |
| **unstructured** | Document parsing | PDF, DOCX, PPTX ingestion |
| **pdfplumber** | PDF text extraction | Precise PDF text extraction |
| **Pillow** | Image processing | Color extraction, resize, format conversion |
| **fastapi** | API layer | If exposing agent as service later |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Vector DB | Chroma | Pinecone | Learning project = avoid vendor lock-in + costs |
| LLM | Claude 3.5 Sonnet | GPT-4o | Cost advantage for text-first; Claude better reasoning |
| Embedding | bge-m3 | OpenAI embeddings | Better bilingual support, no per-token cost |
| Image handling | Multimodal LLM | Separate CLIP | Simpler architecture for MVP |

## LangChain vs LangGraph for This Use Case

**Use LangChain for:**
- Document loading and splitting
- Embedding generation
- Vector store operations
- Retrieval chains (RAG)
- Prompt templates

**Use LangGraph for:**
- Multi-step review workflow state machine
- Conditional branching (e.g., if PRD issues > threshold, escalate)
- Human-in-the-loop checkpoints
- Complex agentic loops with memory
- Orchestrating multiple review types (PRD + prototype)

**Key insight:** LangGraph replaces LangChain's AgentExecutor. For this project, the review workflow is inherently stateful (collect findings, aggregate, generate report) - this is LangGraph's sweet spot.

**Typical architecture:**
```
LangChain Components          LangGraph Workflow
├── Document Loaders     -->   State: {prd_doc, prototype_img, findings[]}
├── Text Splitters            Nodes: Load -> Extract -> Review -> Report
├── Embeddings                
├── VectorStore (Chroma)  -->  Retrieval: Find relevant design standards
└── Prompt Templates          Edges: Conditional routing based on findings
```

## Installation

```bash
# Core dependencies
pip install langchain langgraph langchain-anthropic langchain-community
pip install chromadb sentence-transformers
pip install unstructured pdfplumber Pillow

# Optional for image handling
pip install torch torchvision  # For CLIP if needed
pip install anthropic  # Direct Claude API

# Verify versions
pip show langchain langgraph chromadb | grep -E "^Name:|^Version:"
```

## Architecture Pattern for Learning

```
                    ┌─────────────────┐
                    │   Input Layer   │
                    │ PRD + Prototype │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   LangChain     │
                    │ Document/Image  │
                    │   Processing    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────────┐     │    ┌────────▼────────┐
     │ Vector Store    │     │    │ Multimodal LLM  │
     │ (Chroma + bge)  │     │    │ (Claude vision) │
     └────────┬────────┘     │    └────────┬────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │    LangGraph    │
                    │   Review        │
                    │   Workflow      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Compliance    │
                    │   Report        │
                    │   (Bilingual)   │
                    └─────────────────┘
```

## Phase 1 Specific Recommendations

**Start with these exact technologies:**
1. **Chroma** (local) - no setup, free, sufficient for 100 pages
2. **Claude 3.5 Sonnet** (API) - best reasoning, good pricing
3. **bge-m3** (local) - bilingual embeddings via sentence-transformers
4. **LangChain + LangGraph** - as specified in project constraints

**Defer to Phase 2:**
- Pinecone (only if Chroma insufficient)
- GPT-4o (only if Claude vision inadequate for prototypes)
- CLIP embeddings (only if image similarity search needed)

## Confidence Assessment

| Component | Confidence | Notes |
|-----------|------------|-------|
| LangChain/LangGraph roles | MEDIUM | Well-established patterns, official docs exist |
| Vector DB comparison | LOW | Web search unavailable; recommend verification |
| LLM recommendations | MEDIUM | Claude/GPT known quantities; verify current pricing |
| Chroma recommendation | MEDIUM | Known to be learning-friendly; verify scalability |
| bge-m3 for bilingual | LOW | Training data; verify with benchmarks for Chinese |

## Verification Checklist Before Implementation

```bash
# Check current versions (required before starting)
npm show langchain version
npm show langgraph version  
npm show chromadb version
pip show anthropic | grep Version
pip show sentence-transformers | grep Version

# Verify LangChain + LangGraph compatibility
# (Should work together, but verify on your env)
pip install langchain && pip install langgraph
python -c "import langchain; import langgraph; print('OK')"
```

## Sources

- **Confidence: LOW** (web search unavailable; based on training data)
- LangChain docs: https://python.langchain.com (verify current)
- LangGraph docs: https://langchain-ai.github.io/langgraph/ (verify current)
- Chroma docs: https://docs.trychroma.com (verify current)
- bge-m3: Hugging Face model card (verify multilingual benchmarks)
- Anthropic Claude: https://docs.anthropic.com (verify current pricing/models)

## Gaps to Address

- [ ] Verify current LangChain/LangGraph versions (breaking changes common)
- [ ] Confirm bge-m3 performance vs voyage-multilingual for Chinese/English
- [ ] Benchmark Claude 3.5 Sonnet vision vs GPT-4o for prototype review
- [ ] Test Chroma at 100+ page scale (may need Qdrant migration path)
