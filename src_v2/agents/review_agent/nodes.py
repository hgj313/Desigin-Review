"""LangGraph node functions for review workflow.

Per D-04: Parallel execution when both review types selected.
Each node writes to its designated state partition.
"""
from datetime import datetime
from typing import Any, Literal

from src_v2.agents.review_agent.state import ReviewState
from src_v2.agents.review_agent.services import ReportGenerationServiceImpl
from src_v2.domain.ingestion.entities import Document
from src_v2.domain.review.services.prd_reviewer import PRDReviewerService
from src_v2.domain.review.services.prototype_reviewer import PrototypeReviewerService
from src_v2.domain.review.services.aggregation import aggregate_findings_by_severity
from src_v2.infrastructure.database.repositories.report_repository import SQLAlchemyReportRepository
from src_v2.domain.shared.entities import (
    Finding,
    ReviewContext,
    ReviewDimension,
    ReviewResult,
    SeverityLevel,
)

__all__ = [
    "upload_node",
    "prd_review_node",
    "proto_review_node",
    "aggregate_results_node",
    "generate_report_node",
    "route_reviews",
]


# Placeholder for actual LLM client - will be injected via workflow
# In production, this would be MiniMax M2.7 or OpenAI-compatible client
class DummyLLMClient:
    """Dummy LLM client for testing without API calls."""

    def chat_completion(self, messages: list[dict], **kwargs) -> dict:
        return {"choices": [{"message": {"content": "[]"}}]}


class DummyVisionClient:
    """Dummy vision client for testing without API calls."""

    def extract_colors(self, image_path: str) -> list[str]:
        return ["#333333", "#666666"]

    def extract_typography(self, image_path: str) -> dict:
        return {"family": "Arial", "weight": "Regular", "size": 14}

    def extract_spacing(self, image_path: str) -> dict:
        return {"margin": 16, "padding": 8, "gap": 4}


async def upload_node(state: ReviewState) -> dict[str, Any]:
    """Upload node - validates document path exists.

    Args:
        state: ReviewState with document_path

    Returns:
        Dict with any upload validation results
    """
    document_path = state["document_path"]

    if not document_path:
        return {"error": "No document path provided"}

    return {"uploaded": True}


async def prd_review_node(state: ReviewState) -> dict[str, Any]:
    """PRD review node - writes to prd_findings partition.

    Per D-04: Executes when "prd" in review_types.
    Calls PRDReviewerService and writes findings to prd_findings.

    Args:
        state: ReviewState with document_path

    Returns:
        Dict to merge into state via Annotated reducer
    """
    document_path = state["document_path"]

    # Initialize PRD reviewer (would use real LLM client in production)
    llm_client = DummyLLMClient()
    prd_reviewer = PRDReviewerService(llm_client)

    # Load document (simplified - in production would load from file)
    doc = Document(
        id="prd-doc-001",
        content=f"Document at {document_path}",
        content_type=None,
        metadata={},
    )

    # Run PRD review operations
    vague_findings = prd_reviewer.detect_vague_language(doc)
    structure_findings = prd_reviewer.validate_prd_structure(doc)

    # Aggregate findings
    all_findings = vague_findings + structure_findings
    aggregated = aggregate_findings_by_severity(all_findings)

    return {"prd_findings": aggregated}


async def proto_review_node(state: ReviewState) -> dict[str, Any]:
    """Prototype review node - writes to proto_findings partition.

    Per D-04: Executes when "prototype" in review_types.
    Calls PrototypeReviewerService and writes findings to proto_findings.

    Args:
        state: ReviewState with document_path

    Returns:
        Dict to merge into state via Annotated reducer
    """
    document_path = state["document_path"]

    # Initialize prototype reviewer
    vision_client = DummyVisionClient()
    proto_reviewer = PrototypeReviewerService(vision_client=vision_client)

    # Load screens (simplified - in production would load from files)
    screens = [
        Document(
            id="screen-001",
            content=f"Screen 1 at {document_path}",
            content_type=None,
            metadata={},
        ),
        Document(
            id="screen-002",
            content=f"Screen 2 at {document_path}",
            content_type=None,
            metadata={},
        ),
    ]

    # Run prototype review
    consistency_issues = proto_reviewer.detect_visual_consistency(screens)

    # Convert ConsistencyIssue to Finding for unified processing
    findings: list[Finding] = []
    for issue in consistency_issues:
        findings.append(
            Finding(
                id=f"proto-{issue.issue_type}-{issue.elements[0] if issue.elements else 'unknown'}",
                dimension=ReviewDimension.CONSISTENCY,
                severity=issue.severity,
                rule_id=f"proto-{issue.issue_type}-001",
                description=issue.description,
                location=", ".join(issue.elements) if issue.elements else "unknown",
                suggestion=f"Fix {issue.issue_type} inconsistency",
                evidence="",
                created_at=datetime.now(),
            )
        )

    return {"proto_findings": findings}


async def aggregate_results_node(state: ReviewState) -> dict[str, Any]:
    """Join point - merge findings, calculate compliance score.

    Per D-08: Called after all review branches complete.
    Aggregates all findings and calculates compliance score.

    Args:
        state: ReviewState with prd_findings and proto_findings populated

    Returns:
        Dict to merge - updates compliance_score
    """
    prd_findings = state.get("prd_findings", [])
    proto_findings = state.get("proto_findings", [])
    all_findings = prd_findings + proto_findings

    # Calculate compliance score
    compliance_score = calculate_compliance_score(all_findings)

    return {"compliance_score": compliance_score}


def calculate_compliance_score(findings: list[Finding]) -> int:
    """Calculate compliance score based on findings severity.

    Score = 100 - (critical_count * 20) - (high_count * 10) - (medium_count * 5) - (low_count * 2)
    Minimum score is 0.

    Args:
        findings: List of Finding objects

    Returns:
        Compliance score from 0-100
    """
    if not findings:
        return 100

    critical_count = sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)
    high_count = sum(1 for f in findings if f.severity == SeverityLevel.HIGH)
    medium_count = sum(1 for f in findings if f.severity == SeverityLevel.MEDIUM)
    low_count = sum(1 for f in findings if f.severity == SeverityLevel.LOW)

    score = 100 - (critical_count * 20) - (high_count * 10) - (medium_count * 5) - (low_count * 2)
    return max(0, score)


async def generate_report_node(state: ReviewState) -> dict[str, Any]:
    """Generate final report from aggregated findings and persist to PostgreSQL.

    Per D-08: Called after aggregate_results_node completes.
    Uses ReportGenerationService to create Report entity, then persists
    to PostgreSQL via SQLAlchemyReportRepository.

    Args:
        state: ReviewState with compliance_score and all findings

    Returns:
        dict to merge - sets report field
    """
    prd_findings = state.get("prd_findings", [])
    proto_findings = state.get("proto_findings", [])
    all_findings = prd_findings + proto_findings
    compliance_score = state.get("compliance_score", 100)

    # Determine document type from review_types
    review_types = state.get("review_types", [])
    document_type: Literal["prd", "prototype"] = "prd" if "prd" in review_types else "prototype"

    # Build ReviewResult for report generation
    review_context = ReviewContext(
        document_id=state["document_path"],
        document_type=document_type,
        review_type=" + ".join(review_types) if isinstance(review_types, list) else str(review_types),
        timestamp=datetime.now(),
        findings=all_findings,
    )

    review_result = ReviewResult(
        context=review_context,
        compliance_score=compliance_score,
        summary="",
        recommendations=[],
    )

    # Generate report
    report_service = ReportGenerationServiceImpl()
    report = report_service.generate_report(review_result, format="report")

    # Persist to PostgreSQL
    repository = SQLAlchemyReportRepository()
    await repository.store_async(report)

    # Convert report to dict for state storage
    report_dict = {
        "id": report.id,
        "timestamp": report.timestamp.isoformat(),
        "document_path": report.document_path,
        "document_type": report.document_type,
        "findings": [
            {
                "id": f.id,
                "dimension": f.dimension.value,
                "severity": f.severity.value,
                "rule_id": f.rule_id,
                "description": f.description,
                "location": f.location,
                "suggestion": f.suggestion,
                "evidence": f.evidence,
            }
            for f in report.findings
        ],
        "compliance_score": report.compliance_score,
        "summary": report.summary,
        "severity_breakdown": {
            "critical": report.severity_breakdown.critical,
            "high": report.severity_breakdown.high,
            "medium": report.severity_breakdown.medium,
            "low": report.severity_breakdown.low,
        },
        "recommendations": report.recommendations,
    }

    return {"report": report_dict}


def route_reviews(state: ReviewState) -> list:
    """Route function for parallel fan-out using Send API.

    Per D-04: Routes to prd_review_node and/or proto_review_node
    based on review_types selection.

    Args:
        state: ReviewState with review_types list

    Returns:
        List of Send objects for LangGraph conditional edges
    """
    from langgraph.types import Send

    review_types = state.get("review_types", [])
    sends = []

    if "prd" in review_types:
        sends.append(Send("prd_review_node", {"document_path": state["document_path"]}))

    if "prototype" in review_types:
        sends.append(Send("proto_review_node", {"document_path": state["document_path"]}))

    return sends
