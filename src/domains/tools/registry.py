"""Tool Registry - Centralized tool definitions for LLM Compiler.

This module defines all tools available to the LLM Compiler Agent.
Each tool has name, description, parameters, dependencies, and output schema.

References:
- ARCHITECTURE.md: Tool Registry Pattern section
- FEATURES.md: Tool definitions
- PITFALLS.md: PP-02 tool name whitelist, PP-03 dependency cycles
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from enum import Enum


class ToolParallelGroup(Enum):
    """Groups of tools that can execute in parallel."""
    RETRIEVAL = "retrieval"
    EVALUATION = "evaluation"
    NONE = None


@dataclass
class ToolDefinition:
    """Definition of a tool available to the LLM Compiler.

    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description for LLM
        parameters: JSON Schema for tool arguments
        dependencies: List of tools that must run before this one
        parallel_group: Group for parallel execution (None = sequential)
        retry_on_failure: Whether to retry on failure
        output_schema: Type for output validation
        handler: Callable that executes the tool
    """
    name: str
    description: str
    parameters: dict
    dependencies: list[str] = field(default_factory=list)
    parallel_group: Optional[ToolParallelGroup] = None
    retry_on_failure: bool = False
    output_schema: Optional[type] = None
    handler: Optional[Callable] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for LLM consumption."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
        }


class ToolRegistry:
    """Central registry for all LLM Compiler tools.

    Provides validation and execution for tools.
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._valid_names: set[str] = set()

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool.

        Args:
            tool: Tool definition to register

        Raises:
            ValueError: If tool name already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool
        self._valid_names.add(tool.name)

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        return self._tools.get(name)

    def get_all(self) -> list[ToolDefinition]:
        """Get all registered tools."""
        return list(self._tools.values())

    def validate_tool_name(self, name: str) -> bool:
        """Validate tool name against whitelist (PP-02).

        Args:
            name: Tool name to validate

        Returns:
            True if valid, False otherwise
        """
        return name in self._valid_names

    def get_tools_by_group(self, group: ToolParallelGroup) -> list[ToolDefinition]:
        """Get all tools in a parallel group."""
        if group is None:
            return []
        return [t for t in self._tools.values() if t.parallel_group == group]

    def topological_sort(self, tool_names: list[str]) -> list[str]:
        """Sort tools by dependencies using topological sort (PP-03).

        Args:
            tool_names: List of tool names to sort

        Returns:
            Tools sorted in dependency order

        Raises:
            ValueError: If cycle detected
        """
        visited = set()
        temp = set()
        result = []

        def visit(name: str):
            if name not in self._tools:
                raise ValueError(f"Unknown tool: {name}")
            if name in temp:
                raise ValueError(f"Cycle detected involving: {name}")
            if name in visited:
                return

            temp.add(name)
            tool = self._tools[name]
            for dep in tool.dependencies:
                if dep in tool_names:  # Only consider tools in our list
                    visit(dep)
            temp.remove(name)
            visited.add(name)
            result.append(name)

        for name in tool_names:
            if name not in visited:
                visit(name)

        return result

    def get_parallel_groups(self, tool_names: list[str]) -> dict[Optional[str], list[str]]:
        """Group tools by parallel_group for execution.

        Args:
            tool_names: List of tool names (after topological sort)

        Returns:
            Dict mapping group name to list of tools in that group
        """
        groups: dict[Optional[str], list[str]] = {}
        for name in tool_names:
            tool = self._tools.get(name)
            if tool:
                group = tool.parallel_group
                if group not in groups:
                    groups[group] = []
                groups[group].append(name)
        return groups


# Global registry instance
TOOL_REGISTRY = ToolRegistry()
