# Technology Stack | 技术栈

**Project:** Design Doc Review Expert Agent
**项目：** 设计文档审查专家 Agent
**Researched:** 2026/04/14
**Updated:** 2026/04/16 (LLM switch: Claude → MiniMax)
**Confidence:** LOW-MEDIUM (web search unavailable; verify versions before use)

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

### LLM Choices | LLM 选择

| Provider | Model | Pros | Cons | Document Review Fit |
|----------|-------|------|------|---------------------|
| **MiniMax** | M2.7 / M2.5 | OpenAI-compatible, multimodal (images), strong Chinese/English, free tier | Limited to MiniMax ecosystem | **Best for this project - RECOMMENDED** |
| **Anthropic** | Claude 3.5 Sonnet | Excellent reasoning, vision built-in | Requires API key, cost | If MiniMax insufficient |
| **OpenAI** | GPT-4o | Multimodal natively, good all-around | Higher cost, may be overkill | Good for prototyping |

**Recommendation:** **MiniMax M2.7** because:
1. OpenAI-compatible API → `langchain-openai` with `base_url` config
2. Multimodal support (image understanding) confirmed
3. Strong Chinese/English bilingual support (国产优势)
4. Token Plan with free tier
5. No Claude API key needed

**If MiniMax vision insufficient:** Fall back to Claude Vision (separate image pipeline).

**Verification:**
```bash
pip show langchain-openai  # For MiniMax (OpenAI-compatible)
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
# Using uv (fast, Rust-based package manager)
uv sync

# Or add dependencies
uv add langchain langgraph langchain-openai langchain-community
uv add chromadb sentence-transformers
uv add unstructured pdfplumber Pillow

# Optional for image handling
uv add torch torchvision  # For CLIP if needed

# Verify versions
uv pip show langchain langgraph chromadb | grep -E "^Name:|^Version:"
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
2. **MiniMax M2.7** (API) - OpenAI-compatible, multimodal, strong bilingual
3. **bge-m3** (local) - bilingual embeddings via sentence-transformers
4. **LangChain + LangGraph** - as specified in project constraints

**Defer to Phase 2:**
- Pinecone (only if Chroma insufficient)
- Claude Vision (only if MiniMax vision inadequate for prototypes)
- CLIP embeddings (only if image similarity search needed)

## Confidence Assessment | 置信度评估

| Component | Confidence | Notes |
|-----------|------------|-------|
| LangChain/LangGraph roles | MEDIUM | Well-established patterns, official docs exist |
| Vector DB comparison | LOW | Web search unavailable; recommend verification |
| LLM recommendations | MEDIUM | MiniMax confirmed multimodal via platform docs |
| Chroma recommendation | MEDIUM | Known to be learning-friendly; verify scalability |
| bge-m3 for bilingual | LOW | Training data; verify with benchmarks for Chinese |

## Verification Checklist Before Implementation | 实施前验证清单

```bash
# Check current versions (required before starting)
uv pip show langchain langgraph chromadb | grep -E "^Name:|^Version:"
uv pip show sentence-transformers | grep Version

# Verify LangChain + LangGraph compatibility
# (Should work together, but verify on your env)
python -c "import langchain; import langgraph; print('OK')"
```

## Sources | 参考资料

- **Confidence: LOW** (web search unavailable; based on training data)
- LangChain docs: https://python.langchain.com (verify current)
- LangGraph docs: https://langchain-ai.github.io/langgraph/ (verify current)
- Chroma docs: https://docs.trychroma.com (verify current)
- bge-m3: Hugging Face model card (verify multilingual benchmarks)
- MiniMax API: https://platform.minimaxi.com/docs (verify current models)

## Gaps to Address | 待解决问题

- [ ] Verify current LangChain/LangGraph versions (breaking changes common)
- [ ] Confirm bge-m3 performance vs voyage-multilingual for Chinese/English
- [ ] Test MiniMax M2.7 vision vs Claude Vision for prototype review
- [ ] Test Chroma at 100+ page scale (may need Qdrant migration path)
