"""
Tests for POST /api/complaints/analyze.

All tests mock complaint_graph so no real Groq API calls are made.
The existing CRUD endpoint suite is unaffected.
"""
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ANALYZE_URL = "/api/complaints/analyze"

# ---------------------------------------------------------------------------
# Shared mock state that mimics a realistic finalize_result output
# ---------------------------------------------------------------------------

MOCK_GRAPH_RESULT = {
    "complaint_data": {
        "complaint_source": "text",
        "customer_name": "Jane Roberts",
        "product_name": "Metformin HCl",
        "product_strength": "500mg",
        "batch_number": "MET-2026-004",
        "manufacturing_date": None,
        "expiry_date": None,
        "affected_quantity": 60.0,
        "affected_quantity_unit": "tablets",
        "complaint_type": "Quality Defect",
        "complaint_date": "2026-08-10",
        "complaint_description": "Visible yellowish discolouration and unusual odour on 60 tablets.",
        "severity": "Low",
        "risk_level": "Minor",
        "initial_risk_assessment": "Standard complaint intake processed.",
        "suggested_next_action": "Log complaint, verify batch records, and await standard QA review.",
        "ai_confidence": 0.95,
    },
    "missing_fields": [],
    "validation_errors": [],
    "complaint_category": "Quality Defect",
    "severity": "Low",
    "risk_level": "Minor",
    "initial_risk_assessment": "Standard complaint intake processed.",
    "suggested_next_action": "Log complaint, verify batch records, and await standard QA review.",
    "confidence": 0.95,
    "messages": [{"role": "user", "content": "test input"}],
    "document_metadata": None,
}


# ---------------------------------------------------------------------------
# 1. Successful analysis — full structured response
# ---------------------------------------------------------------------------

def test_analyze_successful_returns_structured_result():
    """Mocked graph returns full extraction; response shape is correct."""
    with patch("app.api.analysis.complaint_graph") as mock_graph:
        mock_graph.invoke.return_value = MOCK_GRAPH_RESULT

        resp = client.post(ANALYZE_URL, json={
            "input_text": "Metformin HCl 500mg batch MET-2026-004 discolouration.",
            "source_type": "text",
        })

    assert resp.status_code == 200
    body = resp.json()

    # Core extracted fields
    assert body["complaint_data"]["customer_name"] == "Jane Roberts"
    assert body["complaint_data"]["product_name"] == "Metformin HCl"
    assert body["complaint_data"]["batch_number"] == "MET-2026-004"
    assert body["complaint_data"]["affected_quantity"] == 60.0

    # Risk assessment fields
    assert body["severity"] == "Low"
    assert body["risk_level"] == "Minor"
    assert body["confidence"] == 0.95
    assert body["suggested_next_action"] is not None
    assert body["initial_risk_assessment"] is not None

    # Missing-fields list present and empty for a complete complaint
    assert body["missing_fields"] == []
    assert body["validation_errors"] == []


# ---------------------------------------------------------------------------
# 2. Empty input — Pydantic validation rejects it before graph is called
# ---------------------------------------------------------------------------

def test_analyze_empty_input_returns_422():
    """Empty input_text must be rejected with HTTP 422 before reaching the graph."""
    with patch("app.api.analysis.complaint_graph") as mock_graph:
        resp = client.post(ANALYZE_URL, json={"input_text": "   ", "source_type": "text"})
        mock_graph.invoke.assert_not_called()

    assert resp.status_code == 422


def test_analyze_missing_input_field_returns_422():
    """Omitting input_text entirely must be rejected with HTTP 422."""
    resp = client.post(ANALYZE_URL, json={"source_type": "text"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 3. source_type handling — unknown value normalised to "other"
# ---------------------------------------------------------------------------

def test_analyze_unknown_source_type_normalised():
    """An unrecognised source_type is normalised to 'other' without erroring."""
    captured_state = {}

    def capture_invoke(state):
        captured_state.update(state)
        return MOCK_GRAPH_RESULT

    with patch("app.api.analysis.complaint_graph") as mock_graph:
        mock_graph.invoke.side_effect = capture_invoke
        resp = client.post(ANALYZE_URL, json={
            "input_text": "Sample complaint text.",
            "source_type": "fax_machine",   # not in allowed set
        })

    assert resp.status_code == 200
    assert captured_state.get("source_type") == "other"


# ---------------------------------------------------------------------------
# 4. Graph result mapped correctly — missing_fields surfaced to response
# ---------------------------------------------------------------------------

def test_analyze_missing_fields_surfaced_in_response():
    """missing_fields produced by validate_complaint node reach the response."""
    partial_result = dict(MOCK_GRAPH_RESULT)
    partial_result["missing_fields"] = ["customer_name", "batch_number"]
    partial_result["validation_errors"] = [
        "Missing required complaint details: customer_name, batch_number"
    ]

    with patch("app.api.analysis.complaint_graph") as mock_graph:
        mock_graph.invoke.return_value = partial_result
        resp = client.post(ANALYZE_URL, json={
            "input_text": "Tablets had an unusual smell.",
            "source_type": "email",
        })

    assert resp.status_code == 200
    body = resp.json()
    assert "customer_name" in body["missing_fields"]
    assert "batch_number" in body["missing_fields"]
    assert len(body["validation_errors"]) == 1


# ---------------------------------------------------------------------------
# 5. Unexpected graph exception → safe HTTP 500 (no internal details leaked)
# ---------------------------------------------------------------------------

def test_analyze_graph_exception_returns_safe_500():
    """If the graph raises an unexpected exception, the route returns HTTP 500
    with a generic safe message — no stack trace, no API key in response."""
    with patch("app.api.analysis.complaint_graph") as mock_graph:
        mock_graph.invoke.side_effect = RuntimeError("Internal graph failure")
        resp = client.post(ANALYZE_URL, json={
            "input_text": "Sample complaint text.",
            "source_type": "text",
        })

    assert resp.status_code == 500
    body = resp.json()
    # Message must be a generic safe string, not the raw exception
    assert "detail" in body
    assert "RuntimeError" not in body["detail"]
    assert "Internal graph failure" not in body["detail"]


# ---------------------------------------------------------------------------
# 6. Existing CRUD endpoints are unaffected
# ---------------------------------------------------------------------------

def test_existing_crud_list_endpoint_still_works():
    """GET /api/complaints must still respond (not shadowed by the new router)."""
    resp = client.get("/api/complaints")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body


def test_existing_health_endpoint_still_works():
    """GET /api/health must still respond."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
