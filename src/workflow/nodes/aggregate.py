"""Findings aggregation node.

Reduces 4 parallel validation streams into single all_findings list.
This is the JOIN node in the fan-out/join pattern.

Per D-25: Implements retry logic for transient errors with exponential backoff.
"""

import time
from typing import List, Union

from src.workflow.state import PRDReviewState, ImageReviewState, Finding


def aggregate_findings_node(state: PRDReviewState) -> PRDReviewState:
    """Aggregate findings from all 4 parallel validators.

    This is the critical connection point where parallel execution
    results are joined. Uses extend to avoid losing any parallel outputs.

    Per D-25: Implements retry logic for transient errors with exponential backoff.
    Transient errors retry 3 times total (2 attempts) with backoff (2s, 4s, 8s).
    Programming errors fail immediately and route to error_handler.

    Args:
        state: PRDReviewState with 4 finding lists populated.

    Returns:
        Updated state with all_findings list and status.
    """
    # Check for errors from validators
    error = state.get("error")
    if error:
        # Check retry count for transient errors
        retry_count = state.get("retry_count", 0)

        # Transient errors: network, API, rate limit - retry with exponential backoff
        transient_keywords = ["timeout", "rate limit", "connection", "network", "429", "500", "502", "503", "504"]
        is_transient = any(kw in error.lower() for kw in transient_keywords)

        if is_transient and retry_count < 2:
            # Exponential backoff: 2s, 4s, 8s
            sleep_time = 2 ** (retry_count + 1)
            time.sleep(sleep_time)
            return {**state, "retry_count": retry_count + 1, "error": None}  # Clear error, will retry
        elif is_transient:
            # Retries exhausted - set permanent error
            return {**state, "error": f"Retries exhausted: {error}"}
        else:
            # Programming error - fail immediately, keep error for error_handler
            return {**state, "error": error}

    # Normal aggregation logic
    all_findings: List[Finding] = []
    all_findings.extend(state.get("structure_findings", []))
    all_findings.extend(state.get("terminology_findings", []))
    all_findings.extend(state.get("completeness_findings", []))
    all_findings.extend(state.get("formatting_findings", []))

    # Determine status based on findings
    status = "validated" if all_findings else "validated_clean"

    return {
        **state,
        "all_findings": all_findings,
        "status": status,
    }


def aggregate_image_findings_node(state: ImageReviewState) -> ImageReviewState:
    """Aggregate all image review findings into all_findings list.

    Combines findings from all 5 image validators:
    - color_findings (IMG-01, IMG-02)
    - typography_findings (IMG-03)
    - spacing_findings (IMG-04)
    - accessibility_findings (IMG-05)
    - assumption_findings (PRD-05)

    Plus inherited PRD findings from PRDReviewState:
    - structure_findings
    - terminology_findings
    - completeness_findings
    - formatting_findings

    Per D-25: Implements retry logic for transient errors with exponential backoff.

    Args:
        state: ImageReviewState with all finding lists populated.

    Returns:
        Updated state with aggregated all_findings.
    """
    # Check for errors from validators
    error = state.get("error")
    if error:
        # Check retry count for transient errors
        retry_count = state.get("retry_count", 0)

        # Transient errors: network, API, rate limit - retry with exponential backoff
        transient_keywords = ["timeout", "rate limit", "connection", "network", "429", "500", "502", "503", "504"]
        is_transient = any(kw in error.lower() for kw in transient_keywords)

        if is_transient and retry_count < 2:
            # Exponential backoff: 2s, 4s, 8s
            sleep_time = 2 ** (retry_count + 1)
            time.sleep(sleep_time)
            return {**state, "retry_count": retry_count + 1, "error": None}  # Clear error, will retry
        elif is_transient:
            # Retries exhausted - set permanent error
            return {**state, "error": f"Retries exhausted: {error}"}
        else:
            # Programming error - fail immediately, keep error for error_handler
            return {**state, "error": error}

    all_findings: List[Finding] = []
    # Inherited PRD findings
    all_findings.extend(state.get("structure_findings", []))
    all_findings.extend(state.get("terminology_findings", []))
    all_findings.extend(state.get("completeness_findings", []))
    all_findings.extend(state.get("formatting_findings", []))
    # Image-specific findings
    all_findings.extend(state.get("color_findings", []))
    all_findings.extend(state.get("typography_findings", []))
    all_findings.extend(state.get("spacing_findings", []))
    all_findings.extend(state.get("accessibility_findings", []))
    all_findings.extend(state.get("assumption_findings", []))

    # Determine status based on findings
    status = "validated" if all_findings else "validated_clean"

    return {
        **state,
        "all_findings": all_findings,
        "status": status,
    }


__all__ = ["aggregate_findings_node", "aggregate_image_findings_node"]
