"""PRD document review module.

Public-facing PRD review workflow wrapper with single-entry point
for reviewing PRD documents against design standards knowledge base.
"""

from src.workflow.state import get_initial_prd_review_state
from src.workflow.graph import create_prd_review_graph


class PRDReviewWorkflow:
    """Public-facing PRD review workflow.

    Provides simple interface for reviewing PRD documents against
    design standards knowledge base.

    Usage:
        workflow = PRDReviewWorkflow(collection_name="design_standards")
        result = workflow.review("# Overview\n\nPRD content here...", review_depth="balanced")
        print(result["report"])
    """

    def __init__(self, collection_name: str = "design_standards"):
        """Initialize PRD review workflow.

        Args:
            collection_name: Chroma collection name for knowledge base.
        """
        self.collection_name = collection_name
        self.graph = create_prd_review_graph()

    def review(self, prd_text: str, review_depth: str = "balanced") -> dict:
        """Execute PRD review workflow.

        Args:
            prd_text: Raw PRD document text.
            review_depth: "fast", "balanced", or "thorough" (default: balanced).

        Returns:
            Final state dict with report field containing Markdown compliance report.
        """
        # Validate review_depth
        if review_depth not in ("fast", "balanced", "thorough"):
            raise ValueError(f"Invalid review_depth: {review_depth}")

        # Initialize state
        initial = get_initial_prd_review_state(
            prd_text=prd_text,
            collection_name=self.collection_name,
            review_depth=review_depth,
        )

        # Execute workflow
        result = self.graph.invoke(initial)

        return result


__all__ = ["PRDReviewWorkflow"]
