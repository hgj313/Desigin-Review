"""Markdown compliance report generation (Simplified Chinese).

生成纯中文 Markdown 合规报告。
"""

from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

from src.workflow.state import Finding


# Severity display names
SEVERITY_CN = {
    "Critical": "严重",
    "Major": "重要",
    "Minor": "次要",
    "Suggestion": "建议",
}

# Issue type display names
ISSUE_TYPE_CN = {
    "structure": "结构",
    "terminology": "术语",
    "completeness": "完整性",
    "formatting": "格式",
    "color": "颜色",
    "typography": "排版",
    "spacing": "间距",
    "accessibility": "无障碍",
    "assumptions": "假设",
}

REPORT_HEADER = """# 设计合规报告
---
审查类型: {review_type}
审查日期: {date}
知识库: {collection_name}
审查深度: {review_depth}
总问题数: {total_count}
---
"""


def _severity_order(severity: str) -> int:
    order = {"Critical": 0, "Major": 1, "Minor": 2, "Suggestion": 3}
    return order.get(severity, 99)


def _group_findings_by_category(findings: List[Finding]) -> Dict[str, List[Finding]]:
    grouped = defaultdict(list)
    for finding in findings:
        grouped[finding.issue_type].append(finding)
    return grouped


def generate_compliance_report(
    findings: List[Finding],
    metadata: Dict[str, Any],
) -> str:
    """生成纯中文 Markdown 合规报告。

    Args:
        findings: Finding 对象列表。
        metadata: 包含 collection_name, review_depth, date, review_type, image_path 的字典。

    Returns:
        格式化的 Markdown 报告字符串。
    """
    review_type = metadata.get("review_type", "PRD审查")
    date = metadata.get("date", datetime.now().strftime("%Y-%m-%d"))
    collection_name = metadata.get("collection_name", "N/A")
    review_depth = metadata.get("review_depth", "balanced")
    image_path = metadata.get("image_path")

    if not findings:
        header = REPORT_HEADER.format(
            review_type=review_type,
            date=date,
            collection_name=collection_name,
            review_depth=review_depth,
            total_count=0,
        )
        return header + "\n## 未发现问题\n\n文档通过了所有验证检查。\n"

    # Group findings by category
    grouped_findings = _group_findings_by_category(findings)

    # Build report
    report_lines = []

    # Report header
    report_lines.append(REPORT_HEADER.format(
        review_type=review_type,
        date=date,
        collection_name=collection_name,
        review_depth=review_depth,
        total_count=len(findings),
    ))

    # Add image path if present
    if image_path:
        report_lines.append(f"**图像:** {image_path}")
        report_lines.append("")

    # Summary statistics
    severity_counts = defaultdict(int)
    for finding in findings:
        severity_counts[finding.severity] += 1

    report_lines.append("## 摘要")
    report_lines.append("")
    report_lines.append(f"- **总问题数:** {len(findings)}")
    report_lines.append(f"- 严重: {severity_counts.get('Critical', 0)}")
    report_lines.append(f"- 重要: {severity_counts.get('Major', 0)}")
    report_lines.append(f"- 次要: {severity_counts.get('Minor', 0)}")
    report_lines.append(f"- 建议: {severity_counts.get('Suggestion', 0)}")
    report_lines.append("")

    # Issues by category section
    report_lines.append("## 按类别排列的问题")
    report_lines.append("")

    # Build sections for each category
    for category, findings_list in grouped_findings.items():
        category_zh = ISSUE_TYPE_CN.get(category, category)

        report_lines.append(f"### {category_zh}")
        report_lines.append("")

        # Summary table header
        report_lines.append("| 严重程度 | 位置 | 问题描述 | 修复建议 |")
        report_lines.append("|----------|------|----------|----------|")

        for finding in sorted(findings_list, key=lambda f: _severity_order(f.severity)):
            severity_label = SEVERITY_CN.get(finding.severity, finding.severity)
            location = finding.location or "-"
            desc = finding.description_zh or finding.description_en or "-"
            sugg = finding.suggestion_zh or finding.suggestion_en or "-"

            report_lines.append(f"| {severity_label} | {location} | {desc} | {sugg} |")

        report_lines.append("")

    return "\n".join(report_lines)


__all__ = [
    "generate_compliance_report",
    "REPORT_HEADER",
    "SEVERITY_CN",
    "ISSUE_TYPE_CN",
]
