"""LangGraph workflow for LLM Compiler Agent.

References:
- ARCHITECTURE.md: LLM Compiler Pattern
- STACK.md: LangGraph StateGraph
"""

from langgraph.graph import StateGraph, END

from src.domains.state import ReviewState, MAX_LOOPS
from src.domains.checkpoint import default_checkpointer
from src.domains.compiler.nodes import (
    think_node,
    plan_node,
    execute_node,
)


def _should_continue(state: ReviewState) -> str:
    """Determine if workflow should continue or end.

    This is the branch routing function - returns node name to go to next.

    Args:
        state: Current review state

    Returns:
        "think" to continue loop, "__end__" to finish
    """
    loop_count = state.get("loop_count", 0)

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


def create_review_workflow() -> StateGraph:
    """Create the LLM Compiler review workflow.

    Graph structure:
        think -> plan -> execute
                            |
                            v
                      _should_continue (branch decision)
                            |
                        +---+---+
                        |       |
                    "think"  "__end__"

    Returns:
        Compiled StateGraph ready to run
    """
    # Create graph with ReviewState
    workflow = StateGraph(ReviewState)

    # Add nodes
    workflow.add_node("think", think_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("execute", execute_node)

    # Define edges - linear flow to execute
    workflow.add_edge("think", "plan")
    workflow.add_edge("plan", "execute")

    # After execute, use conditional edges to decide next
    workflow.add_conditional_edges(
        "execute",
        _should_continue,
        {
            "think": "think",  # Continue to next iteration
            "__end__": END,    # End workflow
        }
    )

    # Set entry point
    workflow.set_entry_point("think")

    # Compile with checkpointer
    return workflow.compile(checkpointer=default_checkpointer)


# Global workflow instance
review_workflow = create_review_workflow()
