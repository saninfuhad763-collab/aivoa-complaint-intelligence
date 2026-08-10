from unittest.mock import MagicMock, patch
import pytest

from app.core.config import Settings
from app.ai.groq_service import (
    get_groq_llm,
    extract_complaint_with_groq,
    AIExtractionOutput,
)
from app.ai import complaint_graph, ComplaintState


def test_groq_model_configuration_reads_correctly():
    """1. Test that GROQ_MODEL configuration reads llama-3.3-70b-versatile correctly."""
    custom_settings = Settings(GROQ_API_KEY="mock-key", GROQ_MODEL="llama-3.3-70b-versatile")
    assert custom_settings.GROQ_MODEL == "llama-3.3-70b-versatile"


def test_default_model_is_llama_3_3_70b_versatile():
    """2. Test that default model requested is llama-3.3-70b-versatile when no override is provided."""
    with patch("app.ai.groq_service.settings.GROQ_API_KEY", "mock-key"):
        with patch("app.ai.groq_service.settings.GROQ_MODEL", "llama-3.3-70b-versatile"):
            llm = get_groq_llm()
            assert llm.model_name == "llama-3.3-70b-versatile"


def test_missing_groq_api_key_handled_cleanly():
    """3. Test that missing GROQ_API_KEY is handled cleanly without crashing."""
    with patch("app.ai.groq_service.settings.GROQ_API_KEY", ""):
        res = extract_complaint_with_groq("Sample text")
        assert res["error"] is not None
        assert "GROQ_API_KEY is not configured" in res["error"]
        assert len(res["missing_fields"]) > 0


def test_structured_output_parsing_with_mocked_llm():
    """4 & 5. Test structured output parsing using mocked LLM output into ComplaintState."""
    mock_extracted = AIExtractionOutput(
        complaint_source="email",
        customer_name="Dr. Alice Smith",
        product_name="Amoxicillin 500mg",
        product_strength="500mg",
        batch_number="BCH-98765",
        affected_quantity=20.0,
        affected_quantity_unit="boxes",
        complaint_type="Packaging Defect",
        complaint_description="Blister foil damaged upon arrival.",
        missing_fields=["manufacturing_date", "expiry_date"],
        confidence=0.92,
    )

    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_chain = MagicMock()

    mock_llm.with_structured_output.return_value = mock_structured
    with patch("app.ai.groq_service.EXTRACTION_PROMPT") as mock_prompt:
        mock_prompt.__or__.return_value = mock_chain
        mock_chain.invoke.return_value = mock_extracted

        res = extract_complaint_with_groq("Input complaint text", source_type="email", llm_client=mock_llm)

    assert res["error"] is None
    assert res["confidence"] == 0.92
    assert res["extracted_data"]["customer_name"] == "Dr. Alice Smith"
    assert res["extracted_data"]["product_name"] == "Amoxicillin 500mg"
    assert res["extracted_data"]["batch_number"] == "BCH-98765"
    assert "manufacturing_date" in res["missing_fields"]


def test_missing_fields_preserved_as_null():
    """6. Test that missing fields remain null/missing."""
    mock_extracted = AIExtractionOutput(
        complaint_source="email",
        customer_name=None,
        product_name="MediCure 100",
        batch_number=None,
        missing_fields=["customer_name", "batch_number"],
        confidence=0.75,
    )

    mock_llm = MagicMock()
    mock_chain = MagicMock()
    mock_llm.with_structured_output.return_value = MagicMock()

    with patch("app.ai.groq_service.EXTRACTION_PROMPT") as mock_prompt:
        mock_prompt.__or__.return_value = mock_chain
        mock_chain.invoke.return_value = mock_extracted

        res = extract_complaint_with_groq("Incomplete complaint text", llm_client=mock_llm)

    assert res["extracted_data"]["customer_name"] is None
    assert res["extracted_data"]["batch_number"] is None
    assert "customer_name" in res["missing_fields"]


def test_malformed_model_output_handled_safely():
    """7 & 8. Test that malformed model output/exception is caught safely without leaking keys."""
    mock_llm = MagicMock()
    mock_llm.with_structured_output.side_effect = Exception("Malformed JSON from LLM - mock-secret-key-12345")

    with patch("app.ai.groq_service.settings.GROQ_API_KEY", "mock-secret-key-12345"):
        res = extract_complaint_with_groq("Test complaint", llm_client=mock_llm)

    assert res["error"] is not None
    # Secret must be redacted
    assert "mock-secret-key-12345" not in res["error"]
    assert "[REDACTED_API_KEY]" in res["error"] or "Malformed JSON" in res["error"]
    assert res["confidence"] == 0.0


def test_empty_input_handled_safely():
    """9. Test that empty input text returns safe empty result."""
    res = extract_complaint_with_groq("   ")
    assert res["error"] == "Empty input text provided"
    assert res["confidence"] == 0.0
    assert len(res["missing_fields"]) > 0


def test_extract_complaint_node_with_mocked_groq():
    """10. Test extract_complaint node in LangGraph pipeline using mocked Groq."""
    mock_extracted = AIExtractionOutput(
        complaint_source="web_form",
        customer_name="PharmCorp Clinic",
        product_name="CardioRelief",
        product_strength="10mg",
        batch_number="CR-2024-55",
        affected_quantity=100.0,
        affected_quantity_unit="tablets",
        complaint_type="Quality Defect",
        complaint_description="Tablets discolored.",
        missing_fields=[],
        confidence=0.95,
    )

    with patch("app.ai.nodes.settings.GROQ_API_KEY", "mock-key"):
        with patch("app.ai.groq_service.get_groq_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_chain = MagicMock()
            mock_get_llm.return_value = mock_llm
            mock_llm.with_structured_output.return_value = MagicMock()

            with patch("app.ai.groq_service.EXTRACTION_PROMPT") as mock_prompt:
                mock_prompt.__or__.return_value = mock_chain
                mock_chain.invoke.return_value = mock_extracted

                input_state: ComplaintState = {
                    "input_text": "PharmCorp Clinic reported CardioRelief 10mg batch CR-2024-55 tablets discolored.",
                    "source_type": "web_form",
                }

                final_state = complaint_graph.invoke(input_state)

    assert final_state["complaint_data"]["product_name"] == "CardioRelief"
    assert final_state["complaint_data"]["batch_number"] == "CR-2024-55"
    assert final_state["complaint_data"]["customer_name"] == "PharmCorp Clinic"
