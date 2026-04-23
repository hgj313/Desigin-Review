"""Tool definitions for LLM Compiler.

Defines all tools with their metadata (name, description, parameters, dependencies).

References:
- FEATURES.md: Tool Registry section
- ARCHITECTURE.md: Tool definitions
"""

from src.domains.tools.registry import (
    ToolDefinition,
    ToolParallelGroup,
    TOOL_REGISTRY,
)


# =============================================================================
# Retrieval Tools
# =============================================================================

SEARCH_STANDARDS_DEF = ToolDefinition(
    name="search_standards",
    description="Search design standards knowledge base for relevant rules and guidelines. "
                "Use this to find standards before evaluating violations.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language query to search standards"
            },
            "dimension": {
                "type": "string",
                "description": "Filter by dimension: structure, terminology, layout, accessibility",
                "enum": ["structure", "terminology", "layout", "accessibility", None],
                "default": None
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 5
            }
        },
        "required": ["query"]
    },
    dependencies=[],
    parallel_group=ToolParallelGroup.RETRIEVAL,
    retry_on_failure=True,
)

# =============================================================================
# Prototype Analysis Tools
# =============================================================================

ANALYZE_PROTOTYPE_DEF = ToolDefinition(
    name="analyze_prototype",
    description="Analyze prototype image using MiniMax Vision API. "
                "Extracts color palette, typography, spacing, and layout information.",
    parameters={
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "Path to prototype image file"
            },
            "analysis_type": {
                "type": "string",
                "description": "Type of analysis to perform",
                "enum": ["full", "color", "typography", "spacing", "accessibility"],
                "default": "full"
            }
        },
        "required": ["image_path"]
    },
    dependencies=[],
    parallel_group=ToolParallelGroup.RETRIEVAL,
    retry_on_failure=True,
)

# =============================================================================
# PRD Evaluation Tools
# =============================================================================

EVALUATE_STRUCTURE_DEF = ToolDefinition(
    name="evaluate_structure",
    description="Evaluate PRD structure against design standards. "
                "Checks for required sections, heading hierarchy, and completeness.",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "PRD content to evaluate"
            },
            "standards": {
                "type": "array",
                "description": "Retrieved standards to check against",
                "items": {"type": "string"}
            }
        },
        "required": ["content", "standards"]
    },
    dependencies=["search_standards"],
    parallel_group=ToolParallelGroup.EVALUATION,
    retry_on_failure=False,
)

EVALUATE_TERMINOLOGY_DEF = ToolDefinition(
    name="evaluate_terminology",
    description="Check PRD terminology against design standards glossary. "
                "Validates consistent use of design terms.",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "PRD content to check"
            },
            "standards": {
                "type": "array",
                "description": "Retrieved glossary standards",
                "items": {"type": "string"}
            }
        },
        "required": ["content", "standards"]
    },
    dependencies=["search_standards"],
    parallel_group=ToolParallelGroup.EVALUATION,
    retry_on_failure=False,
)

EVALUATE_COMPLETENESS_DEF = ToolDefinition(
    name="evaluate_completeness",
    description="Validate PRD completeness. Checks for missing sections, "
                "placeholder content, and vague language.",
    parameters={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "PRD content to evaluate"
            },
            "standards": {
                "type": "array",
                "description": "Retrieved completeness standards",
                "items": {"type": "string"}
            }
        },
        "required": ["content", "standards"]
    },
    dependencies=["search_standards"],
    parallel_group=ToolParallelGroup.EVALUATION,
    retry_on_failure=False,
)

# =============================================================================
# Prototype Evaluation Tools
# =============================================================================

EVALUATE_LAYOUT_DEF = ToolDefinition(
    name="evaluate_layout",
    description="Evaluate prototype layout against design standards. "
                "Validates spacing, grid alignment, and visual hierarchy.",
    parameters={
        "type": "object",
        "properties": {
            "vision_result": {
                "type": "object",
                "description": "Result from analyze_prototype tool"
            },
            "standards": {
                "type": "array",
                "description": "Retrieved layout standards",
                "items": {"type": "string"}
            }
        },
        "required": ["vision_result", "standards"]
    },
    dependencies=["analyze_prototype"],
    parallel_group=ToolParallelGroup.EVALUATION,
    retry_on_failure=False,
)

EVALUATE_ACCESSIBILITY_DEF = ToolDefinition(
    name="evaluate_accessibility",
    description="Check prototype accessibility against WCAG guidelines. "
                "Validates color contrast and text sizing.",
    parameters={
        "type": "object",
        "properties": {
            "vision_result": {
                "type": "object",
                "description": "Result from analyze_prototype tool"
            },
            "standards": {
                "type": "array",
                "description": "Retrieved accessibility standards",
                "items": {"type": "string"}
            }
        },
        "required": ["vision_result", "standards"]
    },
    dependencies=["analyze_prototype"],
    parallel_group=ToolParallelGroup.EVALUATION,
    retry_on_failure=False,
)

# =============================================================================
# Report Generation Tool
# =============================================================================

GENERATE_REPORT_DEF = ToolDefinition(
    name="generate_report",
    description="Generate bilingual compliance report from all findings. "
                "Aggregates, deduplicates, and formats findings into final report.",
    parameters={
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "description": "All findings to include in report",
                "items": {"type": "object"}
            },
            "report_format": {
                "type": "string",
                "description": "Output format: detailed, summary, executive",
                "enum": ["detailed", "summary", "executive"],
                "default": "detailed"
            }
        },
        "required": ["findings"]
    },
    dependencies=["evaluate_structure", "evaluate_terminology", "evaluate_layout", "evaluate_accessibility"],
    parallel_group=None,
    retry_on_failure=False,
)


# =============================================================================
# Register all tools
# =============================================================================

def register_all_tools() -> None:
    """Register all tools with the global registry."""
    tools = [
        SEARCH_STANDARDS_DEF,
        ANALYZE_PROTOTYPE_DEF,
        EVALUATE_STRUCTURE_DEF,
        EVALUATE_TERMINOLOGY_DEF,
        EVALUATE_COMPLETENESS_DEF,
        EVALUATE_LAYOUT_DEF,
        EVALUATE_ACCESSIBILITY_DEF,
        GENERATE_REPORT_DEF,
    ]
    for tool in tools:
        TOOL_REGISTRY.register(tool)


# Auto-register on import
register_all_tools()
