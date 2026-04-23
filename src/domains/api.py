"""Review API - Entry point for the design doc review agent.

Simple usage:
    from src.domains.api import review

    result = review("path/to/prd.md", document_type="prd")
    print(result)
"""

from typing import Optional
import uuid

from src.domains.state import ReviewState
from src.domains.compiler.graph import review_workflow
from src.domains.shared import Finding


def review(
    document_path: str,
    document_type: str = "prd",
    image_paths: Optional[list[str]] = None,
    prototype_analyzed: bool = False,
) -> dict:
    """Review a PRD document or prototype against design standards.

    Args:
        document_path: Path to PRD file or prototype image(s)
        document_type: "prd", "prototype", or "both"
        image_paths: List of prototype image paths (if document_type includes prototype)
        prototype_analyzed: Whether prototype images were provided

    Returns:
        Dict with review results:
        {
            "id": report_id,
            "status": "completed" | "error",
            "summary": {...},
            "findings": [...],
            "final_report": {...}
        }
    """
    # Create initial state
    initial_state: ReviewState = {
        "document_path": document_path,
        "document_type": document_type,
        "image_paths": image_paths or [],
        "prd_findings": [],
        "proto_findings": [],
        "retrieved_standards": {},
        "tool_history": [],
        "current_plan": [],
        "loop_count": 0,
        "final_report": None,
        "prototype_analyzed": prototype_analyzed,
    }

    # Run workflow
    thread_id = f"review-{uuid.uuid4().hex[:8]}"

    try:
        result = review_workflow.invoke(
            initial_state,
            config={"configurable": {"thread_id": thread_id}},
        )

        # Format response
        return {
            "id": result.get("final_report", {}).get("id", thread_id) if result.get("final_report") else thread_id,
            "status": "completed",
            "summary": {
                "prd_findings_count": len(result.get("prd_findings", [])),
                "prototype_findings_count": len(result.get("proto_findings", [])),
                "tool_history_count": len(result.get("tool_history", [])),
                "loop_count": result.get("loop_count", 0),
            },
            "findings": {
                "prd": result.get("prd_findings", []),
                "prototype": result.get("proto_findings", []),
            },
            "final_report": result.get("final_report"),
        }

    except Exception as e:
        return {
            "id": thread_id,
            "status": "error",
            "error": str(e),
            "summary": {
                "prd_findings_count": len(initial_state.get("prd_findings", [])),
                "prototype_findings_count": len(initial_state.get("proto_findings", [])),
            },
            "findings": {
                "prd": initial_state.get("prd_findings", []),
                "prototype": initial_state.get("proto_findings", []),
            },
            "final_report": None,
        }


__all__ = ["review"]
