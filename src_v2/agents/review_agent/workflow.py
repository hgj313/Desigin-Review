"""LangGraph StateGraph for review workflow orchestration.

Per D-04: Parallel execution when both review types selected.
Uses Send API for conditional fan-out to parallel branches.

Graph structure:
    upload -> route_reviews -+-> prd_review_node
                             +-> proto_review_node
                             +-> (join via conditional edges)
                              -> aggregate_results -> generate_report
"""
from langgraph.graph import StateGraph, END

from src_v2.agents.review_agent.state import ReviewState
from src_v2.agents.review_agent.nodes import (
    upload_node,
    prd_review_node,
    proto_review_node,
    aggregate_results_node,
    generate_report_node,
    route_reviews,
)

__all__ = ["review_graph"]


def build_review_graph() -> StateGraph:
    """Build the review workflow StateGraph.

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the state graph
    graph = StateGraph(ReviewState)

    # Add nodes
    graph.add_node("upload", upload_node)
    graph.add_node("prd_review_node", prd_review_node)
    graph.add_node("proto_review_node", proto_review_node)
    graph.add_node("aggregate_results", aggregate_results_node)
    graph.add_node("generate_report", generate_report_node)

    # Set entry point
    graph.set_entry_point("upload")

    # Conditional edges for parallel fan-out via Send API
    # route_reviews returns list of Send objects for parallel execution
    graph.add_conditional_edges(
        "upload",
        route_reviews,
    )

    # After conditional edges complete, move to aggregate
    graph.add_edge("prd_review_node", "aggregate_results")
    graph.add_edge("proto_review_node", "aggregate_results")

    # After aggregate, generate report
    graph.add_edge("aggregate_results", "generate_report")

    # End after report generation
    graph.add_edge("generate_report", END)

    return graph


# Build and compile the graph once at module load
review_graph = build_review_graph().compile()
