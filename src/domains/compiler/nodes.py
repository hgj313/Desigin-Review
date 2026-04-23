"""LangGraph nodes implementing the LLM Compiler workflow.

References:
- ARCHITECTURE.md: LLM Compiler Pattern
- FEATURES.md: Tool orchestration flow
"""

from typing import Any

from src.domains.state import ReviewState, MAX_LOOPS
from src.domains.tools import TOOL_REGISTRY, TOOL_HANDLERS
from src.domains.compiler.core import LLMCompiler, CompilerPhase


def think_node(state: ReviewState) -> dict:
    """Think node: LLM reasons about required tools.

    Args:
        state: Current review state

    Returns:
        State update with tools_to_call and reasoning
    """
    compiler = LLMCompiler()

    # Determine document context
    document_type = state.get("document_type", "unknown")
    existing_findings = (
        len(state.get("prd_findings", [])) +
        len(state.get("proto_findings", []))
    )

    # Rule-based tool selection (simplified - full impl would use LLM)
    tools_to_call = []

    if document_type in ["prd", "both"]:
        tools_to_call.append("search_standards")
        if existing_findings == 0:
            tools_to_call.append("evaluate_structure")
            tools_to_call.append("evaluate_terminology")

    if document_type in ["prototype", "both"]:
        tools_to_call.append("analyze_prototype")
        if existing_findings == 0:
            tools_to_call.append("evaluate_layout")
            tools_to_call.append("evaluate_accessibility")

    # Check if we should generate report
    if existing_findings >= 3 or state.get("tool_history"):
        tools_to_call.append("generate_report")

    reasoning = f"Document type: {document_type}, Existing findings: {existing_findings}, Tools: {tools_to_call}"

    # Increment loop count
    current_loop = state.get("loop_count", 0)

    return {
        "current_plan": tools_to_call,
        "loop_count": current_loop + 1,
        "tool_history": [{
            "phase": "think",
            "reasoning": reasoning,
            "tools_suggested": tools_to_call,
        }],
    }


def plan_node(state: ReviewState) -> dict:
    """Plan node: Sort tools by dependencies.

    Args:
        state: Current review state with tools_to_call

    Returns:
        State update with sorted tools
    """
    tools_to_call = state.get("current_plan", [])

    if not tools_to_call:
        return {"current_plan": []}

    # Filter to valid tools
    valid_tools = [t for t in tools_to_call if TOOL_REGISTRY.validate_tool_name(t)]

    # Topological sort
    try:
        sorted_tools = TOOL_REGISTRY.topological_sort(valid_tools)
    except ValueError:
        # Cycle detected - use original order
        sorted_tools = valid_tools

    return {
        "current_plan": sorted_tools,
        "tool_history": state.get("tool_history", []) + [{
            "phase": "plan",
            "tools_sorted": sorted_tools,
        }],
    }


def execute_node(state: ReviewState) -> dict:
    """Execute node: Run tools and collect results.

    Args:
        state: Current review state with sorted tools in current_plan

    Returns:
        State update with tool results and findings
    """
    tools_to_call = state.get("current_plan", [])
    if not tools_to_call:
        return {}

    from src.domains.tools.handlers import TOOL_HANDLERS

    tool_results = []
    state_updates = {}
    loop_count = state.get("loop_count", 0)

    # Group tools by parallel execution
    parallel_groups = TOOL_REGISTRY.get_parallel_groups(tools_to_call)

    for group, group_tools in parallel_groups.items():
        for tool_name in group_tools:
            handler = TOOL_HANDLERS.get(tool_name)
            if not handler:
                continue

            # Build args based on tool and state
            args = _build_tool_args(tool_name, state)

            try:
                result = handler(args)
                tool_results.append({
                    "tool": tool_name,
                    "result": result if not isinstance(result, dict) else result,
                    "success": True,
                })

                # Update state based on result
                _update_state_from_result(tool_name, result, state_updates)

            except Exception as e:
                tool_results.append({
                    "tool": tool_name,
                    "error": str(e),
                    "success": False,
                })

    # Record execution
    tool_history_entry = {
        "phase": "execute",
        "tools_executed": tools_to_call,
        "results": tool_results,
        "loop_count": loop_count,
    }

    state_updates.setdefault("tool_history", [])
    state_updates["tool_history"].append(tool_history_entry)

    return state_updates


def branch_node(state: ReviewState) -> str:
    """Branch node: Decide next action.

    Args:
        state: Current review state

    Returns:
        Next node name: "think", "execute", or "__end__"
    """
    loop_count = state.get("loop_count", 0) + 1

    # Check MAX_LOOPS (PP-01)
    if loop_count >= MAX_LOOPS:
        return "__end__"

    # Check if we have a report
    if state.get("final_report") is not None:
        return "__end__"

    # Check if we have enough findings
    findings_count = (
        len(state.get("prd_findings", [])) +
        len(state.get("proto_findings", []))
    )
    if findings_count >= 5:
        return "__end__"

    # Check tool history for errors
    tool_history = state.get("tool_history", [])
    if tool_history:
        last_execution = tool_history[-1]
        if "results" in last_execution:
            failed = [r for r in last_execution["results"] if not r.get("success", False)]
            if failed and loop_count >= MAX_LOOPS // 2:
                return "__end__"

    # Continue reviewing
    return "think"


def _build_tool_args(tool_name: str, state: ReviewState) -> dict:
    """Build arguments for a tool based on current state."""
    args = {}

    if tool_name == "search_standards":
        args = {
            "query": state.get("document_path", ""),
            "dimension": None,
            "limit": 5,
        }
    elif tool_name == "analyze_prototype":
        image_paths = state.get("image_paths", [])
        args = {
            "image_path": image_paths[0] if image_paths else None,
            "analysis_type": "full",
        }
    elif tool_name == "evaluate_structure":
        args = {
            "content": state.get("document_path", ""),
            "standards": state.get("retrieved_standards", {}).get("structure", []),
        }
    elif tool_name == "evaluate_terminology":
        args = {
            "content": state.get("document_path", ""),
            "standards": state.get("retrieved_standards", {}).get("terminology", []),
        }
    elif tool_name == "evaluate_completeness":
        args = {
            "content": state.get("document_path", ""),
            "standards": state.get("retrieved_standards", {}).get("structure", []),
        }
    elif tool_name == "evaluate_layout":
        args = {
            "vision_result": state.get("vision_result", {}),
            "standards": state.get("retrieved_standards", {}).get("layout", []),
        }
    elif tool_name == "evaluate_accessibility":
        args = {
            "vision_result": state.get("vision_result", {}),
            "standards": state.get("retrieved_standards", {}).get("accessibility", []),
        }
    elif tool_name == "generate_report":
        args = {
            "findings": state.get("prd_findings", []) + state.get("proto_findings", []),
            "report_format": "detailed",
        }

    return args


def _update_state_from_result(
    tool_name: str,
    result: Any,
    state_updates: dict
) -> None:
    """Update state based on tool execution result."""
    if tool_name == "search_standards" and isinstance(result, list):
        state_updates.setdefault("retrieved_standards", {})
        for item in result:
            if isinstance(item, dict):
                metadata = item.get("metadata", {})
                dim = metadata.get("dimension", "general")
                content = item.get("content", "")
                if dim not in state_updates["retrieved_standards"]:
                    state_updates["retrieved_standards"][dim] = []
                if content and content not in state_updates["retrieved_standards"][dim]:
                    state_updates["retrieved_standards"][dim].append(content)

    elif tool_name in ["evaluate_structure", "evaluate_terminology", "evaluate_completeness"]:
        if isinstance(result, dict) and "findings" in result:
            state_updates.setdefault("prd_findings", [])
            for finding in result["findings"]:
                if isinstance(finding, dict):
                    state_updates["prd_findings"].append(finding)

    elif tool_name in ["evaluate_layout", "evaluate_accessibility"]:
        if isinstance(result, dict) and "findings" in result:
            state_updates.setdefault("proto_findings", [])
            for finding in result["findings"]:
                if isinstance(finding, dict):
                    state_updates["proto_findings"].append(finding)

    elif tool_name == "analyze_prototype" and isinstance(result, dict):
        state_updates["vision_result"] = result

    elif tool_name == "generate_report" and isinstance(result, dict):
        state_updates["final_report"] = result
