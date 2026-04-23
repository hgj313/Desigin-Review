"""Tool Executor - Handles tool invocation with validation.

References:
- ARCHITECTURE.md: Tool Registry Pattern
- PITFALLS.md: PP-01 MAX_LOOPS, PP-02 tool name validation, PP-03 cycle detection
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import asyncio

from src.domains.tools.registry import TOOL_REGISTRY, ToolDefinition
from src.domains.state import MAX_LOOPS


@dataclass
class ToolCall:
    """Record of a single tool invocation."""
    tool_name: str
    args: dict
    result: Any = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    execution_time_ms: int = 0


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: int = 0


class ToolExecutor:
    """Executes tools with validation and error handling."""

    def __init__(self, registry=TOOL_REGISTRY):
        self.registry = registry
        self.tool_history: list[ToolCall] = []

    def validate_tool(self, tool_name: str) -> None:
        """Validate tool name against whitelist (PP-02).

        Args:
            tool_name: Tool name to validate

        Raises:
            ValueError: If tool not in whitelist
        """
        if not self.registry.validate_tool_name(tool_name):
            valid_tools = [t.name for t in self.registry.get_all()]
            raise ValueError(
                f"Invalid tool: {tool_name}. Valid tools: {valid_tools}"
            )

    def execute(self, tool_name: str, args: dict, handler: Any) -> ToolExecutionResult:
        """Execute a tool with validation.

        Args:
            tool_name: Name of tool to execute
            args: Tool arguments
            handler: Callable that executes the tool

        Returns:
            ToolExecutionResult with success status and data

        Raises:
            ValueError: If tool not in whitelist
        """
        # Validate tool name (PP-02)
        self.validate_tool(tool_name)

        tool_def = self.registry.get(tool_name)
        if tool_def is None:
            return ToolExecutionResult(
                success=False,
                data=None,
                error=f"Tool not found: {tool_name}",
            )

        # Execute
        start = datetime.utcnow()
        try:
            result = handler(args)
            execution_time = int((datetime.utcnow() - start).total_seconds() * 1000)

            # Record in history
            self.tool_history.append(ToolCall(
                tool_name=tool_name,
                args=args,
                result=result,
                execution_time_ms=execution_time,
            ))

            return ToolExecutionResult(
                success=True,
                data=result,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            execution_time = int((datetime.utcnow() - start).total_seconds() * 1000)
            error_msg = str(e)

            # Record failed call
            self.tool_history.append(ToolCall(
                tool_name=tool_name,
                args=args,
                error=error_msg,
                execution_time_ms=execution_time,
            ))

            # Retry if enabled
            if tool_def.retry_on_failure:
                return self._retry_with_backoff(tool_name, args, handler, error_msg)

            return ToolExecutionResult(
                success=False,
                data=None,
                error=error_msg,
                execution_time_ms=execution_time,
            )

    def _retry_with_backoff(
        self, tool_name: str, args: dict, handler: Any, last_error: str
    ) -> ToolExecutionResult:
        """Retry a failed tool with exponential backoff.

        Args:
            tool_name: Tool to retry
            args: Tool arguments
            handler: Callable to execute
            last_error: Previous error message

        Returns:
            ToolExecutionResult after retry attempts
        """
        tool_def = self.registry.get(tool_name)
        max_retries = 3
        base_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                delay = base_delay * (2 ** attempt)
                import time
                time.sleep(delay)

                result = handler(args)
                return ToolExecutionResult(
                    success=True,
                    data=result,
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    return ToolExecutionResult(
                        success=False,
                        data=None,
                        error=f"Retry failed after {max_retries} attempts: {last_error}, {str(e)}",
                    )

        return ToolExecutionResult(
            success=False,
            data=None,
            error=f"Retry failed: {last_error}",
        )

    def execute_batch(self, tool_calls: list[tuple[str, dict, Any]]) -> list[ToolExecutionResult]:
        """Execute multiple tools.

        Args:
            tool_calls: List of (tool_name, args, handler) tuples

        Returns:
            List of ToolExecutionResult in same order as input
        """
        results = []
        for tool_name, args, handler in tool_calls:
            result = self.execute(tool_name, args, handler)
            results.append(result)
        return results

    def get_tool_history(self) -> list[ToolCall]:
        """Get history of all tool calls."""
        return self.tool_history

    def clear_history(self) -> None:
        """Clear tool execution history."""
        self.tool_history = []


def check_loop_count(tool_history: list[ToolCall], max_loops: int = MAX_LOOPS) -> bool:
    """Check if loop count exceeds maximum (PP-01).

    Args:
        tool_history: History of tool calls
        max_loops: Maximum allowed loops

    Returns:
        True if within limit, False if exceeded
    """
    # Count "execute" phases (not think/plan/branch)
    execute_count = sum(
        1 for tc in tool_history
        if tc.tool_name in ["think", "plan", "execute", "branch"]
    )
    return execute_count < max_loops
