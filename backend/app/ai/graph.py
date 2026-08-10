from langgraph.graph import StateGraph, START, END

from app.ai.state import ComplaintState
from app.ai.nodes import (
    normalize_input,
    extract_complaint,
    validate_complaint,
    classify_complaint,
    assess_risk,
    recommend_action,
    finalize_result,
)


def build_complaint_graph():
    """
    Construct and compile the explicit 7-node LangGraph workflow for AIVOA Complaint Intelligence.

    Workflow Sequence:
    START -> normalize_input -> extract_complaint -> validate_complaint
          -> classify_complaint -> assess_risk -> recommend_action
          -> finalize_result -> END
    """
    builder = StateGraph(ComplaintState)

    # 1. Add explicit nodes
    builder.add_node("normalize_input", normalize_input)
    builder.add_node("extract_complaint", extract_complaint)
    builder.add_node("validate_complaint", validate_complaint)
    builder.add_node("classify_complaint", classify_complaint)
    builder.add_node("assess_risk", assess_risk)
    builder.add_node("recommend_action", recommend_action)
    builder.add_node("finalize_result", finalize_result)

    # 2. Add explicit sequential edges
    builder.add_edge(START, "normalize_input")
    builder.add_edge("normalize_input", "extract_complaint")
    builder.add_edge("extract_complaint", "validate_complaint")
    builder.add_edge("validate_complaint", "classify_complaint")
    builder.add_edge("classify_complaint", "assess_risk")
    builder.add_edge("assess_risk", "recommend_action")
    builder.add_edge("recommend_action", "finalize_result")
    builder.add_edge("finalize_result", END)

    # 3. Compile and return executable graph
    return builder.compile()


# Expose compiled graph instance for reuse
complaint_graph = build_complaint_graph()
