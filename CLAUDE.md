<!-- GSD:project-start source:PROJECT.md -->
## Project

**Design Doc Review Expert Agent**
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
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
| **Anthropic** | Claude 3.5 Sonnet | Excellent reasoning, cost-effective, strong instruction following | API cost (but lower than GPT-4) | **Best for structured review tasks** |
| **OpenAI** | GPT-4o | Multimodal natively (images), good all-around | Higher cost, may be overkill for text-only | Good if prototyping image review |
| **Local** | Llama 3.1 70B / Mixtral | Privacy, no API cost | Requires GPU, quality gap, setup complexity | Only if privacy critical |
### Embedding Models
| Model | Purpose | Why |
|-------|---------|-----|
| **text-embedding-3-small** | General text embedding | Good quality, low cost, OpenAI hosted |
| **bge-m3** | Bilingual (Chinese/English) | Specifically designed for multilingual, open source |
| **voyage-multilingual-2** | Multilingual retrieval | Optimized for RAG, supports 10+ languages |
### Image Handling for Prototype Review
| Approach | Tool | Complexity | Notes |
|----------|------|------------|-------|
| **Multimodal LLM** | Claude 3.5 Sonnet (vision) / GPT-4o | Low | Direct image input, no embedding needed |
| **Image Embedding + RAG** | CLIP (OpenAI) / image-chroma | Medium | For similarity search across prototype database |
| **Visual Comparison** | Custom pipeline | High | Extract colors, layout, compare against design tokens |
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
## Installation
# Core dependencies
# Optional for image handling
# Verify versions
## Architecture Pattern for Learning
## Phase 1 Specific Recommendations
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
# Check current versions (required before starting)
# Verify LangChain + LangGraph compatibility
# (Should work together, but verify on your env)
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

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
