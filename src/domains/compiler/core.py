"""LLM Compiler Core - Think/Plan/Execute/Branch Loop.

Implements the LLM Compiler pattern from ARCHITECTURE.md section 1.

References:
- ARCHITECTURE.md: LLM Compiler Pattern
- FEATURES.md: Tool orchestration flow
- PITFALLS.md: PP-01 MAX_LOOPS, PP-03 cycle detection
"""

from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum

from src.domains.state import ReviewState, MAX_LOOPS
from src.domains.tools import TOOL_REGISTRY, ToolExecutor


class CompilerPhase(Enum):
    """LLM Compiler phases."""
    THINK = "think"
    PLAN = "plan"
    EXECUTE = "execute"
    BRANCH = "branch"


@dataclass
class CompilerResult:
    """Result of a compiler iteration."""
    phase: CompilerPhase
    decision: str  # What the LLM decided
    tools_to_call: list[str]
    state_update: dict
    should_continue: bool


class LLMCompiler:
    """LLM Compiler Agent Core.

    Implements Think -> Plan -> Execute -> Branch loop.
    """

    def __init__(self, llm=None):
        self.llm = llm
        self.executor = ToolExecutor()
        self.loop_count = 0

    def think(self, state: ReviewState) -> CompilerResult:
        """Think phase: LLM reasons about what tools are needed.

        Args:
            state: Current review state

        Returns:
            CompilerResult with reasoning and tool suggestions
        """
        # Build context for LLM
        document_type = state.get("document_type", "unknown")
        document_path = state.get("document_path", "")
        existing_findings_count = (
            len(state.get("prd_findings", [])) +
            len(state.get("proto_findings", []))
        )
        tool_history_count = len(state.get("tool_history", []))

        # Simple rule-based thinking for now
        # Full implementation would use LLM
        tools_needed = []

        if document_type in ["prd", "both"]:
            tools_needed.extend(["search_standards"])
            if existing_findings_count == 0:
                tools_needed.extend(["evaluate_structure", "evaluate_terminology"])

        if document_type in ["prototype", "both"]:
            tools_needed.extend(["analyze_prototype"])
            if existing_findings_count == 0:
                tools_needed.extend(["evaluate_layout", "evaluate_accessibility"])

        # Check if we have enough findings to generate report
        if existing_findings_count > 0 or tool_history_count > 5:
            tools_needed.append("generate_report")

        decision = f"Need to call: {', '.join(tools_needed)}"

        return CompilerResult(
            phase=CompilerPhase.THINK,
            decision=decision,
            tools_to_call=tools_needed,
            state_update={},
            should_continue=True,
        )

    def plan(self, tools: list[str]) -> list[str]:
        """Plan phase: Sort tools by dependencies.

        Args:
            tools: Raw list of tools suggested by Think

        Returns:
            Topologically sorted tool list
        """
        if not tools:
            return []

        # Filter to valid tools
        valid_tools = [t for t in tools if TOOL_REGISTRY.validate_tool_name(t)]

        # Topological sort
        try:
            sorted_tools = TOOL_REGISTRY.topological_sort(valid_tools)
            return sorted_tools
        except ValueError as e:
            # Cycle detected - fall back to original order
            return valid_tools

    def execute(
        self,
        tools: list[str],
        state: ReviewState,
        handlers: dict[str, Any]
    ) -> tuple[list[dict], dict]:
        """Execute phase: Run tools and collect results.

        Args:
            tools: Topologically sorted tool list
            state: Current review state
            handlers: Tool handler functions

        Returns:
            Tuple of (tool_results, state_updates)
        """
        from src.domains.tools.handlers import TOOL_HANDLERS

        results = []
        state_updates = {}

        # Group by parallel execution
        parallel_groups = TOOL_REGISTRY.get_parallel_groups(tools)

        # Execute each group
        for group, group_tools in parallel_groups.items():
            if group is not None:  # Parallel execution
                # Execute all tools in group concurrently
                for tool_name in group_tools:
                    handler = handlers.get(tool_name, TOOL_HANDLERS.get(tool_name))
                    if handler:
                        args = self._build_tool_args(tool_name, state)
                        result = self.executor.execute(tool_name, args, handler)
                        results.append({
                            "tool": tool_name,
                            "result": result.data,
                            "success": result.success,
                            "error": result.error,
                        })
            else:  # Sequential execution
                for tool_name in group_tools:
                    handler = handlers.get(tool_name, TOOL_HANDLERS.get(tool_name))
                    if handler:
                        args = self._build_tool_args(tool_name, state)
                        result = self.executor.execute(tool_name, args, handler)
                        results.append({
                            "tool": tool_name,
                            "result": result.data,
                            "success": result.success,
                            "error": result.error,
                        })

                        # Update state based on results
                        self._update_state_from_result(tool_name, result, state_updates)

        return results, state_updates

    def branch(self, state: ReviewState, results: list[dict]) -> tuple[str, dict]:
        """Branch phase: Decide whether to continue or finish.

        Args:
            state: Current review state
            results: Results from Execute phase

        Returns:
            Tuple of (action, state_update)
            action is "CONTINUE", "FINALIZE", or "RETRY"
        """
        # Check MAX_LOOPS (PP-01)
        self.loop_count += 1
        if self.loop_count >= MAX_LOOPS:
            return "FINALIZE", {"loop_count": self.loop_count}

        # Check for errors
        errors = [r for r in results if not r.get("success", False)]
        if errors:
            # Some tools failed - decide whether to retry
            if self.loop_count < MAX_LOOPS // 2:
                return "RETRY", {"loop_count": self.loop_count}
            else:
                return "FINALIZE", {"loop_count": self.loop_count}

        # Check if we have a report
        if state.get("final_report") is not None:
            return "FINALIZE", {"loop_count": self.loop_count}

        # Check if we have enough findings
        findings_count = (
            len(state.get("prd_findings", [])) +
            len(state.get("proto_findings", []))
        )
        if findings_count >= 5:
            return "FINALIZE", {"loop_count": self.loop_count}

        # Continue for more review
        return "CONTINUE", {"loop_count": self.loop_count}

    def _build_tool_args(self, tool_name: str, state: ReviewState) -> dict:
        """Build arguments for a tool based on current state."""
        args = {}

        if tool_name == "search_standards":
            # Determine dimension from context
            document_type = state.get("document_type", "prd")
            args = {
                "query": state.get("document_path", ""),
                "dimension": None,  # Search all
                "limit": 5,
            }
        elif tool_name == "analyze_prototype":
            args = {
                "image_path": state.get("image_paths", [None])[0] if state.get("image_paths") else None,
                "analysis_type": "full",
            }
        elif tool_name == "evaluate_structure":
            # Would need actual content from document
            args = {
                "content": state.get("document_path", ""),
                "standards": state.get("retrieved_standards", {}).get("structure", []),
            }
        elif tool_name == "generate_report":
            args = {
                "findings": state.get("prd_findings", []) + state.get("proto_findings", []),
                "report_format": "detailed",
            }

        return args

    def _update_state_from_result(
        self,
        tool_name: str,
        result: Any,
        state_updates: dict
    ) -> None:
        """Update state based on tool execution result."""
        if not result.success:
            return

        data = result.data
        if tool_name == "search_standards" and isinstance(data, list):
            state_updates.setdefault("retrieved_standards", {})
            for item in data:
                if "metadata" in item:
                    dim = item["metadata"].get("dimension", "general")
                    if dim not in state_updates["retrieved_standards"]:
                        state_updates["retrieved_standards"][dim] = []
                    state_updates["retrieved_standards"][dim].append(item.get("content", ""))
                else:
                    state_updates["retrieved_standards"].setdefault("general", []).append(item.get("content", ""))

    def run(self, state: ReviewState, handlers: dict[str, Any]) -> dict:
        """Run the full compiler loop.

        Args:
            state: Initial review state
            handlers: Tool handler functions

        Returns:
            Final state after compiler completes
        """
        while True:
            # Think
            think_result = self.think(state)
            if not think_result.should_continue:
                break

            # Plan
            sorted_tools = self.plan(think_result.tools_to_call)
            if not sorted_tools:
                break

            # Execute
            results, state_updates = self.execute(sorted_tools, state, handlers)

            # Apply state updates
            for key, value in state_updates.items():
                if key in state:
                    if isinstance(state[key], list) and isinstance(value, list):
                        state[key].extend(value)
                    elif isinstance(state[key], dict) and isinstance(value, dict):
                        state[key].update(value)
                    else:
                        state[key] = value

            # Branch
            action, branch_updates = self.branch(state, results)
            state.update(branch_updates)

            if action == "FINALIZE":
                break
            elif action == "RETRY":
                continue

        return state
