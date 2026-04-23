"""Tools package - Tool Registry, Definitions, and Executor.

Provides centralized tool management for the LLM Compiler.

Modules:
- registry: ToolDefinition and ToolRegistry classes
- definitions: All tool definitions
- executor: ToolExecutor with validation
"""

from .registry import (
    ToolDefinition,
    ToolParallelGroup,
    ToolRegistry,
    TOOL_REGISTRY,
)
from .definitions import (
    SEARCH_STANDARDS_DEF,
    ANALYZE_PROTOTYPE_DEF,
    EVALUATE_STRUCTURE_DEF,
    EVALUATE_TERMINOLOGY_DEF,
    EVALUATE_COMPLETENESS_DEF,
    EVALUATE_LAYOUT_DEF,
    EVALUATE_ACCESSIBILITY_DEF,
    GENERATE_REPORT_DEF,
    register_all_tools,
)
from .executor import (
    ToolCall,
    ToolExecutor,
    ToolExecutionResult,
    check_loop_count,
)
from .handlers import TOOL_HANDLERS

__all__ = [
    # Registry
    "ToolDefinition",
    "ToolParallelGroup",
    "ToolRegistry",
    "TOOL_REGISTRY",
    # Definitions
    "SEARCH_STANDARDS_DEF",
    "ANALYZE_PROTOTYPE_DEF",
    "EVALUATE_STRUCTURE_DEF",
    "EVALUATE_TERMINOLOGY_DEF",
    "EVALUATE_COMPLETENESS_DEF",
    "EVALUATE_LAYOUT_DEF",
    "EVALUATE_ACCESSIBILITY_DEF",
    "GENERATE_REPORT_DEF",
    "register_all_tools",
    # Executor
    "ToolCall",
    "ToolExecutor",
    "ToolExecutionResult",
    "check_loop_count",
    # Handlers
    "TOOL_HANDLERS",
]
