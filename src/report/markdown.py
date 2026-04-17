"""Bilingual Markdown compliance report generation.

Generates interleaved Chinese/English Markdown reports per RPT-01 through RPT-05.
"""

from typing import List, Dict, Any
from datetime import datetime

from src.workflow.state import Finding


# Severity display names in Chinese
SEVERITY_CN = {
    "Critical": "严重",
    "Major": "重要",
    "Minor": "次要",
    "Suggestion": "建议",
}

# Issue type display names in Chinese
ISSUE_TYPE_CN = {
    "structure": "结构",
    "terminology": "术语",
    "completeness": "完整性",
    "formatting": "格式",
}

REPORT_HEADER = """# PRD Compliance Review Report
# PRD 合规审查报告
---
Review Date | 审查日期: {date}
Collection | 知识库: {collection_name}
Review Depth | 审查深度: {review_depth}
Total Issues | 总问题数: {total_count}
---
"""


def generate_compliance_report(
    findings: List[Finding],
    metadata: Dict[str, Any],
) -> str:
    """Generate bilingual Markdown compliance report per RPT-01, RPT-05.

    Groups findings by severity (Critical > Major > Minor > Suggestion)
    and interleaves Chinese/English per D-10/D-18.

    Args:
        findings: List of Finding objects from validation.
        metadata: Dict with collection_name, review_depth, date.

    Returns:
        Formatted bilingual Markdown report string.
    """
    if not findings:
        return REPORT_HEADER.format(
            date=metadata.get("date", datetime.now().strftime("%Y-%m-%d")),
            collection_name=metadata.get("collection_name", "N/A"),
            review_depth=metadata.get("review_depth", "N/A"),
            total_count=0,
        ) + "\n## No Issues Found\n# 未发现问题\n\nThe PRD document passed all validation checks.\nPRD文档通过了所有验证检查。\n"

    # Group findings by severity
    severity_groups: Dict[str, List[Finding]] = {
        "Critical": [],
        "Major": [],
        "Minor": [],
        "Suggestion": [],
    }

    for finding in findings:
        severity_groups[finding.severity].append(finding)

    # Build report sections
    sections = []
    sections.append(REPORT_HEADER.format(
        date=metadata.get("date", datetime.now().strftime("%Y-%m-%d")),
        collection_name=metadata.get("collection_name", "N/A"),
        review_depth=metadata.get("review_depth", "N/A"),
        total_count=len(findings),
    ))

    # Process each severity level
    for severity in ["Critical", "Major", "Minor", "Suggestion"]:
        findings_in_group = severity_groups[severity]
        if not findings_in_group:
            continue

        severity_cn = SEVERITY_CN.get(severity, severity)
        issue_type_cn_map = ISSUE_TYPE_CN

        sections.append(f"## {severity} | {severity_cn}")
        sections.append(f"Count | 数量: {len(findings_in_group)}")
        sections.append("")

        for i, finding in enumerate(findings_in_group, 1):
            issue_type_cn = issue_type_cn_map.get(finding.issue_type, finding.issue_type)

            sections.append(f"### {i}. {finding.issue_type} | {issue_type_cn}")
            sections.append(f"**Location | 位置:** {finding.location}")
            sections.append("")
            sections.append(f"**English:** {finding.description_en}")
            sections.append(f"**中文:** {finding.description_zh}")
            sections.append("")

            if finding.suggestion_en or finding.suggestion_zh:
                sections.append(f"**Suggestion | 建议:** {finding.suggestion_en or ''}")
                if finding.suggestion_zh:
                    sections.append(f"**建议:** {finding.suggestion_zh}")
            sections.append("")
            sections.append("---")
            sections.append("")

    return "\n".join(sections)


__all__ = ["generate_compliance_report", "REPORT_HEADER", "SEVERITY_CN", "ISSUE_TYPE_CN"]
