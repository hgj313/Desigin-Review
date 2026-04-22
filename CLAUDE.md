<!-- GSD:project-start source:PROJECT.md -->
## Project | 项目

**Design Doc Review Expert Agent** | 设计文档审查专家 Agent
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack | 技术栈

## Recommended Stack | 推荐技术栈
### Core Framework
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **LangChain** | ^0.3.x | RAG/Retrieval framework | Required per project constraints; strong retrieval abstractions |
| **LangGraph** | ^0.2.x | Workflow orchestration | Required per project constraints; superior for complex stateful workflows |
| **Python** | 3.11+ | Primary language | LangChain/LangGraph native; rich ML/embedding ecosystem |
### Vector Database
| Technology | Purpose | Pros | Cons | Recommended For |
|------------|---------|------|------|-----------------|
| **Chroma** | Local vector DB | Zero setup, easy LocalAI integration, free, great for learning | Not production-scalable, single-node only | **Learning project - RECOMMENDED** |
| **Qdrant** | Vector search | Good performance, cloud or self-hosted, Rust-based | More complex setup than Chroma | When outgrowing Chroma |
| **Pinecone** | Managed vector DB | Fully managed, scalable, good SDK | Cost, vendor lock-in, less learning value | Production with team |
| **Weaviate** | Vector search | Good built-in modules, hybrid search | Resource-heavy | Complex multi-modal |
### LLM Choices
| Provider | Model | Pros | Cons | Document Review Fit |
|----------|-------|------|------|---------------------|
| **MiniMax** | M2.7 / M2.5 | OpenAI-compatible, multimodal (images), strong Chinese/English, free tier | Limited to MiniMax ecosystem | **Best for this project - RECOMMENDED** |
| **Anthropic** | Claude 3.5 Sonnet | Excellent reasoning, vision built-in | Requires API key, cost | If MiniMax insufficient |
| **OpenAI** | GPT-4o | Multimodal natively, good all-around | Higher cost | Alternative |
### Embedding Models
| Model | Purpose | Why |
|-------|---------|-----|
| **text-embedding-3-small** | General text embedding | Good quality, low cost, OpenAI hosted |
| **bge-m3** | Bilingual (Chinese/English) | Specifically designed for multilingual, open source |
| **voyage-multilingual-2** | Multilingual retrieval | Optimized for RAG, supports 10+ languages |
### Image Handling for Prototype Review
| Approach | Tool | Complexity | Notes |
|----------|------|------------|-------|
| **MiniMax Image Understanding** | MiniMax M2.7 (multimodal) | Low | OpenAI-compatible API, free tier |
| **Claude Vision** | Claude 3.5 Sonnet (vision) | Low | If MiniMax insufficient |
| **Image Embedding + RAG** | CLIP (OpenAI) / image-chroma | Medium | For similarity search across prototype database |
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
| LLM | MiniMax M2.7 | Claude 3.5 Sonnet | No Claude API key; MiniMax supports multimodal |
| Embedding | bge-m3 | OpenAI embeddings | Better bilingual support, no per-token cost |
| Image handling | MiniMax Image Understanding | Separate CLIP | Simpler architecture for MVP |
## LangChain vs LangGraph for This Use Case
- Document loading and splitting
- Embedding generation
- Vector store operations
- Retrieval chains (RAG)
- Prompt templates
- Multi-step review workflow state machine
- Conditional branching (e.g., if PRD issues > threshold, escalate)
- Human-in-the-loop checkpoints
- Complex agentic loops with memory
- Orchestrating multiple review types (PRD + prototype)
## Installation | 安装

```bash
# Using uv (fast, Rust-based package manager)
uv sync

# Or install dependencies directly
uv add langchain langgraph langchain-openai langchain-community
uv add chromadb sentence-transformers
uv add unstructured pdfplumber Pillow

# Verify versions
uv pip show langchain langgraph chromadb | grep -E "^Name:|^Version:"
```
## Architecture Pattern for Learning
## Phase 1 Specific Recommendations
- Pinecone (only if Chroma insufficient)
- Claude Vision (only if MiniMax vision inadequate for prototypes)
- CLIP embeddings (only if image similarity search needed)
## Confidence Assessment
| Component | Confidence | Notes |
|-----------|------------|-------|
| LangChain/LangGraph roles | MEDIUM | Well-established patterns, official docs exist |
| Vector DB comparison | LOW | Web search unavailable; recommend verification |
| LLM recommendations | MEDIUM | MiniMax confirmed multimodal via platform docs |
| Chroma recommendation | MEDIUM | Known to be learning-friendly; verify scalability |
| bge-m3 for bilingual | LOW | Training data; verify with benchmarks for Chinese |
## Verification Checklist Before Implementation | 实施前验证清单

```bash
# Check uv is installed
uv --version

# Verify Python version
python --version  # Should be 3.11+

# Verify LangChain + LangGraph compatibility
python -c "import langchain; import langgraph; print('OK')"
```
# Check current versions (required before starting)
# Verify LangChain + LangGraph compatibility
# (Should work together, but verify on your env)
## Sources
- **Confidence: LOW** (web search unavailable; based on training data)
- LangChain docs: https://python.langchain.com (verify current)
- LangGraph docs: https://langchain-ai.github.io/langgraph/ (verify current)
- Chroma docs: https://docs.trychroma.com (verify current)
- bge-m3: Hugging Face model card (verify multilingual benchmarks)
- MiniMax API: https://platform.minimaxi.com/docs (verified 2026/04/16 - supports image understanding)
## Gaps to Address
- [ ] Verify current LangChain/LangGraph versions (breaking changes common)
- [ ] Confirm bge-m3 performance vs voyage-multilingual for Chinese/English
- [ ] Test MiniMax M2.7 image understanding for prototype review
- [ ] Test Chroma at 100+ page scale (may need Qdrant migration path)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture | 架构

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
