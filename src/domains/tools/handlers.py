"""Tool handlers - Actual implementations of tool logic.

References:
- FEATURES.md: Tool implementation
- ARCHITECTURE.md: Tool execution flow
"""

from typing import Any, Optional
import os

from src.domains.shared import Finding, SeverityLevel, ReviewDimension


def search_standards_handler(args: dict) -> list[dict]:
    """Handle search_standards tool invocation."""
    query = args.get("query", "")
    dimension = args.get("dimension")
    limit = args.get("limit", 5)

    try:
        from src.vectorstore.chroma_store import ChromaStore
        store = ChromaStore()
        results = store.search(query, dimension=dimension, k=limit)
        return [
            {
                "id": r["id"],
                "content": r["content"][:500],
                "metadata": r["metadata"],
                "score": r.get("score", 0),
            }
            for r in results
        ]
    except ImportError:
        return [{"error": "Vector store not initialized"}]
    except Exception as e:
        return [{"error": str(e)}]


def analyze_prototype_handler(args: dict) -> dict:
    """Handle analyze_prototype tool invocation."""
    image_path = args.get("image_path")
    analysis_type = args.get("analysis_type", "full")

    if not image_path:
        return {"error": "image_path is required"}

    try:
        from src.image.minimax_vision import MiniMaxVisionClient
        client = MiniMaxVisionClient()
        result = client.analyze_ui_image(image_path, analysis_type)
        return {
            "image_path": image_path,
            "analysis_type": analysis_type,
            "raw_response": result.get("raw_response", ""),
        }
    except ImportError:
        return {"error": "MiniMax Vision client not available"}
    except Exception as e:
        return {"error": str(e)}


def evaluate_structure_handler(args: dict) -> dict:
    """Handle evaluate_structure tool invocation."""
    content = args.get("content", "")
    standards = args.get("standards", [])

    if not content:
        return {"findings": [], "error": "No content to evaluate"}

    findings = []

    # Check for required sections
    required_sections = ["overview", "user stories", "acceptance criteria", "requirements"]
    content_lower = content.lower()

    for section in required_sections:
        if section not in content_lower:
            findings.append(Finding(
                source_context="prd",
                dimension=ReviewDimension.STRUCTURE,
                severity=SeverityLevel.HIGH,
                rule_id="struct-001",
                description=f"Missing required section: {section}",
                location="Document structure",
                suggestion=f"Add a {section} section to the PRD",
            ).to_dict())

    return {"findings": findings}


def evaluate_terminology_handler(args: dict) -> dict:
    """Handle evaluate_terminology tool invocation."""
    content = args.get("content", "")
    standards = args.get("standards", [])

    if not content:
        return {"findings": [], "error": "No content to evaluate"}

    try:
        from src.domains.prd.entities import PRDDocument
        from src.domains.prd.services import PRDTerminologyChecker

        doc = PRDDocument.from_text(content)
        checker = PRDTerminologyChecker()
        findings = checker.check(doc, standards)

        return {"findings": [f.to_dict() for f in findings]}
    except ImportError:
        return {"findings": [], "error": "PRD services not available"}
    except Exception as e:
        return {"findings": [], "error": str(e)}


def evaluate_completeness_handler(args: dict) -> dict:
    """Handle evaluate_completeness tool invocation."""
    content = args.get("content", "")
    standards = args.get("standards", [])

    if not content:
        return {"findings": [], "error": "No content to evaluate"}

    placeholders = ["TODO", "TBD", "xxx", "..."]
    findings = []

    for placeholder in placeholders:
        if placeholder in content:
            findings.append(Finding(
                source_context="prd",
                dimension=ReviewDimension.STRUCTURE,
                severity=SeverityLevel.MEDIUM,
                rule_id="complete-001",
                description=f"Found placeholder text: {placeholder}",
                location="Document content",
                suggestion="Replace placeholder with actual content",
            ).to_dict())

    return {"findings": findings}


def evaluate_layout_handler(args: dict) -> dict:
    """Handle evaluate_layout tool invocation."""
    vision_result = args.get("vision_result", {})
    standards = args.get("standards", [])

    if not vision_result:
        return {"findings": [], "error": "No vision result to evaluate"}

    raw_response = vision_result.get("raw_response", "")

    if not raw_response:
        return {"findings": [], "error": "No analysis content"}

    findings = []
    raw_lower = raw_response.lower()

    # Check for spacing keywords
    has_spacing = "spacing" in raw_lower or "间距" in raw_response or "margin" in raw_lower or "padding" in raw_lower
    has_grid = "grid" in raw_lower or "网格" in raw_response or "对齐" in raw_response
    has_8pt = "8pt" in raw_lower or "8 pt" in raw_lower

    # Check for inconsistent spacing
    has_inconsistent = any(kw in raw_lower for kw in ["inconsistent", "uneven", "irregular", "不一致", "不均匀", "混乱"])

    if has_spacing or has_grid:
        if not has_8pt:
            findings.append(Finding(
                source_context="prototype",
                dimension=ReviewDimension.LAYOUT,
                severity=SeverityLevel.MEDIUM,
                rule_id="proto-layout-001",
                description="Spacing may not align to 8pt grid",
                location="Prototype layout",
                suggestion="Ensure all spacing uses multiples of 8pt",
                evidence=raw_response[:200],
            ).to_dict())

        if has_inconsistent:
            findings.append(Finding(
                source_context="prototype",
                dimension=ReviewDimension.LAYOUT,
                severity=SeverityLevel.MEDIUM,
                rule_id="proto-layout-002",
                description="Inconsistent spacing detected in layout",
                location="Prototype layout",
                suggestion="Standardize spacing to 8pt grid increments",
                evidence=raw_response[:200],
            ).to_dict())

    # Check for alignment issues
    if "alignment" in raw_lower or "对齐" in raw_response:
        if "not aligned" in raw_lower or "misaligned" in raw_lower or "未对齐" in raw_response:
            findings.append(Finding(
                source_context="prototype",
                dimension=ReviewDimension.LAYOUT,
                severity=SeverityLevel.MEDIUM,
                rule_id="proto-layout-003",
                description="Elements may be misaligned",
                location="Prototype layout",
                suggestion="Ensure elements align to grid or use consistent reference points",
                evidence=raw_response[:200],
            ).to_dict())

    return {"findings": findings}


def evaluate_accessibility_handler(args: dict) -> dict:
    """Handle evaluate_accessibility tool invocation."""
    vision_result = args.get("vision_result", {})
    standards = args.get("standards", [])

    if not vision_result:
        return {"findings": [], "error": "No vision result to evaluate"}

    raw_response = vision_result.get("raw_response", "")

    if not raw_response:
        return {"findings": [], "error": "No analysis content"}

    findings = []
    raw_lower = raw_response.lower()

    # Check for contrast issues
    has_contrast = "contrast" in raw_lower or "对比度" in raw_response or "color" in raw_lower
    contrast_keywords = ["fail", "insufficient", "low", "poor", "不足", "过低", "差", "weak"]
    has_contrast_issue = any(kw in raw_lower for kw in contrast_keywords)

    if has_contrast and has_contrast_issue:
        findings.append(Finding(
            source_context="prototype",
            dimension=ReviewDimension.ACCESSIBILITY,
            severity=SeverityLevel.HIGH,
            rule_id="proto-a11y-001",
            description="Color contrast may be insufficient (WCAG AA requires 4.5:1)",
            location="Prototype accessibility",
            suggestion="Ensure text/background contrast ratio is at least 4.5:1",
            evidence=raw_response[:200],
        ).to_dict())

    # Check for text size issues (too small for accessibility)
    if "text size" in raw_lower or "font size" in raw_lower or "字号" in raw_response:
        if "small" in raw_lower or "too small" in raw_lower or "过小" in raw_response:
            findings.append(Finding(
                source_context="prototype",
                dimension=ReviewDimension.ACCESSIBILITY,
                severity=SeverityLevel.MEDIUM,
                rule_id="proto-a11y-002",
                description="Text may be too small for accessibility",
                location="Prototype accessibility",
                suggestion="Ensure body text is at least 16px (12pt) for readability",
                evidence=raw_response[:200],
            ).to_dict())

    return {"findings": findings}


def generate_report_handler(args: dict) -> dict:
    """Handle generate_report tool invocation."""
    findings_data = args.get("findings", [])
    report_format = args.get("report_format", "detailed")

    findings = []
    for f in findings_data:
        try:
            findings.append(Finding.from_dict(f))
        except Exception:
            pass

    from src.domains.report import Report, ReportSummary
    from src.domains.report.services import BilingualReportFormatter, SeverityCalculator

    # Calculate severity counts
    severity_calc = SeverityCalculator()
    severity_counts = {
        "critical": sum(1 for f in findings if f.severity.value == 0),
        "high": sum(1 for f in findings if f.severity.value == 1),
        "medium": sum(1 for f in findings if f.severity.value == 2),
        "low": sum(1 for f in findings if f.severity.value == 3),
    }

    # Check if prototype was analyzed
    prototype_analyzed = any(f.source_context == "prototype" for f in findings)

    # Create report
    report = Report(
        document_path="",
        findings=findings,
    )
    report.summary.prototype_analyzed = prototype_analyzed
    report.summary.prd_findings_count = sum(1 for f in findings if f.source_context == "prd")
    report.summary.prototype_findings_count = sum(1 for f in findings if f.source_context == "prototype")
    report.summary.compliance_score = severity_calc.calculate_compliance_score(findings)
    report.summary.critical_count = severity_counts["critical"]
    report.summary.high_count = severity_counts["high"]
    report.summary.medium_count = severity_counts["medium"]
    report.summary.low_count = severity_counts["low"]
    report.summary.total_findings = len(findings)
    report.generate()

    # Format with bilingual formatter
    formatter = BilingualReportFormatter()
    formatted = formatter.format_report(report)

    return {
        "id": report.id,
        "timestamp": report.timestamp.isoformat(),
        "document_path": report.document_path,
        "summary": formatted["summary"],
        "severity_breakdown": formatted["severity_breakdown"],
        "findings": formatted["findings"],
        "suggestions": formatted["suggestions"],
        "language": "bilingual",
        "report_format": report_format,
    }


# Handler mapping
TOOL_HANDLERS = {
    "search_standards": search_standards_handler,
    "analyze_prototype": analyze_prototype_handler,
    "evaluate_structure": evaluate_structure_handler,
    "evaluate_terminology": evaluate_terminology_handler,
    "evaluate_completeness": evaluate_completeness_handler,
    "evaluate_layout": evaluate_layout_handler,
    "evaluate_accessibility": evaluate_accessibility_handler,
    "generate_report": generate_report_handler,
}
