"""SQLAlchemy implementation of IReportRepository."""
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src_v2.domain.reporting.entities import Report, ReportSeverityBreakdown
from src_v2.domain.reporting.repositories import IReportRepository
from src_v2.domain.shared.entities import Finding, SeverityLevel, ReviewDimension
from src_v2.infrastructure.database.base import AsyncSessionMaker
from src_v2.infrastructure.database.models import ReportModel


class SQLAlchemyReportRepository(IReportRepository):
    """SQLAlchemy implementation of report repository."""

    def __init__(self, session_maker: type[AsyncSession] = AsyncSessionMaker):
        self._session_maker = session_maker

    def _report_to_model(self, report: Report) -> ReportModel:
        """Convert Report entity to ReportModel for storage."""
        return ReportModel(
            id=report.id,
            timestamp=report.timestamp,
            document_path=report.document_path,
            document_type=report.document_type,
            findings=[self._finding_to_dict(f) for f in report.findings],
            compliance_score=report.compliance_score,
            summary=report.summary,
            severity_breakdown={
                "critical": report.severity_breakdown.critical,
                "high": report.severity_breakdown.high,
                "medium": report.severity_breakdown.medium,
                "low": report.severity_breakdown.low,
            },
            recommendations=report.recommendations,
        )

    def _model_to_report(self, model: ReportModel) -> Report:
        """Convert ReportModel back to Report entity."""
        severity_breakdown = ReportSeverityBreakdown(
            critical=model.severity_breakdown.get("critical", 0),
            high=model.severity_breakdown.get("high", 0),
            medium=model.severity_breakdown.get("medium", 0),
            low=model.severity_breakdown.get("low", 0),
        )
        findings = [self._dict_to_finding(f) for f in model.findings]
        return Report(
            id=model.id,
            timestamp=model.timestamp,
            document_path=model.document_path,
            document_type=model.document_type,  # type: ignore
            findings=findings,
            compliance_score=model.compliance_score,
            summary=model.summary,
            severity_breakdown=severity_breakdown,
            recommendations=model.recommendations,
        )

    def _finding_to_dict(self, finding: Finding) -> dict[str, Any]:
        """Convert Finding entity to dict for JSONB storage."""
        return {
            "id": finding.id,
            "dimension": finding.dimension.value,
            "severity": finding.severity.value,
            "rule_id": finding.rule_id,
            "description": finding.description,
            "location": finding.location,
            "suggestion": finding.suggestion,
            "evidence": finding.evidence,
            "created_at": finding.created_at.isoformat() if finding.created_at else None,
        }

    def _dict_to_finding(self, data: dict[str, Any]) -> Finding:
        """Convert dict back to Finding entity."""
        return Finding(
            id=data["id"],
            dimension=ReviewDimension(data["dimension"]),
            severity=SeverityLevel(data["severity"]),
            rule_id=data["rule_id"],
            description=data["description"],
            location=data["location"],
            suggestion=data["suggestion"],
            evidence=data["evidence"],
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
        )

    def store(self, report: Report) -> None:
        """Store a report (async, must be called with await)."""
        raise NotImplementedError("store must be called with await in async context")

    async def store_async(self, report: Report) -> None:
        """Store a report asynchronously."""
        async with self._session_maker() as session:
            model = self._report_to_model(report)
            session.add(model)
            await session.commit()

    def find_by_id(self, id: str) -> Report | None:
        """Find a report by ID (async)."""
        raise NotImplementedError("find_by_id must be called with await")

    async def find_by_id_async(self, id: str) -> Report | None:
        """Find a report by ID asynchronously."""
        async with self._session_maker() as session:
            result = await session.execute(
                select(ReportModel).where(ReportModel.id == id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._model_to_report(model)

    def find_by_document_path(self, path: str) -> list[Report]:
        """Find all reports for a document path (async)."""
        raise NotImplementedError("find_by_document_path must be called with await")

    async def find_by_document_path_async(self, path: str) -> list[Report]:
        """Find all reports for a document path asynchronously."""
        async with self._session_maker() as session:
            result = await session.execute(
                select(ReportModel)
                .where(ReportModel.document_path == path)
                .order_by(ReportModel.timestamp.desc())
            )
            models = result.scalars().all()
            return [self._model_to_report(m) for m in models]

    def find_latest(self, path: str) -> Report | None:
        """Find the most recent report for a document path (async)."""
        raise NotImplementedError("find_latest must be called with await")

    async def find_latest_async(self, path: str) -> Report | None:
        """Find the most recent report for a document path asynchronously."""
        async with self._session_maker() as session:
            result = await session.execute(
                select(ReportModel)
                .where(ReportModel.document_path == path)
                .order_by(ReportModel.timestamp.desc())
                .limit(1)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._model_to_report(model)
