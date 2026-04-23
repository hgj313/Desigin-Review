"""SQLAlchemy ORM models for database tables."""
from datetime import datetime
from typing import Any

from sqlalchemy import String, DateTime, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from src_v2.infrastructure.database.base import Base


class ReportModel(Base):
    """SQLAlchemy model for reports table."""

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    document_path: Mapped[str] = mapped_column(String(512), nullable=False)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    compliance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity_breakdown: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "document_path": self.document_path,
            "document_type": self.document_type,
            "findings": self.findings,
            "compliance_score": self.compliance_score,
            "summary": self.summary,
            "severity_breakdown": self.severity_breakdown,
            "recommendations": self.recommendations,
        }
