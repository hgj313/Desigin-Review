"""Review agent state schema with partitioned findings per D-03."""
from typing import TypedDict, Annotated, Literal
import operator

from src_v2.domain.shared.entities import Finding

__all__ = ["ReviewState"]


class ReviewState(TypedDict):
    """LangGraph state for review workflow.

    Per D-03: State partitioned into separate areas for each review type.
    Per D-05: review_types list determines which branches execute.

    Uses Annotated with operator.add for thread-safe accumulation
    in parallel branches per LangGraph documentation.
    """
    document_path: str
    review_types: list[Literal["prd", "prototype"]]
    prd_findings: Annotated[list[Finding], operator.add]
    proto_findings: Annotated[list[Finding], operator.add]
    compliance_score: int | None
    report: dict