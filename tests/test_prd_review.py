"""Integration tests for PRD review workflow."""

import pytest
from src.prd.review import PRDReviewWorkflow
from src.workflow.state import PRDReviewState

# Sample PRD with known issues
SAMPLE_PRD = """
# Product Requirements Document

# Overview
This document describes the requirements for the new feature.

# User Stories
- User can login
- User can view dashboard
- User can TBD

# Acceptance Criteria
- System should work
- Performance should be good
"""


def test_review_workflow():
    """Test complete PRD review workflow."""
    workflow = PRDReviewWorkflow(collection_name="design_standards")

    # Execute review
    result = workflow.review(SAMPLE_PRD, review_depth="fast")

    # Verify output structure
    assert "report" in result
    assert "all_findings" in result or "refined_findings" in result
    assert result["status"] == "completed"

    # Verify report is Markdown
    report = result["report"]
    assert "# PRD Compliance Review Report" in report
    assert "# PRD 合规审查报告" in report
    assert "Critical" in report or "Major" in report or "Minor" in report

    print("Report preview:")
    print(report[:500])


def test_review_depth_parameter():
    """Test review_depth parameter affects workflow."""
    workflow = PRDReviewWorkflow(collection_name="design_standards")

    # Fast review
    result_fast = workflow.review(SAMPLE_PRD, review_depth="fast")
    assert result_fast["review_depth"] == "fast"
    assert result_fast["max_iterations"] == 1

    # Thorough review
    result_thorough = workflow.review(SAMPLE_PRD, review_depth="thorough")
    assert result_thorough["review_depth"] == "thorough"
    assert result_thorough["max_iterations"] == 3


def test_invalid_review_depth():
    """Test that invalid review_depth raises ValueError."""
    workflow = PRDReviewWorkflow(collection_name="design_standards")

    with pytest.raises(ValueError, match="Invalid review_depth"):
        workflow.review(SAMPLE_PRD, review_depth="invalid")


if __name__ == "__main__":
    test_review_workflow()
    test_review_depth_parameter()
    test_invalid_review_depth()
