"""LangGraph State definition for the review workflow.

This module defines the ReviewState TypedDict that flows through the
LangGraph workflow. It documents field ownership per PITFALLS.md PP-04.

References:
- ARCHITECTURE.md: LangGraph State Schema section
- STACK.md: LangGraph state management
- PITFALLS.md: PP-04 state field ownership documentation
"""

from typing import TypedDict, Annotated, Optional
from typing import Any
import operator

from src.domains.shared import Finding


class ReviewState(TypedDict, total=False):
    """Main state that flows through the LangGraph review workflow.

    Field Ownership (per PP-04):
    - start node writes: document_path, document_type, image_paths
    - retrieve node writes: retrieved_standards
    - prd_evaluate node writes: prd_findings
    - proto_evaluate node writes: proto_findings
    - report node writes: final_report

    All fields use operator.add for list accumulation except
    primitive fields which are overwritten.
    """

    # ===== Input Fields =====
    # Written by: start node
    # Input document path (PRD file or image)
    document_path: str

    # Document type: "prd" | "prototype" | "both"
    document_type: str

    # List of prototype image paths (empty if no prototype)
    image_paths: list[str]

    # ===== Context Accumulated During Review =====
    # Written by: retrieve node
    # Retrieved standards keyed by dimension
    retrieved_standards: dict[str, list[str]]

    # Written by: prd_evaluate node (PP-05: source_context labeling)
    # PRD review findings
    prd_findings: Annotated[list[Finding], operator.add]

    # Written by: proto_evaluate node (PP-05: source_context labeling)
    # Prototype review findings
    proto_findings: Annotated[list[Finding], operator.add]

    # ===== LLM Compiler State =====
    # Written by: think/plan/execute/branch nodes
    # History of all tool calls made
    tool_history: Annotated[list[dict], operator.add]

    # Current tool execution plan
    current_plan: list[str]

    # Loop counter to prevent infinite loops (PP-01: MAX_LOOPS=10)
    loop_count: int

    # ===== Output =====
    # Written by: report node
    # Final compliance report
    final_report: Optional[dict]

    # ===== State Metadata =====
    # Whether prototype was analyzed (for summary)
    prototype_analyzed: bool


# State ownership documentation for reference
STATE_OWNERSHIP = {
    "start": ["document_path", "document_type", "image_paths"],
    "retrieve": ["retrieved_standards"],
    "prd_evaluate": ["prd_findings"],
    "proto_evaluate": ["proto_findings"],
    "report": ["final_report"],
    "compiler": ["tool_history", "current_plan", "loop_count"],
}

# MAX_LOOPS as specified in PITFALLS.md PP-01
MAX_LOOPS = 10
