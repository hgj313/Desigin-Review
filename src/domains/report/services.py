"""Report Domain Services - Severity calculation and report generation.

Services:
- SeverityCalculator: Calculates severity from violation impact
- FindingAggregator: Aggregates and deduplicates findings from all contexts
- BilingualReportFormatter: Formats reports in Chinese/English

References:
- ARCHITECTURE.md: Report Context Services section
- PITFALLS.md: PP-05 source_context labeling
"""

from typing import Optional
from datetime import datetime

from src.domains.report.entities import Report, ReportSummary
from src.domains.shared import Finding, SeverityLevel, ReviewDimension


class SeverityCalculator:
    """Calculates severity based on violation impact.

    Severity rules:
    - CRITICAL: Violation prevents design system usage
    - HIGH: Significant deviation from standard
    - MEDIUM: Minor deviation, advisory
    - LOW: Suggestion, not violation
    """

    # Severity weights for compliance score
    WEIGHTS = {
        SeverityLevel.CRITICAL: 10,
        SeverityLevel.HIGH: 5,
        SeverityLevel.MEDIUM: 2,
        SeverityLevel.LOW: 1,
    }

    def calculate(self, finding: Finding, context: Optional[dict] = None) -> SeverityLevel:
        """Calculate severity for a finding.

        Args:
            finding: The finding to evaluate
            context: Additional context (optional)

        Returns:
            SeverityLevel enum value
        """
        # Rule-based severity calculation
        # Full implementation would use LLM for complex cases

        rule_id = finding.rule_id

        # Critical rules
        if rule_id.startswith("prd-struct-001"):  # Missing required section
            return SeverityLevel.HIGH
        if rule_id.startswith("proto-a11y-001"):  # Contrast issue
            return SeverityLevel.HIGH

        # High rules
        if rule_id.startswith("prd-struct-002"):  # Heading hierarchy
            return SeverityLevel.MEDIUM
        if rule_id.startswith("proto-layout-001"):  # Grid alignment
            return SeverityLevel.MEDIUM

        # Medium/Low rules
        if rule_id.startswith("prd-term-"):
            return SeverityLevel.LOW
        if rule_id.startswith("prd-struct-00"):
            return SeverityLevel.MEDIUM

        # Default
        return SeverityLevel.MEDIUM

    def calculate_compliance_score(self, findings: list[Finding]) -> int:
        """Calculate overall compliance score (0-100).

        Higher score = better compliance.

        Args:
            findings: All findings

        Returns:
            Score from 0-100
        """
        if not findings:
            return 100

        total_weight = sum(self.WEIGHTS.get(f.severity, 0) for f in findings)
        return max(0, 100 - total_weight)


class FindingAggregator:
    """Aggregates findings from PRD and Prototype contexts.

    Handles:
    - Cross-context deduplication
    - Finding prioritization
    - Source tracking
    """

    def aggregate(
        self,
        prd_findings: list[Finding],
        prototype_findings: list[Finding],
        prototype_analyzed: bool = False
    ) -> list[Finding]:
        """Aggregate findings from all sources.

        Args:
            prd_findings: Findings from PRD review
            prototype_findings: Findings from Prototype review
            prototype_analyzed: Whether prototype was included

        Returns:
            Deduplicated, prioritized findings
        """
        all_findings = []

        # Add PRD findings with source_context already set
        all_findings.extend(prd_findings)

        # Add Prototype findings
        if prototype_analyzed:
            all_findings.extend(prototype_findings)

        # Deduplicate by rule_id + location
        unique = self._deduplicate(all_findings)

        # Sort by severity (CRITICAL first)
        sorted_findings = sorted(
            unique,
            key=lambda f: f.severity.value
        )

        return sorted_findings

    def _deduplicate(self, findings: list[Finding]) -> list[Finding]:
        """Remove duplicate findings by rule_id + location.

        Args:
            findings: All findings

        Returns:
            Unique findings
        """
        seen = set()
        unique = []

        for f in findings:
            key = (f.rule_id, f.location)
            if key not in seen:
                seen.add(key)
                unique.append(f)

        return unique


class BilingualReportFormatter:
    """Formats compliance reports in Chinese and English.

    Handles:
    - Bilingual section headers
    - Severity label translation
    - Suggestion translation
    """

    # Severity translations
    SEVERITY_LABELS = {
        SeverityLevel.CRITICAL: {"zh": "严重", "en": "Critical"},
        SeverityLevel.HIGH: {"zh": "高", "en": "High"},
        SeverityLevel.MEDIUM: {"zh": "中", "en": "Medium"},
        SeverityLevel.LOW: {"zh": "低", "en": "Low"},
    }

    # Dimension translations
    DIMENSION_LABELS = {
        ReviewDimension.STRUCTURE: {"zh": "结构", "en": "Structure"},
        ReviewDimension.TERMINOLOGY: {"zh": "术语", "en": "Terminology"},
        ReviewDimension.LAYOUT: {"zh": "布局", "en": "Layout"},
        ReviewDimension.ACCESSIBILITY: {"zh": "可访问性", "en": "Accessibility"},
    }

    # Section headers
    SECTIONS = {
        "summary": {"zh": "总结", "en": "Summary"},
        "findings": {"zh": "发现问题", "en": "Findings"},
        "severity_breakdown": {"zh": "严重程度分布", "en": "Severity Breakdown"},
        "compliance_score": {"zh": "合规评分", "en": "Compliance Score"},
        "suggestions": {"zh": "改进建议", "en": "Suggestions"},
    }

    def format_report(self, report: Report) -> dict:
        """Format report in bilingual structure.

        Args:
            report: Report to format

        Returns:
            Bilingual report dict
        """
        return {
            "id": report.id,
            "timestamp": report.timestamp.isoformat(),
            "document_path": report.document_path,
            "language": "bilingual",
            "summary": self._format_summary(report.summary),
            "severity_breakdown": self._format_severity_breakdown(report),
            "findings": self._format_findings(report.findings),
            "suggestions": self._format_suggestions(report.findings),
        }

    def _format_summary(self, summary: ReportSummary) -> dict:
        """Format summary section."""
        return {
            "zh": {
                "文档路径": getattr(summary, 'document_path', ''),
                "问题总数": summary.total_findings,
                "PRD问题数": summary.prd_findings_count,
                "原型问题数": summary.prototype_findings_count,
                "原型已分析": summary.prototype_analyzed,
                "合规评分": f"{summary.compliance_score}/100",
                "严重程度": {
                    "严重": summary.critical_count,
                    "高": summary.high_count,
                    "中": summary.medium_count,
                    "低": summary.low_count,
                },
            },
            "en": {
                "document_path": getattr(summary, 'document_path', ''),
                "total_findings": summary.total_findings,
                "prd_findings": summary.prd_findings_count,
                "prototype_findings": summary.prototype_findings_count,
                "prototype_analyzed": summary.prototype_analyzed,
                "compliance_score": f"{summary.compliance_score}/100",
                "severity_breakdown": {
                    "Critical": summary.critical_count,
                    "High": summary.high_count,
                    "Medium": summary.medium_count,
                    "Low": summary.low_count,
                },
            },
        }

    def _format_severity_breakdown(self, report: Report) -> dict:
        """Format severity breakdown section."""
        return {
            "zh": {
                "CRITICAL": {
                    "label": "严重",
                    "count": report.summary.critical_count,
                    "description": "必须立即修复的问题",
                },
                "HIGH": {
                    "label": "高",
                    "count": report.summary.high_count,
                    "description": "重要问题，应优先修复",
                },
                "MEDIUM": {
                    "label": "中",
                    "count": report.summary.medium_count,
                    "description": "建议修复的问题",
                },
                "LOW": {
                    "label": "低",
                    "count": report.summary.low_count,
                    "description": "可选改进建议",
                },
            },
            "en": {
                "CRITICAL": {
                    "label": "Critical",
                    "count": report.summary.critical_count,
                    "description": "Must be fixed immediately",
                },
                "HIGH": {
                    "label": "High",
                    "count": report.summary.high_count,
                    "description": "Important issues to prioritize",
                },
                "MEDIUM": {
                    "label": "Medium",
                    "count": report.summary.medium_count,
                    "description": "Recommended fixes",
                },
                "LOW": {
                    "label": "Low",
                    "count": report.summary.low_count,
                    "description": "Optional improvements",
                },
            },
        }

    def _format_findings(self, findings: list[Finding]) -> list[dict]:
        """Format findings list."""
        formatted = []
        for f in findings:
            formatted.append({
                "id": f.id,
                "source_context": f.source_context,
                "dimension": {
                    "zh": self.DIMENSION_LABELS[f.dimension]["zh"],
                    "en": self.DIMENSION_LABELS[f.dimension]["en"],
                },
                "severity": {
                    "zh": self.SEVERITY_LABELS[f.severity]["zh"],
                    "en": self.SEVERITY_LABELS[f.severity]["en"],
                },
                "rule_id": f.rule_id,
                "description": f.description,
                "location": f.location,
                "suggestion": f.suggestion,
                "evidence": f.evidence,
            })
        return formatted

    def _format_suggestions(self, findings: list[Finding]) -> list[dict]:
        """Format suggestions grouped by severity."""
        by_severity = {
            SeverityLevel.CRITICAL: [],
            SeverityLevel.HIGH: [],
            SeverityLevel.MEDIUM: [],
            SeverityLevel.LOW: [],
        }

        for f in findings:
            by_severity[f.severity].append({
                "rule_id": f.rule_id,
                "suggestion": f.suggestion,
                "location": f.location,
            })

        return {
            "zh": {
                "严重": by_severity[SeverityLevel.CRITICAL],
                "高": by_severity[SeverityLevel.HIGH],
                "中": by_severity[SeverityLevel.MEDIUM],
                "低": by_severity[SeverityLevel.LOW],
            },
            "en": {
                "Critical": by_severity[SeverityLevel.CRITICAL],
                "High": by_severity[SeverityLevel.HIGH],
                "Medium": by_severity[SeverityLevel.MEDIUM],
                "Low": by_severity[SeverityLevel.LOW],
            },
        }
