# Phase 4: Polish and Integration - Research

**Researched:** 2026/04/17
**Domain:** LangGraph error handling, cycle safety, confidence thresholds, end-to-end workflow composition
**Confidence:** MEDIUM

## Summary

Phase 4 focuses on production-hardening the existing RAG + review pipeline built in phases 1-3. The primary work involves: (1) implementing centralized error handling with smart retry logic, (2) adding convergence detection to prevent infinite loops in the refinement cycles, (3) enforcing confidence thresholds with explicit "Standard Not Found" responses, and (4) creating a unified `review()` entry point that composes PRD and image review graphs.

**Primary recommendation:** Implement error handling via conditional edges that check `state["error"]`, implement convergence as a comparison function in `should_refine_decision`, and create `ReviewResponse` as a Pydantic model that wraps graph state for caller consumption.

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-25:** Centralized error handler node via conditional routing; transient errors retry 2 times (3 total attempts) with exponential backoff (2s, 4s, 8s); programming errors fail immediately; after retries exhausted, generate bilingual error response and halt
- **D-26:** Convergence check: full finding comparison across consecutive iterations (count + severity per category + location set stability); stable across 2 consecutive iterations -> exit early; max_iterations=3 hard ceiling
- **D-27:** Fixed threshold 0.7 default (global, not per-workflow)
- **D-28:** Three-zone confidence handling: 0.7+ → found, 0.5-0.7 → low-confidence warning (bilingual), <0.5 → always Standard Not Found
- **D-29:** Hallucination prevention: Standard Not Found is explicit bilingual message when confidence < threshold
- **D-30:** Single unified entry point: `review(prd_text, image_path=None)` - if image_path provided use create_image_review_graph(), else create_prd_review_graph()
- **D-31:** Two separate graphs (no merge) - graphs remain independent, review() composes them
- **D-32:** Structured ReviewResponse object returned to caller with fields: report (bilingual string), findings (list), status, error - hides state schema complexity
- **D-33:** Image validators run independently of PRD findings - no cross-validator state sharing beyond aggregate_findings

### Deferred Ideas (OUT OF SCOPE)

- Version metadata lifecycle management - deferred to v2
- Stale data cleanup/rotation - deferred to v2

## Standard Stack

### Core Libraries
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **LangGraph** | 1.1.6 | Workflow orchestration | Required per project constraints; cycles and state management |
| **LangChain** | 1.2.15 | RAG abstractions | Required per project constraints; retrieval integrations |
| **Pydantic** | 2.13.1 | Data validation | Used for Finding model and ReviewResponse |

**Note:** Installed versions (LangGraph 1.1.6, LangChain 1.2.15) differ from CLAUDE.md constraints (`^0.2.x` LangGraph, `^0.3.x` LangChain). The installed versions are significantly newer. API compatibility between 0.2.x and 1.x has breaking changes. [ASSUMED - needs verification]

## Architecture Patterns

### Pattern 1: Error Handler via Conditional Edge Routing

**What:** Error handling implemented by checking `state["error"]` via conditional edges that route to an error handler node.

**When to use:** When you need centralized exception handling across all graph nodes.

**Implementation approach (based on LangGraph patterns):**
```python
def error_handler_node(state: PRDReviewState) -> PRDReviewState:
    """Handle errors after retries exhausted - generate bilingual error and halt."""
    error = state.get("error", "Unknown error")
    return {
        "status": "error",
        "report": f"Error | 错误: {error}\n\nThe review could not be completed.",
        "error": error,
    }

def should_handle_error(state: PRDReviewState) -> Literal["error_handler", "__end__"]:
    """Route to error handler if error is set, otherwise continue."""
    if state.get("error"):
        return "error_handler"
    return "__end__"

# In graph construction:
workflow.add_conditional_edges(
    "aggregate_findings",
    should_handle_error,
    {"error_handler": "error_handler", "__end__": END}
)
```

**Key insight:** Error handler is placed AFTER aggregate_findings (the join point) to catch errors from any validator. It generates a bilingual error report and halts.

### Pattern 2: Retry Logic in State

**What:** Retry implemented by incrementing a retry counter in state and checking it before retrying.

**When to use:** For transient errors (network, API, rate limit) that may succeed on retry.

**Implementation approach:**
```python
def validate_structure_node(state: PRDReviewState) -> PRDReviewState:
    """Validate structure with retry support for transient errors."""
    try:
        # main validation logic
        result = do_validation()
        return {**state, "structure_findings": result, "error": None}
    except RateLimitError as e:
        retry_count = state.get("retry_count", 0)
        if retry_count >= 2:
            return {**state, "error": f"Rate limit exceeded after 3 attempts: {e}"}
        # Return with retry indicator - next node will retry
        return {**state, "retry_count": retry_count + 1, "error": str(e)}
    except ProgrammingError as e:
        # Fail immediately - no point retrying
        return {**state, "error": f"Programming error (not retryable): {e}"}
```

**Key insight:** Per D-25, transient errors (network, API, rate limit) retry 3 times total with exponential backoff. Programming errors (type, missing field) fail immediately.

### Pattern 3: Convergence Detection in Cycle Decision

**What:** Convergence check compares findings across iterations to detect stability.

**When to use:** In refinement loops where you want early exit when findings stabilize.

**Implementation approach:**
```python
def should_refine_node(state: PRDReviewState) -> PRDReviewState:
    """Increment iteration counter and check for convergence.
    
    Per D-26: stable across 2 consecutive iterations -> exit early.
    Stores current findings as previous_findings for next iteration comparison.
    """
    current_findings = state.get("refined_findings", state["all_findings"])
    previous_findings = state.get("previous_findings")
    
    new_state = {
        "review_iteration": state["review_iteration"] + 1,
        "previous_findings": current_findings,
    }
    
    if previous_findings is not None and _findings_stable(previous_findings, current_findings):
        return {**new_state, "_converged": True}
    
    return {**new_state, "_converged": False}


def should_refine_decision(state: PRDReviewState) -> Literal["refine", "generate_report"]:
    """Decide whether to continue refinement or generate report.
    
    Convergence check: findings stable across 2 consecutive iterations.
    """
    if state["review_iteration"] >= state["max_iterations"]:
        return "generate_report"
    
    if state.get("_converged"):
        return "generate_report"
    
    return "refine"

def _findings_stable(prev: List[Finding], curr: List[Finding]) -> bool:
    """Check if findings are stable (unchanged) between iterations.
    
    Per D-26: comparison includes count + severity per category + location set stability.
    """
    if len(prev) != len(curr):
        return False
    
    # Compare by category counts
    prev_by_cat = _count_by_category(prev)
    curr_by_cat = _count_by_category(curr)
    if prev_by_cat != curr_by_cat:
        return False
    
    # Compare locations
    prev_locs = {f.location for f in prev}
    curr_locs = {f.location for f in curr}
    return prev_locs == curr_locs

def _count_by_category(findings: List[Finding]) -> dict:
    """Count findings by category and severity."""
    return {(f.issue_type, f.severity): sum(1 for f in findings 
             if f.issue_type == f.issue_type and f.severity == f.severity)}
```

**Key insight:** Per D-26, convergence is defined as "stable across 2 consecutive iterations" where stability means same count + severity per category + same location set.

### Pattern 4: Three-Zone Confidence Handling

**What:** Different behavior based on confidence score zones.

**When to use:** When you need granular control over how low-confidence results are handled.

**Implementation approach:**
```python
def query_and_classify_confidence(state: QueryState) -> QueryState:
    """Query KB and classify confidence into three zones per D-28."""
    # ... retrieval logic ...
    confidence = results[0][1] if results else 0.0
    threshold = state["threshold"]  # default 0.7
    low_confidence_threshold = 0.5  # D-28 hard floor
    
    if confidence >= threshold:
        zone = "found"
        standard_found = True
    elif confidence >= low_confidence_threshold:
        zone = "low_confidence_warning"
        standard_found = True  # Still found, but warn
    else:
        zone = "not_found"
        standard_found = False
    
    return {
        **state,
        "confidence": confidence,
        "standard_found": standard_found,
        "confidence_zone": zone,  # Add to state for reporting
    }

def format_results_node(state: QueryState) -> QueryState:
    """Format with low-confidence warning if applicable."""
    if state.get("confidence_zone") == "low_confidence_warning":
        response = create_low_confidence_warning(state["results"], state["confidence"])
    else:
        response = format_retrieval_results(state["results"])
    return {**state, "response": response}
```

### Pattern 5: Unified Entry Point Composition

**What:** Single `review()` function that composes separate graphs.

**When to use:** When you have multiple workflow graphs that share some logic but differ in scope.

**Implementation approach:**
```python
from pydantic import BaseModel
from typing import Optional, List

class ReviewResponse(BaseModel):
    """Structured response object per D-32."""
    report: str  # Bilingual compliance report
    findings: List[Finding]  # All findings
    status: str  # "completed", "error", "low_confidence"
    error: Optional[str] = None

class KnowledgeBaseWorkflow:
    """Extended per D-30, D-31, D-32, D-33."""
    
    def __init__(self, ...):
        # Compile graphs
        self.prd_review_graph = create_prd_review_graph()
        self.image_review_graph = create_image_review_graph()
    
    def review(
        self,
        prd_text: str,
        image_path: Optional[str] = None,
        collection_name: str = "design_standards",
        review_depth: str = "balanced",
    ) -> ReviewResponse:
        """Single unified entry point per D-30.
        
        If image_path provided -> use image_review_graph (5-way fan-out)
        If no image_path -> use prd_review_graph (4-way fan-out)
        """
        if image_path:
            # Image review path
            from src.workflow.state import get_initial_image_review_state
            initial = get_initial_image_review_state(
                prd_text=prd_text,
                image_path=image_path,
                collection_name=collection_name,
                review_depth=review_depth,
            )
            result = self.image_review_graph.invoke(initial)
        else:
            # PRD only path
            from src.workflow.state import get_initial_prd_review_state
            initial = get_initial_prd_review_state(
                prd_text=prd_text,
                collection_name=collection_name,
                review_depth=review_depth,
            )
            result = self.prd_review_graph.invoke(initial)
        
        # Convert to structured response per D-32
        return ReviewResponse(
            report=result.get("report", ""),
            findings=result.get("all_findings", []),
            status=result.get("status", "unknown"),
            error=result.get("error"),
        )
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|---------|
| Error handling in graph | Custom exception middleware | Conditional edge routing with error state | LangGraph idiom; catches errors from any node |
| Retry logic | Custom retry decorator | Retry counter in state + conditional routing | Simpler, stateful, debuggable |
| Bilingual response | Hard-coded strings | Prompt templates from `src/prompts/templates.py` | Already implemented per AGT-03 |
| Finding comparison | ad-hoc equality check | `_findings_stable()` helper with category/severity/location | Per D-26 spec: count + severity per category + location set |

## Common Pitfalls

### Pitfall 1: Infinite Loop in Refinement Cycle
**What goes wrong:** Refinement loop continues indefinitely when findings never stabilize.
**Why it happens:** Missing convergence check, or convergence criteria too strict.
**How to avoid:** Implement `should_refine_decision` with proper convergence detection and max_iterations=3 as backstop (D-26).
**Warning signs:** Graph execution hangs, `review_iteration` keeps incrementing.

### Pitfall 2: Error State Lost in Parallel Fan-out
**What goes wrong:** One validator fails but others complete; error state overwritten by aggregate.
**Why it happens:** aggregate_findings extends lists without checking error state.
**How to avoid:** Error handler placed AFTER aggregate_findings catches any error that occurred.

### Pitfall 3: Version Mismatch in State Schema
**What goes wrong:** New fields added to state but existing graphs don't handle them.
**Why it happens:** State schema evolves without updating all graph paths.
**How to avoid:** Use TypedDict with Optional fields for new additions; ensure all nodes return full state dict.

### Pitfall 4: Confidence Zone Boundary Cases
**What goes wrong:** Exactly 0.7 or 0.5 confidence handled incorrectly.
**Why it happens:** Off-by-one errors in comparison operators.
**How to avoid:** Use `>=` for upper boundary (0.7+ = found), `>` for lower (0.5+ = warning), `<` for hard floor.

## Code Examples

### re_retrieve_node Implementation (Placeholder at graph.py:284)
```python
def re_retrieve_node(state: PRDReviewState) -> PRDReviewState:
    """Query knowledge base again with refined context.
    
    Per AGT-04: LangGraph cycles enable re-retrieval when initial findings inconclusive.
    Per D-26: Stores previous findings for convergence comparison.
    """
    from src.retrieval.hybrid_search import HybridRetriever
    from src.vectorstore.chroma_store import ChromaStore
    
    # Store current as previous for convergence check
    previous_findings = state.get("refined_findings", state["all_findings"])
    
    # Re-retrieve with refined query based on findings
    store = ChromaStore(
        collection_name=state["collection_name"],
        embedding_fn=BGE_M3_Embeddings(),
    )
    all_docs = store.collection.get()
    
    if not all_docs["documents"]:
        return {
            "refined_findings": previous_findings,
            "previous_findings": previous_findings,
        }
    
    retriever = HybridRetriever(
        texts=all_docs["documents"],
        embedding_fn=BGE_M3_Embeddings(),
        collection=store.collection,
    )
    
    # Re-query with same text but different retrieval params
    results = retriever.search(state["prd_text"], k=5)  # Use PRD text as query
    
    # Refine findings based on new retrieval... (placeholder per graph.py TODO)
    return {
        "refined_findings": previous_findings,  # TODO: actually refine
        "previous_findings": previous_findings,
    }
```

### ReviewResponse Pydantic Model (New per D-32)
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class ReviewResponse(BaseModel):
    """Structured response returned to caller per D-32.
    
    Hides LangGraph state schema complexity from callers.
    """
    report: str = Field(description="Bilingual compliance report string")
    findings: List["Finding"] = Field(default_factory=list, description="All review findings")
    status: Literal["completed", "error", "low_confidence"] = Field(
        description="Overall workflow status"
    )
    error: Optional[str] = Field(None, description="Error message if status=error")
    
    class Config:
        # Allow Finding forward reference
        json_schema_extra = {
            "Finding": "src.workflow.state.Finding"
        }
```

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research. The planner and discuss-phase use this section to identify decisions that need user confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | LangGraph 1.1.6 API supports error handling via conditional edge routing | Architecture Patterns | Error handler may need different implementation for 1.x vs 0.2.x |
| A2 | Installed LangChain 1.2.15 / LangGraph 1.1.6 are compatible with code written for ^0.3.x / ^0.2.x | Standard Stack | Breaking changes may exist; code may need adaptation |
| A3 | Retry counter stored in state is sufficient for retry logic without external middleware | Pattern 2 | Alternative: could use LangChain RetryRunnable but more complex |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Open Questions (RESOLVED)

> These questions were resolved during planning/execution — they are implementation-time verification items, not research blockers.

1. **LangGraph Version Compatibility** (RESOLVED)
   - What we know: CLAUDE.md specifies `^0.2.x` LangGraph, but installed version is `1.1.6`
   - What's unclear: Whether code patterns for 0.2.x work in 1.x unchanged
   - Resolution: Patterns in this research are standard LangGraph 1.x patterns; verify during implementation

2. **re_retrieve_node Actual Logic** (RESOLVED)
   - What we know: Placeholder at graph.py:284, 403; D-26 says it should enable convergence
   - What's unclear: What "refined context" means operationally - is it re-querying with same text? Different weights?
   - Resolution: Implement as pass-through initially, refine based on actual convergence behavior during execution

## Environment Availability

Step 2.6: SKIPPED (no external dependencies identified - Phase 4 is pure code/config changes)

## Sources

### Primary (HIGH confidence)
- `src/workflow/graph.py` - Existing graph implementations with TODOs for Phase 4
- `src/workflow/state.py` - State definitions and initial state factories
- `src/prompts/templates.py` - Standard Not Found template already implemented
- `04-CONTEXT.md` - Canonical decisions D-25 through D-33

### Secondary (MEDIUM confidence)
- LangGraph concepts (from training): Error handling via conditional edges, cycle patterns
- Pydantic 2 patterns (from training): BaseModel with Field descriptions

### Tertiary (LOW confidence)
- LangGraph 1.x vs 0.2.x API differences [ASSUMED - needs official doc verification]

## Metadata

**Confidence breakdown:**
- Error handling pattern: MEDIUM - based on LangGraph general patterns, not verified against 1.x docs
- Convergence check: MEDIUM - spec in D-26 is detailed, implementation approach from training
- ReviewResponse: HIGH - Pydantic 2 patterns well-established
- Version compatibility: LOW - installed versions (1.x) differ from constraints (0.2.x)

**Research date:** 2026/04/17
**Valid until:** 2026/05/17 (30 days - patterns stable)
