# Domain Pitfalls

**Domain:** RAG + Agent Document Review System (Design Doc Review Expert Agent)
**Researched:** 2026/04/14
**Confidence:** MEDIUM (domain expertise from training data; cannot verify with current external sources due to tool restrictions)

---

## Critical Pitfalls

Mistakes that cause rewrites, failed reviews, or silent compliance failures.

### Pitfall 1: Semantic Chunking Ignores Document Structure

**What goes wrong:** Using fixed-size character chunking (e.g., 512 tokens) destroys semantic coherence. A design principle spanning page 47 that references page 12 gets split across chunks, breaking retrieval.

**Why it happens:** Simple chunking is easy to implement. Naive overlap helps but doesn't preserve logical document structure (sections, tables, numbered lists).

**Consequences:**
- Agent retrieves fragments without context, making incorrect compliance judgments
- "Spacing should be 16px" retrieved but without the condition "for mobile breakpoints only"
- Cross-reference failures: standard A says X, standard B overrides A, agent sees only one

**Prevention:**
- Use structural chunking: split on headers, list items, table rows, paragraphs
- Preserve section hierarchy in chunk metadata
- Implement cross-chunk relationship tracking for related standards

**Detection:**
- Audit retrieved chunks for semantic completeness
- Test with queries requiring multi-standard synthesis
- Log cases where retrieved context feels "cut off"

---

### Pitfall 2: Embedding Model Mismatch with Domain Vocabulary

**What goes wrong:** General-purpose embeddings (e.g., text-embedding-3-small) fail on design terminology. "8pt grid" embeds closer to "eight point" generic text than to "baseline grid system." "Hierarchy" means different things to a general model vs. a design system.

**Why it happens:** Design standards use specialized vocabulary, Chinese-English mixed terms, and domain-specific abbreviations (MT, BD, Figma-specific terms).

**Consequences:**
- Relevant standards not retrieved when queries use standard terminology
- False positives: generic "color" standards retrieved for specific "brand color" queries
- Bilingual retrieval fails: Chinese query retrieves English chunks poorly

**Prevention:**
- Fine-tune embeddings on design corpus OR use domain-adapted models
- Build terminology glossary with query variants
- Implement synonym expansion for domain terms
- Test retrieval precision with domain-specific queries before full ingestion

**Detection:**
- Manual spot-check of retrieval results with domain expert
- Track "relevant but not retrieved" cases
- Measure retrieval quality on domain terminology queries

---

### Pitfall 3: Agent Hallucinates Compliance When Standards Are Silent

**What goes wrong:** Agent sees no explicit standard for X, so it "infers" a requirement and flags the document as non-compliant. Or worse, it invents a standard that does not exist.

**Why it happens:** LLM default behavior is to be helpful and complete. Without explicit guardrails, agents fill gaps with plausible-sounding but incorrect "standards."

**Consequences:**
- False positives: PRD marked as violating standards that don't exist
- Credibility damage: users learn to ignore agent outputs
- Legal risk if decisions are made based on hallucinated compliance

**Prevention:**
- Explicit "Standard Not Found" response instead of inference
- Confidence thresholds: if retrieval confidence < X, state uncertainty
- Human-in-the-loop for borderline cases
- Never generate fake standard citations

**Detection:**
- Audit outputs for standards that don't exist in knowledge base
- Build test suite with known compliant/non-compliant cases
- Monitor "I couldn't find" vs "You violated" ratio

---

### Pitfall 4: Linear Agent Workflow Misses Iterative Review Needs

**What goes wrong:** Implementing a simple linear pipeline: retrieve -> analyze -> report. For document review, this fails because:
- First retrieval may miss relevant context
- Analysis may need re-retrieval based on partial findings
- Some checks require comparing multiple sections

**Why it happens:** Linear pipelines are simpler to implement with LangChain. Cyclic/iterative workflows require LangGraph state management.

**Consequences:**
- Incomplete reviews: issues in section 3 discovered but section 1 check didn't account for cross-dependencies
- Missed context: analysis stops when it "finds enough issues"
- No refinement: initial hypothesis not tested against full document

**Prevention:**
- Use LangGraph for stateful review with iteration
- Implement "review loop" with explicit stages: initial scan -> gap identification -> targeted retrieval -> synthesis
- Allow agent to say "I need to re-check X after understanding Y"

**Detection:**
- Compare linear vs. iterative review outputs on complex documents
- Track how often initial conclusions change after re-review
- Measure coverage: does review of section N improve after reviewing section N+1?

---

### Pitfall 5: Knowledge Base Staleness Without Version Control

**What goes wrong:** Design standards evolve. Agent continues citing standards that have been superseded, overridden, or deleted.

**Why it happens:** RAG systems treat knowledge base as static. No mechanism tracks document versions, effective dates, or supersession relationships.

**Consequences:**
- Outdated standards applied as current requirements
- Contradictory outputs: "Section 4.2 requires X" and "Section 4.2 (superseded) prohibited X"
- User confidence in agent collapses when they discover the standard changed

**Prevention:**
- Implement knowledge base versioning with effective date tracking
- Tag chunks with version metadata (version_id, effective_date, superseded_date)
- Query-time filtering: only retrieve current valid standards
- Explicitly note when retrieved content is from older version

**Detection:**
- Regular audits of retrieved standards against source documents
- Alert when supersession relationships are violated
- Track "this standard changed" feedback from users

---

## Moderate Pitfalls

Issues that cause degraded quality but not complete failure.

### Pitfall 6: Prototype Image Review Treats OCR as Truth

**What goes wrong:** OCR extracts "spacing: 16px" from a prototype image. Agent trusts this number. In reality, OCR misread "18px" or the spacing is visually inconsistent with the number shown.

**Why it happens:** OCR confidence scores are ignored. No visual validation. LLM accepts extracted text at face value.

**Consequences:**
- False compliance claims based on misread values
- Missing actual spacing violations because numbers "look correct"
- Layout interpretation limited to extracted text, ignoring visual hierarchy

**Prevention:**
- Treat OCR as "hint" not "fact" - flag low-confidence extractions
- Use multiple OCR passes and cross-validate results
- Implement visual sanity checks (does extracted value match visual estimate?)
- Separate "what the text says" from "what the design shows"

**Detection:**
- Human audit of OCR confidence scores vs. actual accuracy
- Test with intentionally misaligned numbers vs. visual spacing
- Track "extraction confidence < 0.8" rate

---

### Pitfall 7: Context Window Saturation by Retrieval Volume

**What goes wrong:** Agent retrieves 20 relevant chunks. All stuffed into context. Important signals get lost in noise. Agent注意力分散，忽略了最关键的问题。

**Why it happens:** "More context is better" assumption. No prioritization or filtering of retrieved content.

**Consequences:**
- Important standards mentioned at position 15 of 20 chunks get ignored
- Agent summarizes rather than analyzes ("this section mentions spacing issues")
- Cost and latency increase without quality improvement

**Prevention:**
- Rank and filter retrieved chunks by relevance score
- Implement maximum context budget (e.g., top 5-7 chunks per check)
- Use two-stage retrieval: broad retrieval -> focused re-ranking
- Let agent request more context if needed (iterative approach)

**Detection:**
- Monitor context length vs. output quality correlation
- Test if reducing retrieval set improves output precision
- Track agent feedback: "I need more context" requests

---

### Pitfall 8: LangChain LangGraph Architectural Confusion

**What goes wrong:** Using LangChain for complex workflows that should use LangGraph, OR using LangGraph for simple retrieval that should use LangChain. Result: overengineered or limitation-hit code.

**Why it happens:** Both tools have overlapping capabilities. Documentation emphasizes "use LangGraph for agents" but doesn't clarify when simple LangChain chains suffice.

**Consequences:**
- LangChain: Workflow logic becomes unmaintainable nested chains
- LangGraph: Simple retrieval wrapped in unnecessary state management
- Team confusion: different parts of system use different patterns inconsistently

**Prevention:**
- Decision framework:
  - Simple sequential retrieval -> LangChain LCEL chains
  - Stateful multi-step with branching/iteration -> LangGraph
  - Complex agentic behavior with tool use -> LangGraph
- Document architectural decisions with explicit rationale
- Establish team consensus on pattern usage before implementation

**Detection:**
- Code review for architectural fitness
- Complexity metrics: decision points, state variables, tool count
- Refactoring triggers: nested chains > 3 levels, > 5 tools in single chain

---

### Pitfall 9: Bilingual Output Creates Inconsistent Semantics

**What goes wrong:** Chinese and English outputs diverge. Chinese says "严重" while English says "warning" for the same severity level. Terminology inconsistent across languages.

**Why it happens:** Independent translation without glossary. LLM generates different severity assessments in each language. No cross-language consistency checks.

**Consequences:**
- User trust damage when outputs don't match
- Compliance confusion: is "warning" = "严重" or just "注意"?
- Bilingual feature becomes bilingual problem

**Prevention:**
- Build severity glossary: CRITICAL=严重/关键, WARNING=警告, INFO=提示/信息
- Generate English first, use as source for Chinese translation (not vice versa)
- Implement cross-language consistency validation
- Human review of bilingual outputs until consistency established

**Detection:**
- Track severity term usage across languages
- Audit random samples for semantic equivalence
- Build test cases with known severity levels and verify both languages match

---

### Pitfall 10: Document Review Agent Doesn't Know What It Doesn't Know

**What goes wrong:** Agent reviews typography but misses that the standard it cited applies only to web, not mobile. Agent doesn't know its own limitations.

**Why it happens:** No explicit scope definition in agent system prompt. No "out of scope" declaration. Agent overgeneralizes.

**Consequences:**
- Applies wrong standard to wrong context
- False confidence in outputs
- Users rely on outputs for unintended use cases

**Prevention:**
- Explicit scope declaration in system prompt: "You review mobile app PRDs against mobile design standards v2.3"
- Define checkable dimensions: what this review covers, what it explicitly does not
- Implement uncertainty expression: "This standard appears to apply to X context"
- Build scope boundaries into evaluation criteria

**Detection:**
- Test with out-of-scope document types
- Audit outputs for out-of-scope claims
- Track user feedback: "this doesn't apply to my use case"

---

## Minor Pitfalls

Issues that cause friction but are recoverable.

### Pitfall 11: Evaluation Without Ground Truth Remains Anecdotal

**What goes wrong:** Team manually reviews some outputs and says "looks good." No systematic evaluation. Quality remains unknown.

**Prevention:** Build golden dataset with known inputs and expected outputs. Measure precision/recall on issue detection.

---

### Pitfall 12: Chunk Overlap Creates Redundant Retrieval

**What goes wrong:** Overlap=200 tokens causes same content retrieved multiple times, diluting context window with duplicates.

**Prevention:** Track chunk provenance. Deduplicate retrieved content before context assembly.

---

### Pitfall 13: Embedding Cache Invalidation Ignored

**What goes wrong:** Knowledge base updated but embeddings not regenerated. Stale vectors retrieved.

**Prevention:** Hash-based cache invalidation. Version embeddings with content.

---

## Phase-Specific Warnings

| Phase | Likely Pitfall | Mitigation |
|-------|---------------|------------|
| Phase 1: RAG Setup | Pitfall 1 (Semantic Chunking) | Invest in structural chunking early; re-chunkting later is costly |
| Phase 2: Agent Core | Pitfall 3 (Hallucination) | Implement "standard not found" guardrails from day 1 |
| Phase 3: Multi-Document | Pitfall 5 (Staleness) | Design versioning schema before ingesting first doc |
| Phase 4: Prototype Review | Pitfall 6 (OCR Trust) | Build visual validation layer; don't trust OCR alone |
| Phase 5: Bilingual | Pitfall 9 (Inconsistency) | Create terminology glossary before generating bilingual output |
| Cross-cutting | Pitfall 8 (LangChain/LangGraph confusion) | Document decision framework early; revisit at each phase |

---

## Anti-Patterns to Avoid

### "Retrieve Everything, Let LLM Filter"
**What:** Retrieve top-k chunks regardless of relevance, stuff into context.
**Why bad:** Signal-to-noise degrades. LLM attention diffuses. Cost explodes.
**Instead:** Two-stage retrieval with relevance threshold, not just top-k.

### "Trust First Retrieval"
**What:** Use initial retrieval as definitive.
**Why bad:** Retrieval fails silently. Wrong initial context poisons all downstream analysis.
**Instead:** Implement self-correction loop where agent can request re-retrieval.

### "One-Shot Review"
**What:** Single pass through document, report all findings.
**Why bad:** Misses cross-document dependencies. Initial findings may change with fuller context.
**Instead:** Iterative refinement with explicit review stages.

### "Standards as Laws"
**What:** Treat every retrieved standard as absolute requirement.
**Why bad:** Standards have context, conditions, exceptions. Overly rigid review produces false positives.
**Instead:** Distinguish mandatory vs. recommended, general vs. specific, current vs. superseded.

---

## Sources

- **Confidence Note:** This analysis is based on domain expertise from training data. External verification tools (Context7, WebSearch, WebFetch) were unavailable during research. Claims should be validated against current LangChain/LangGraph documentation and RAG best practices before implementation.

- RAG pitfalls documented in academic literature and industry post-mortems (semantic chunking, embedding mismatch, hallucination)
- LangChain/LangGraph architectural guidance from official documentation patterns
- Document review system anti-patterns from similar AI compliance/audit system deployments

---

## Gaps to Address

- No verified current sources for LangChain LCEL vs LangGraph decision framework (2025-2026 updates)
- Prototype/image review pitfalls insufficiently documented in public literature
- Chinese-language RAG-specific challenges (embedding models, tokenization) need specialized research
- Knowledge base versioning patterns for RAG systems not well-established in public docs
