"""Findings aggregation node.

Reduces 4 parallel validation streams into single all_findings list.
This is the JOIN node in the fan-out/join pattern.
"""

from typing import List

from src.workflow.state import PRDReviewState, Finding


def aggregate_findings_node(state: PRDReviewState) -> PRDReviewState:
    """Aggregate findings from all 4 parallel validators.

    This is the critical connection point where parallel execution
    results are joined. Uses extend to avoid losing any parallel outputs.

    Args:
        state: PRDReviewState with 4 finding lists populated.

    Returns:
        Updated state with all_findings list and status.
    """
    # Collect all findings from the 4 parallel validation streams
    all_findings: List[Finding] = []
    all_findings.extend(state.get("structure_findings", []))
    all_findings.extend(state.get("terminology_findings", []))
    all_findings.extend(state.get("completeness_findings", []))
    all_findings.extend(state.get("formatting_findings", []))

    # Determine status based on findings
    if all_findings:
        status = "validated"
    else:
        status = "validated_clean"

    return {
        **state,
        "all_findings": all_findings,
        "status": status,
    }


__all__ = ["aggregate_findings_node"]
