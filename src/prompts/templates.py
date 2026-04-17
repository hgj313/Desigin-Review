"""Prompt templates for bilingual output and Standard Not Found behavior.

Provides prompt templates for formatting retrieval results and generating
explicit "Standard Not Found" responses per D-10 (bilingual), D-12, and AGT-03.

References:
- D-10: All outputs must be bilingual (Chinese/English)
- D-12: System explicitly states Standard Not Found when no relevant guidance
- AGT-03: Agent explicitly states Standard Not Found when no relevant guidance
"""

from typing import Optional

from langchain_core.documents import Document


# ============================================================================
# Prompt Templates
# ============================================================================


STANDARD_NOT_FOUND_TEMPLATE = """English:
Standard Not Found. Knowledge base has no relevant guidance for this query.

Chinese:
未找到相关标准。知识库中没有与此查询相关的指导。

---
Query: {query}
Confidence Threshold: {threshold}
Top Result Confidence: {confidence:.2f}
"""

RETRIEVAL_RESULT_TEMPLATE = """Retrieved Design Standards:

{results}

---

Source Attribution:
{source_info}

Relevance Score: {score:.2f}
"""

SOURCE_ATTRIBUTION_TEMPLATE = """Document: {document_name}
Section: {section}
Version: {version_id} (Effective: {effective_date})
Source: {source_file}
"""


# ============================================================================
# Helper Functions
# ============================================================================


def format_source_attribution(metadata: dict) -> str:
    """Format source attribution from document metadata.

    Args:
        metadata: Document metadata dict with document_name, section,
                  version_id, effective_date, source_file.

    Returns:
        Formatted source attribution string.
    """
    return SOURCE_ATTRIBUTION_TEMPLATE.format(
        document_name=metadata.get("document_name", "Unknown"),
        section=metadata.get("section", "Unknown"),
        version_id=metadata.get("version_id", "Unknown"),
        effective_date=metadata.get("effective_date", "Unknown"),
        source_file=metadata.get("source_file", "Unknown"),
    )


def format_retrieval_results(results: list[tuple[Document, float]]) -> str:
    """Format retrieval results with source attribution.

    Generates bilingual output combining Chinese and English sections
    per D-10.

    Args:
        results: List of (Document, score) tuples from hybrid retrieval.

    Returns:
        Formatted bilingual string with all results and attribution.
    """
    if not results:
        return "No results found."

    formatted_results = []

    for i, (doc, score) in enumerate(results, 1):
        # Format source attribution
        source_info = format_source_attribution(doc.metadata)

        # Format individual result (bilingual)
        result_text = f"""
---
Result {i}:

[English]
Content: {doc.page_content}

[中文]
内容：{doc.page_content}

---
Source Attribution:
{source_info}

Relevance Score: {score:.4f}
"""
        formatted_results.append(result_text)

    all_results = "\n".join(formatted_results)

    # Create header (bilingual)
    header = """
Design Standards Retrieval Results
设计标准检索结果
---
"""

    return f"{header}\n{all_results}"


SEVERITY_ASSESSMENT_TEMPLATE = """English:
Assess the severity of this PRD review finding.

Issue Type: {issue_type}
Description: {description}
Context: {context}

Severity levels: Critical > Major > Minor > Suggestion
Critical = Required section missing or blocks review
Major = Significant issue affecting clarity or compliance
Minor = Formatting or style issue
Suggestion = Best practice recommendation

Chinese:
评估此PRD审查问题的严重程度。

问题类型：{issue_type}
描述：{description}
上下文：{context}

严重级别：Critical > Major > Minor > Suggestion
Critical = 缺少必需章节或阻止审查
Major = 影响清晰度或合规性的重要问题
Minor = 格式或样式问题
Suggestion = 最佳实践建议

{format_instructions}
"""


def format_severity_assessment(
    issue_type: str,
    description: str,
    context: str,
    format_instructions: str,
) -> str:
    """Format severity assessment prompt.

    Args:
        issue_type: Type of issue being assessed.
        description: Description of the finding.
        context: Surrounding context from the document.
        format_instructions: Instructions for response formatting.

    Returns:
        Formatted severity assessment prompt string.
    """
    return SEVERITY_ASSESSMENT_TEMPLATE.format(
        issue_type=issue_type,
        description=description,
        context=context,
        format_instructions=format_instructions,
    )


def create_not_found_response(
    query: str,
    threshold: float,
    confidence: float,
) -> str:
    """Create explicit Standard Not Found response.

    Per AGT-03: When confidence < threshold, return explicit
    "Standard Not Found" message in both Chinese and English.

    Args:
        query: The original query string.
        threshold: The confidence threshold that was not met.
        confidence: The actual top result confidence score.

    Returns:
        Bilingual Standard Not Found response string.
    """
    return STANDARD_NOT_FOUND_TEMPLATE.format(
        query=query,
        threshold=threshold,
        confidence=confidence,
    )


__all__ = [
    "STANDARD_NOT_FOUND_TEMPLATE",
    "RETRIEVAL_RESULT_TEMPLATE",
    "SOURCE_ATTRIBUTION_TEMPLATE",
    "SEVERITY_ASSESSMENT_TEMPLATE",
    "format_retrieval_results",
    "format_source_attribution",
    "create_not_found_response",
    "format_severity_assessment",
]
