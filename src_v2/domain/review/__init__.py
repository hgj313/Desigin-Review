"""Review bounded context - PRD and prototype review."""

from src_v2.domain.review.entities import ConsistencyIssue, CrossReference, VagueLanguagePattern
from src_v2.domain.review.repositories import IStandardRepository
from src_v2.domain.review.services import (
    IPRDReviewerService,
    IPrototypeReviewerService,
    IReviewAggregationService,
)

__all__ = [
    # entities
    "VagueLanguagePattern",
    "CrossReference",
    "ConsistencyIssue",
    # protocols
    "IPRDReviewerService",
    "IPrototypeReviewerService",
    "IReviewAggregationService",
    # re-exported from ingestion
    "IStandardRepository",
]
