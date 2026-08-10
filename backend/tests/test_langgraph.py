import pytest
from app.ai import complaint_graph, build_complaint_graph, ComplaintState


def test_graph_import_and_compilation():
    """Verify that complaint_graph imports and compiles without errors."""
    assert complaint_graph is not None
    compiled = build_complaint_graph()
    assert compiled is not None


def test_graph_nodes_exist():
    """Verify that all 7 mandatory explicit nodes are present in the graph builder."""
    graph = build_complaint_graph()
    node_names = set(graph.nodes.keys())
    expected_nodes = {
        "normalize_input",
        "extract_complaint",
        "validate_complaint",
        "classify_complaint",
        "assess_risk",
        "recommend_action",
        "finalize_result",
    }
    assert expected_nodes.issubset(node_names)


def test_graph_execution_deterministic_sample():
    """Verify graph execution with deterministic input text."""
    input_state: ComplaintState = {
        "input_text": "  Customer reported damaged seal on Amoxicillin 500mg batch BCH-99.  ",
        "source_type": "email",
    }

    final_state = complaint_graph.invoke(input_state)

    assert final_state["input_text"] == "Customer reported damaged seal on Amoxicillin 500mg batch BCH-99."
    assert final_state["source_type"] == "email"
    assert "complaint_data" in final_state
    assert final_state["severity"] is not None
    assert final_state["risk_level"] is not None
    assert final_state["suggested_next_action"] is not None
    assert isinstance(final_state["confidence"], float)


def test_graph_missing_fields_detection():
    """Verify that validate_complaint identifies missing mandatory fields."""
    input_state: ComplaintState = {
        "input_text": "Incomplete complaint email with missing details",
        "source_type": "email",
        "complaint_data": {
            "product_name": "MediCure 250",
            # missing customer_name, batch_number, complaint_type, etc.
        }
    }

    final_state = complaint_graph.invoke(input_state)

    assert "missing_fields" in final_state
    assert "customer_name" in final_state["missing_fields"]
    assert "batch_number" in final_state["missing_fields"]
    assert len(final_state["validation_errors"]) > 0


def test_graph_runs_without_external_llm_calls():
    """Verify graph executes completely offline without calling Groq/LLM services."""
    input_state: ComplaintState = {
        "input_text": "Test offline graph execution",
        "source_type": "text",
        "complaint_data": {
            "product_name": "OfflineTest",
            "batch_number": "BATCH-001",
            "customer_name": "Test User",
            "complaint_type": "Quality Defect",
            "complaint_description": "Testing node graph offline flow",
        }
    }

    final_state = complaint_graph.invoke(input_state)

    assert final_state["complaint_category"] == "Quality Defect"
    assert final_state["complaint_data"]["product_name"] == "OfflineTest"
    assert len(final_state["missing_fields"]) == 0
