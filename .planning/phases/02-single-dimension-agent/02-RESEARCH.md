# Phase 2: Single-Dimension Agent - Research

**Researched:** 2026/04/16
**Domain:** PRD Document Review Agent with LangGraph iterative refinement
**Confidence:** MEDIUM (training knowledge; web search unavailable for verification)

## Summary

Phase 2 extends the Phase 1 Core RAG Pipeline with a PRD document review agent that validates PRD structure, terminology, and completeness against design standards. The agent uses LangGraph cycles for iterative refinement (max 3 iterations per D-17), generates bilingual Markdown compliance reports (per D-13), and employs hybrid severity calibration combining rule-based scoring with LLM discretion (per D-14).

**Primary recommendation:** Build a PRD review state machine with fan-out/join pattern where structure, terminology, and completeness checks run in parallel, then aggregate results into a structured report. Use a `review_iteration` counter in state to enforce max 3 iterations.

## User Constraints (from CONTEXT.md)

### Phase 1 Decisions (Extends)
- **D-10:** All outputs must be bilingual (Chinese/English)
- **D-12:** System explicitly states "Standard Not Found" when knowledge base has no relevant guidance
- **LangGraph for workflow orchestration (AGT-01)**
- **Chroma for vector storage**
- **bge-m3 for embeddings**
- **MiniMax M2.7 for LLM**

### Phase 2 Specific Decisions
- **D-13:** Structured Markdown compliance reports
- **D-14:** Hybrid severity calibration (rules + LLM discretion)
- **D-15:** Hybrid terminology matching (exact + semantic)
- **D-16:** User-controlled review depth (fast/thorough/balanced)
- **D-17:** Iterative refine agent loop, max 3 iterations

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PRD-01 | Validate PRD structure (Overview, User Stories, Acceptance Criteria) | LangGraph state machine pattern |
| PRD-02 | Check terminology consistency against design glossary | Exact match + semantic similarity |
| PRD-03 | Validate completeness (all required sections, no placeholders) | LLM-powered content analysis |
| PRD-04 | Check basic formatting (heading hierarchy, bullet consistency) | Rule-based validation |
| RPT-01 | Generate categorized compliance report (Structure, Terminology, Layout, Accessibility) | Markdown report generation |
| RPT-02 | Each issue includes severity (Critical / Major / Minor / Suggestion) | Hybrid severity calibration |
| RPT-03 | Each issue includes exact location reference | Line numbers, section names |
| RPT-04 | Specific improvement suggestions per issue | LLM prompt engineering |
| RPT-05 | All outputs bilingual (Chinese and English) | Bilingual prompt templates |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **LangChain** | ^0.3.x | LLM integration, retrieval chains | Required per project constraints |
| **LangGraph** | ^0.2.x | State machine workflow, cycles | Required per AGT-01; superior for iterative workflows |
| **MiniMax SDK** | latest | OpenAI-compatible LLM API | Required per PROJECT.md; multimodal M2.7 |
| **Chroma** | latest | Vector store (from Phase 1) | Local, zero-setup |
| **bge-m3** | latest | Embeddings (from Phase 1) | Bilingual Chinese/English |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **rank_bm25** | latest | BM25 for exact terminology matching | PRD-02 terminology check |
| **regex** | built-in | Heading hierarchy validation | PRD-04 formatting check |
| **pydantic** | latest | Structured output validation | RPT-01 report structure |

**Note:** Verify versions with `npm view <package> version` or `uv pip show <package>` before implementation.

## Architecture Patterns

### Recommended Project Structure
```
src/
├── workflow/
│   ├── state.py          # PRDReviewState definition
│   ├── graph.py          # PRD review graph (extends Phase 1)
│   └── nodes/            # Node implementations
│       ├── structure.py   # PRD structure validation
│       ├── terminology.py # Terminology matching
│       ├── completeness.py # Completeness validation
│       └── report.py      # Report generation
├── retrieval/
│   └── hybrid_search.py  # From Phase 1, use for terminology
├── llm/
│   └── minimax.py        # MiniMax LLM client
├── report/
│   ├── markdown.py        # Markdown report generation
│   └── severity.py        # Severity calibration
└── prompts/
    └── prd_review.py      # PRD review prompt templates
```

### Pattern 1: Iterative Refinement with Cycles

**What:** LangGraph state machine with conditional edges that loop back to previous nodes for refinement.

**When to use:** When initial review findings are inconclusive and need re-retrieval or re-analysis (per D-17, max 3 iterations).

**Implementation pattern:**
```python
from typing import Literal
from langgraph.graph import StateGraph, END

class PRDReviewState(TypedDict):
    prd_text: str
    review_iteration: int
    max_iterations: int
    findings: List[Finding]
    refined_findings: Optional[List[Finding]]
    report: Optional[str]

def check_iteration_limit(state: PRDReviewState) -> Literal["refine", "generate_report"]:
    if state["review_iteration"] < state["max_iterations"]:
        return "refine"
    return "generate_report"

workflow.add_conditional_edges(
    "analyze_findings",
    check_iteration_limit,
    {
        "refine": "re_retrieve",
        "generate_report": "generate_report",
    }
)
workflow.add_edge("re_retrieve", "analyze_findings")
```

**Source:** [ASSUMED] LangGraph 0.2.x documentation on conditional edges and cycles

### Pattern 2: Fan-Out/Join for Parallel Validation

**What:** Multiple validation checks (structure, terminology, completeness) run in parallel as separate nodes, then results are joined.

**When to use:** When PRD-01, PRD-02, PRD-03, PRD-04 can run independently.

**Implementation pattern:**
```python
# Fan-out: parallel execution
workflow.add_node("validate_structure", validate_structure_node)
workflow.add_node("validate_terminology", validate_terminology_node)
workflow.add_node("validate_completeness", validate_completeness_node)
workflow.add_node("validate_formatting", validate_formatting_node)

# All feed into aggregation
workflow.add_edge("validate_structure", "aggregate_findings")
workflow.add_edge("validate_terminology", "aggregate_findings")
workflow.add_edge("validate_completeness", "aggregate_findings")
workflow.add_edge("validate_formatting", "aggregate_findings")

# Join node
workflow.add_node("aggregate_findings", aggregate_findings_node)
```

**Source:** [ASSUMED] LangGraph fan-out/join pattern documentation

### Pattern 3: Hybrid Severity Calibration (Rules + LLM)

**What:** Severity determined by combining rule-based scoring with LLM discretion.

**When to use:** Per D-14: "Hybrid severity calibration: rules + LLM discretion"

**Implementation pattern:**
```python
def calculate_severity(issue_type: str, location: str, content: str, llm_assessment: str) -> str:
    """
    1. Apply rule-based severity for known issue types
    2. Allow LLM to override within bounds (e.g., Major -> Critical if severe)
    """
    # Rule-based initial severity
    rule_severity_map = {
        "missing_section": "Critical",
        "undefined_term": "Major",
        "placeholder_content": "Major",
        "heading_inconsistency": "Minor",
    }
    base_severity = rule_severity_map.get(issue_type, "Minor")

    # LLM can adjust within bounds: Minor < Suggestion, but cannot go Critical -> Minor
    severity_hierarchy = ["Critical", "Major", "Minor", "Suggestion"]

    # Parse LLM assessment and adjust if appropriate
    if llm_assessment and "elevate" in llm_assessment.lower():
        current_idx = severity_hierarchy.index(base_severity)
        if current_idx > 0:  # Not already Critical
            base_severity = severity_hierarchy[current_idx - 1]

    return base_severity
```

**Source:** [ASSUMED] Common severity calibration patterns in code review tools

### Pattern 4: Hybrid Terminology Matching (Exact + Semantic)

**What:** Combine exact string matching (BM25) with semantic similarity (vector) for terminology validation.

**When to use:** Per D-15: "Hybrid terminology matching: exact + semantic"

**Implementation pattern:**
```python
def check_terminology(text: str, glossary: List[Tuple[str, str]]) -> List[TerminologyIssue]:
    """
    1. Exact match: Find undefined terms via glossary lookup
    2. Semantic match: Find similar-but-different terms via embeddings
    """
    issues = []

    # Exact matching using glossary terms
    for term, definition in glossary:
        if term.lower() in text.lower() and term not in DEFINED_TERMS:
            issues.append(TerminologyIssue(
                term=term,
                type="undefined_term",
                severity="Major",
                location=find_location(text, term),
            ))

    # Semantic matching using embeddings
    # (Use bge-m3 embeddings for Chinese/English cross-lingual)
    text_embedding = embedding_fn.embed_query(text)
    for term, definition in glossary:
        term_embedding = embedding_fn.embed_query(term)
        similarity = cosine_similarity(text_embedding, term_embedding)

        # Flag if similar but not exact match (possible variant/misspelling)
        if 0.85 <= similarity < 1.0:  # Threshold for "similar"
            issues.append(TerminologyIssue(
                term=term,
                type="similar_term",
                severity="Minor",
                location=find_location(text, term),
                suggestion=f"Did you mean '{term}'?",
            ))

    return issues
```

**Source:** [ASSUMED] Hybrid retrieval pattern from Phase 1 HybridRetriever, applied to terminology

### Pattern 5: Review Depth Control (Fast/Thorough/Balanced)

**What:** User selects review depth that controls iteration count, retrieval breadth, and LLM analysis depth.

**When to use:** Per D-16: "User-controlled review depth: fast/thorough/balanced"

**Implementation pattern:**
```python
DEPTH_CONFIG = {
    "fast": {
        "max_iterations": 1,
        "retrieval_k": 3,
        "llm_detail": "brief",
    },
    "balanced": {
        "max_iterations": 2,
        "retrieval_k": 5,
        "llm_detail": "standard",
    },
    "thorough": {
        "max_iterations": 3,
        "retrieval_k": 10,
        "llm_detail": "comprehensive",
    },
}
```

**Source:** [ASSUMED] Common review depth patterns

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM structured output | Custom JSON parsing | Pydantic models + LangChain output parsers | Robust parsing with validation |
| Markdown report formatting | String concatenation | markdown library (e.g., `markdown` or `mdutils`) | Proper escaping, structure |
| Cosine similarity | Manual math | numpy or sklearn.metrics.pairwise.cosine_similarity | Optimized, tested |
| Bilingual formatting | Separate English/Chinese sections | Template with interleaved sections per D-10 | Consistency |

**Key insight:** For bilingual output, use a template pattern that interleaves Chinese and English for each section, rather than separate full sections. This is already established in `src/prompts/templates.py`.

## Common Pitfalls

### Pitfall 1: Infinite Loops in LangGraph Cycles

**What goes wrong:** Conditional edges create infinite loops if iteration check fails to increment.

**Why it happens:** Forgetting to increment `review_iteration` counter in state.

**How to avoid:**
- Always increment `review_iteration` in the refine path
- Set explicit `max_iterations` bound
- Use a `should_continue` function that checks both iteration count AND convergence

**Warning signs:** Graph execution never terminates, high token usage

### Pitfall 2: Lost State in Fan-Out/Join

**What goes wrong:** State from parallel nodes overwrites each other in join.

**Why it happens:** LangGraph state updates are dict merges; parallel writes can lose data.

**How to avoid:**
- Use `reduce` function to accumulate findings from all parallel nodes
- Each parallel node should append to a list, not replace

```python
def aggregate_findings(state: PRDReviewState) -> PRDReviewState:
    # Collect all findings from validation nodes
    all_findings = []
    for finding in state.get("structure_findings", []):
        all_findings.append(finding)
    for finding in state.get("terminology_findings", []):
        all_findings.append(finding)
    # ... etc

    return {"all_findings": all_findings}
```

**Warning signs:** Some findings missing from final report

### Pitfall 3: Severity Escalation Without Bounds

**What goes wrong:** LLM can escalate any issue to Critical regardless of context.

**Why it happens:** No bounds check on LLM severity adjustments.

**How to avoid:**
- Define severity hierarchy with allowed transitions
- LLM can only escalate by one level, not jump directly to Critical
- Rule-based severity sets the floor, LLM can only increase within limits

**Warning signs:** All issues become Critical, report loses differentiation

### Pitfall 4: Terminology False Positives from Semantic Matching

**What goes wrong:** Low specificity in semantic matching flags valid content as issues.

**Why it happens:** Semantic similarity threshold too aggressive (e.g., > 0.7 for Chinese text).

**How to avoid:**
- Use higher threshold for semantic matching (e.g., 0.90+)
- Require exact match confirmation before flagging as "similar" issue
- Combine with exact matching first, then only use semantic for ambiguous cases

**Warning signs:** Report has many Minor/Suggestion issues that are false positives

## Code Examples

### PRD Review State Definition

```python
from typing import TypedDict, List, Optional, Literal
from pydantic import BaseModel

class Finding(BaseModel):
    """Single review finding with location and severity."""
    issue_type: str  # structure, terminology, completeness, formatting
    severity: Literal["Critical", "Major", "Minor", "Suggestion"]
    location: str  # line number, section name, or coordinates
    description_en: str
    description_zh: str
    suggestion_en: Optional[str] = None
    suggestion_zh: Optional[str] = None

class PRDReviewState(TypedDict):
    """State for PRD review workflow."""
    prd_text: str
    collection_name: str
    review_depth: Literal["fast", "balanced", "thorough"]
    max_iterations: int
    review_iteration: int

    # Parallel validation results (fan-out)
    structure_findings: List[Finding]
    terminology_findings: List[Finding]
    completeness_findings: List[Finding]
    formatting_findings: List[Finding]

    # Aggregation and refinement
    all_findings: List[Finding]
    refined_findings: Optional[List[Finding]]

    # Final output
    report: Optional[str]
```

### MiniMax Structured Output

```python
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

# MiniMax OpenAI-compatible API
llm = ChatOpenAI(
    model="MiniMax/M2.7",
    api_key=os.environ.get("MINIMAX_API_KEY"),
    base_url="https://api.minimax.chat/v1",
)

class SeverityAssessment(BaseModel):
    """LLM severity assessment for a finding."""
    suggested_severity: str  # Critical, Major, Minor, Suggestion
    reasoning_en: str
    reasoning_zh: str
    should_elevate: bool

# Use with LangChain output parser
from langchain.output_parsers import PydanticOutputParser
parser = PydanticOutputParser(pydantic_object=SeverityAssessment)

prompt = f"""
Assess the severity of this PRD issue:

Issue: {{issue_description}}
Context: {{prd_context}}

{parser.get_format_instructions()}
"""
```

### Report Generation (Bilingual Markdown)

```python
def generate_markdown_report(findings: List[Finding]) -> str:
    """Generate bilingual Markdown compliance report per RPT-01, RPT-05."""

    # Group by severity for organized presentation
    severity_order = ["Critical", "Major", "Minor", "Suggestion"]
    grouped = {s: [] for s in severity_order}
    for f in findings:
        grouped[f.severity].append(f)

    lines = [
        "# PRD Compliance Review Report",
        "# PRD 合规审查报告",
        "",
        f"Total Issues: {len(findings)}",
        f"总问题数：{len(findings)}",
        "",
    ]

    for severity in severity_order:
        issues = grouped[severity]
        if not issues:
            continue

        lines.append(f"## {severity} | {severity}")
        lines.append(f"Count | 数量: {len(issues)}")
        lines.append("")

        for i, issue in enumerate(issues, 1):
            lines.append(f"### {i}. {issue.issue_type} | {issue.issue_type}")
            lines.append(f"**Location | 位置:** {issue.location}")
            lines.append("")
            lines.append(f"**English:** {issue.description_en}")
            lines.append(f"**Chinese:** {issue.description_zh}")
            if issue.suggestion_en:
                lines.append(f"**Suggestion | 建议:** {issue.suggestion_en}")
                lines.append(f"**建议:** {issue.suggestion_zh}")

            lines.append("")

    return "\n".join(lines)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-pass review | Iterative refinement with cycles | LangGraph 0.2.x added cycle support | Better handling of inconclusive initial findings |
| LLM-only severity | Hybrid rules + LLM | Emerging best practice 2024-2025 | More consistent, auditable severity decisions |
| Exact string matching | Hybrid exact + semantic | RAG advanced 2023+ | Catches terminology issues that exact match misses |

**Deprecated/outdated:**
- LangChain `create_stuff_documents_chain` — use LangGraph StateGraph for complex workflows
- `directory_load` for document ingestion — use `unstructured` library directly

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | LangGraph 0.2.x supports conditional edges that can loop back | Architecture Patterns | Cycle pattern may require different API |
| A2 | MiniMax API is OpenAI-compatible with structured output support | MiniMax Integration | May need custom output parsing |
| A3 | Fan-out/join pattern works with reduce function for state accumulation | Common Pitfalls | State may be lost in parallel execution |
| A4 | bge-m3 similarity threshold 0.85-0.90 is appropriate for semantic terminology matching | Pattern 4 | May need calibration with real data |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Open Questions

1. **How to implement the "depth" parameter in LangGraph state?**
   - What we know: Need to control `max_iterations`, `retrieval_k`, `llm_detail`
   - What's unclear: Whether depth should be a node parameter or graph compilation option
   - Recommendation: Pass as initial state, let nodes read from state

2. **Should MiniMax structured output use JSON mode or Pydantic parsing?**
   - What we know: MiniMax is OpenAI-compatible; supports `response_format: { type: "json_object" }`
   - What's unclear: Whether JSON mode is stable across all MiniMax models
   - Recommendation: Use PydanticOutputParser for robustness, fallback to JSON parse

3. **How to handle PRD-05 (detecting vague language) in Phase 2 vs Phase 3?**
   - What we know: PRD-05 is traced to Phase 3 in REQUIREMENTS.md
   - What's unclear: Whether Phase 2 should still implement basic vague language detection
   - Recommendation: Defer to Phase 3 per traceability matrix

## Environment Availability

> Step 2.6: SKIPPED (no external dependencies beyond Phase 1 code)

Phase 2 builds entirely on existing Phase 1 infrastructure. No new external tools, services, or runtimes required beyond verification of existing dependencies.

## Validation Architecture

> `workflow.nyquist_validation: false` in config — skip validation architecture section.

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A — no auth in MVP |
| V3 Session Management | No | N/A — stateless review |
| V4 Access Control | No | N/A — single user |
| V5 Input Validation | Yes | Pydantic models for all inputs (PRD text, findings) |
| V6 Cryptography | No | N/A — no cryptographic operations |

**Known Threat Patterns for PRD Review:**
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious PRD with embedded scripts | Information Disclosure | Sanitize output before display; no eval() of PRD content |
| Prompt injection via PRD content | Integrity | Treat PRD as untrusted input; don't include raw PRD in LLM prompts without framing |
| Large PRD causing token overflow | Denial of Service | Enforce chunking limits before processing |

## Sources

### Primary (HIGH confidence)
- None available (web search unavailable)

### Secondary (MEDIUM confidence)
- [ASSUMED] LangGraph documentation on conditional edges and cycles
- [ASSUMED] LangChain Pydantic output parser documentation

### Tertiary (LOW confidence)
- [ASSUMED] Severity calibration patterns from code review tools
- [ASSUMED] MiniMax OpenAI-compatible API behavior

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM — based on Phase 1 choices and training knowledge
- Architecture: MEDIUM — LangGraph patterns well-documented, iterative refinement less common
- Pitfalls: MEDIUM — common LangGraph issues, may need verification

**Research date:** 2026/04/16
**Valid until:** 2026/05/16 (30 days — stable patterns)
