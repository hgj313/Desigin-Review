"""Bilingual Markdown compliance report generation.

Generates interleaved Chinese/English Markdown reports per RPT-01 through RPT-05.
Supports all finding categories from PRD review (structure, terminology, completeness, formatting)
and image review (color, typography, spacing, accessibility, assumptions).
"""

from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

from src.workflow.state import Finding


# Severity display names in Chinese
SEVERITY_CN = {
    "Critical": "严重",
    "Major": "重要",
    "Minor": "次要",
    "Suggestion": "建议",
}

# Issue type display names (bilingual per D-18)
ISSUE_TYPE_CN = {
    # PRD review categories
    "structure": ("Structure", "结构"),
    "terminology": ("Terminology", "术语"),
    "completeness": ("Completeness", "完整性"),
    "formatting": ("Formatting", "格式"),
    # Image review categories
    "color": ("Color", "颜色"),
    "typography": ("Typography", "排版"),
    "spacing": ("Spacing", "间距"),
    "accessibility": ("Accessibility", "无障碍"),
    "assumptions": ("Assumptions", "假设"),
}

# Severity badge text (bilingual per D-18)
SEVERITY_BADGES = {
    "Critical": ("[CRITICAL]", "[严重]"),
    "Major": ("[MAJOR]", "[重要]"),
    "Minor": ("[MINOR]", "[次要]"),
    "Suggestion": ("[SUGGESTION]", "[建议]"),
}

REPORT_HEADER = """# Design Compliance Report
# 设计合规报告
---
Review Type | 审查类型: {review_type}
Review Date | 审查日期: {date}
Collection | 知识库: {collection_name}
Review Depth | 审查深度: {review_depth}
Total Issues | 总问题数: {total_count}
---
"""


def _severity_order(severity: str) -> int:
    """Return sort order for severity levels.

    Critical first, then Major, Minor, Suggestion.
    """
    order = {"Critical": 0, "Major": 1, "Minor": 2, "Suggestion": 3}
    return order.get(severity, 99)


def _severity_badge(severity: str) -> str:
    """Generate severity badge text (bilingual).

    Args:
        severity: Severity level string.

    Returns:
        Formatted badge string.
    """
    en, zh = SEVERITY_BADGES.get(severity, ("[UNKNOWN]", "[未知]"))
    return f"{en} {zh}"


def _group_findings_by_category(findings: List[Finding]) -> Dict[str, List[Finding]]:
    """Group findings by issue_type for organized reporting.

    Args:
        findings: List of Finding objects.

    Returns:
        Dict mapping issue_type to list of findings.
    """
    grouped = defaultdict(list)
    for finding in findings:
        grouped[finding.issue_type].append(finding)
    return grouped


def generate_compliance_report(
    findings: List[Finding],
    metadata: Dict[str, Any],
) -> str:
    """Generate bilingual Markdown compliance report per RPT-01 through RPT-05.

    Extended to include all image review finding categories:
    - structure, terminology, completeness, formatting (from PRD review)
    - color, typography, spacing, accessibility (from image review)
    - assumptions (from PRD-05)

    Per RPT-01: Categorized issues (Structure, Terminology, Layout, Accessibility)
    Per RPT-02: Severity level (Critical / Major / Minor / Suggestion)
    Per RPT-03: Location reference (line number, section name, or image coordinates)
    Per RPT-04: Specific improvement suggestions
    Per RPT-05: Bilingual output (Chinese and English)

    Groups findings by category with summary statistics.

    Args:
        findings: List of Finding objects from validation.
        metadata: Dict with collection_name, review_depth, date, review_type, image_path.

    Returns:
        Formatted bilingual Markdown report string.
    """
    review_type = metadata.get("review_type", "prd_review")
    date = metadata.get("date", datetime.now().strftime("%Y-%m-%d"))
    collection_name = metadata.get("collection_name", "N/A")
    review_depth = metadata.get("review_depth", "balanced")
    image_path = metadata.get("image_path")

    if not findings:
        header = REPORT_HEADER.format(
            review_type=review_type.title(),
            date=date,
            collection_name=collection_name,
            review_depth=review_depth,
            total_count=0,
        )
        return header + "\n## No Issues Found\n# 未发现问题\n\nThe document passed all validation checks.\n文档通过了所有验证检查。\n"

    # Group findings by category
    grouped_findings = _group_findings_by_category(findings)

    # Build report
    report_lines = []

    # Report header
    report_lines.append(REPORT_HEADER.format(
        review_type=review_type.title(),
        date=date,
        collection_name=collection_name,
        review_depth=review_depth,
        total_count=len(findings),
    ))

    # Add image path if present
    if image_path:
        report_lines.append(f"**Image | 图像:** {image_path}")
        report_lines.append("")

    # Summary statistics
    severity_counts = defaultdict(int)
    for finding in findings:
        severity_counts[finding.severity] += 1

    report_lines.append("## Summary | 摘要")
    report_lines.append("")
    report_lines.append(f"- **Total Issues | 总问题数:** {len(findings)}")
    report_lines.append(f"- Critical | 严重: {severity_counts.get('Critical', 0)}")
    report_lines.append(f"- Major | 重要: {severity_counts.get('Major', 0)}")
    report_lines.append(f"- Minor | 次要: {severity_counts.get('Minor', 0)}")
    report_lines.append(f"- Suggestion | 建议: {severity_counts.get('Suggestion', 0)}")
    report_lines.append("")

    # Issues by category section
    report_lines.append("## Issues by Category | 按类别排列的问题")
    report_lines.append("")

    # Build sections for each category
    for category, findings_list in grouped_findings.items():
        category_en, category_zh = ISSUE_TYPE_CN.get(category, (category, category))

        report_lines.append(f"### {category_en} | {category_zh}")
        report_lines.append("")

        # Summary table header
        report_lines.append("| Severity | Location | Description | Suggestion |")
        report_lines.append("|----------|----------|-------------|------------|")

        for finding in sorted(findings_list, key=lambda f: _severity_order(f.severity)):
            severity_badge = _severity_badge(finding.severity)
            location = finding.location or "-"
            desc_en = finding.description_en or "-"
            desc_zh = finding.description_zh or ""
            suggestion_en = finding.suggestion_en or "-"
            suggestion_zh = finding.suggestion_zh or ""

            # Format description - bilingual
            if desc_zh:
                desc = f"{desc_en}\n{desc_zh}"
            else:
                desc = desc_en

            # Format suggestion - bilingual
            if suggestion_zh:
                sugg = f"{suggestion_en}\n{suggestion_zh}"
            else:
                sugg = suggestion_en if suggestion_en else "-"

            report_lines.append(f"| {severity_badge} | {location} | {desc} | {sugg} |")

        report_lines.append("")

    return "\n".join(report_lines)


__all__ = [
    "generate_compliance_report",
    "REPORT_HEADER",
    "SEVERITY_CN",
    "ISSUE_TYPE_CN",
    "SEVERITY_BADGES",
    "_severity_order",
    "_severity_badge",
    "_group_findings_by_category",
]
