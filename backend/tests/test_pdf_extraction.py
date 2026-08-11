"""
Tests for PDF text extraction service and document endpoints:
- POST /api/documents/extract-text
- POST /api/documents/analyze

Programmatically generates test PDFs in memory to ensure no external test files
or Groq dependencies are required.
"""
import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.pdf_service import extract_text_from_pdf

client = TestClient(app)


def generate_test_pdf(pages_text: list[str]) -> bytes:
    """
    Generate minimal valid multi-page PDF binary data with text streams.
    """
    objects = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    page_refs = " ".join(f"{i+3} 0 R" for i in range(len(pages_text)))
    objects.append(
        f"2 0 obj\n<< /Type /Pages /Kids [{page_refs}] /Count {len(pages_text)} >>\nendobj\n".encode("latin1")
    )

    objects.append(b"99 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    content_offset = 3 + len(pages_text)
    for i in range(len(pages_text)):
        page_id = 3 + i
        stream_id = content_offset + i
        objects.append(
            f"{page_id} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 99 0 R >> >> /Contents {stream_id} 0 R >>\nendobj\n".encode("latin1")
        )

    for i, text in enumerate(pages_text):
        stream_data = f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode("latin1")
        stream_obj = (
            f"{content_offset + i} 0 obj\n<< /Length {len(stream_data)} >>\nstream\n".encode("latin1")
            + stream_data
            + b"\nendstream\nendobj\n"
        )
        objects.append(stream_obj)

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(out.tell())
        out.write(obj)
    xref_offset = out.tell()
    out.write(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode("latin1"))
    for offset in offsets[1:]:
        out.write(f"{offset:010d} 00000 n \n".encode("latin1"))
    out.write(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1"))

    return out.getvalue()


def generate_blank_pdf() -> bytes:
    """
    Generate a valid PDF containing a blank page with no text content.
    """
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


# ---------------------------------------------------------------------------
# Unit tests for pdf_service
# ---------------------------------------------------------------------------

def test_service_extract_single_page():
    pdf_bytes = generate_test_pdf(["Batch BCH-100 failed dissolution."])
    res = extract_text_from_pdf(pdf_bytes, filename="test_single.pdf")
    assert res["filename"] == "test_single.pdf"
    assert res["page_count"] == 1
    assert "Batch BCH-100 failed dissolution." in res["text"]


def test_service_extract_multi_page():
    pdf_bytes = generate_test_pdf([
        "Page 1: Complaint received regarding Amoxicillin 500mg.",
        "Page 2: Patient reports nausea and discoloration."
    ])
    res = extract_text_from_pdf(pdf_bytes, filename="test_multi.pdf")
    assert res["filename"] == "test_multi.pdf"
    assert res["page_count"] == 2
    assert "Page 1: Complaint received" in res["text"]
    assert "Page 2: Patient reports" in res["text"]


def test_service_empty_bytes_raises():
    with pytest.raises(ValueError, match="empty"):
        extract_text_from_pdf(b"", filename="empty.pdf")


def test_service_corrupted_bytes_raises():
    with pytest.raises(ValueError, match="Invalid or corrupted PDF"):
        extract_text_from_pdf(b"NOT_A_REAL_PDF_CONTENT", filename="corrupt.pdf")


# ---------------------------------------------------------------------------
# Endpoint tests: POST /api/documents/extract-text
# ---------------------------------------------------------------------------

def test_api_extract_valid_pdf_success():
    pdf_bytes = generate_test_pdf(["Customer complaint text for batch 98765."])
    files = {
        "file": ("complaint.pdf", pdf_bytes, "application/pdf")
    }
    response = client.post("/api/documents/extract-text", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "complaint.pdf"
    assert data["page_count"] == 1
    assert "Customer complaint text for batch 98765." in data["text"]


def test_api_extract_multi_page_pdf_success():
    pdf_bytes = generate_test_pdf([
        "First page complaint summary.",
        "Second page batch records details."
    ])
    files = {
        "file": ("multi_page.pdf", pdf_bytes, "application/pdf")
    }
    response = client.post("/api/documents/extract-text", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "multi_page.pdf"
    assert data["page_count"] == 2
    assert "First page" in data["text"]
    assert "Second page" in data["text"]


def test_api_non_pdf_file_rejected():
    files = {
        "file": ("sample.txt", b"This is plain text, not a PDF", "text/plain")
    }
    response = client.post("/api/documents/extract-text", files=files)
    assert response.status_code == 400
    assert "Only PDF files are accepted" in response.json()["detail"]


def test_api_empty_file_rejected():
    files = {
        "file": ("empty.pdf", b"", "application/pdf")
    }
    response = client.post("/api/documents/extract-text", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_api_malformed_pdf_rejected():
    files = {
        "file": ("broken.pdf", b"%PDF-1.4 corrupted header payload bytes", "application/pdf")
    }
    response = client.post("/api/documents/extract-text", files=files)
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower() or "pdf" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Endpoint tests: POST /api/documents/analyze
# ---------------------------------------------------------------------------

def test_api_analyze_valid_pdf_success():
    pdf_bytes = generate_test_pdf(["Customer reported severe defect in batch BCH-9999 of Paracetamol."])
    files = {
        "file": ("complaint_report.pdf", pdf_bytes, "application/pdf")
    }

    mock_graph_result = {
        "input_text": "Customer reported severe defect in batch BCH-9999 of Paracetamol.",
        "source_type": "pdf_upload",
        "complaint_data": {
            "product_name": "Paracetamol",
            "batch_number": "BCH-9999",
            "complaint_source": "pdf_upload",
            "complaint_description": "Customer reported severe defect in batch BCH-9999 of Paracetamol.",
        },
        "missing_fields": ["expiry_date"],
        "validation_errors": [],
        "complaint_category": "Quality Defect",
        "severity": "High",
        "risk_level": "Major",
        "initial_risk_assessment": "Defect reported in batch BCH-9999 requires investigation.",
        "suggested_next_action": "Quarantine affected lot and initiate QA investigation.",
        "confidence": 0.95,
        "messages": [{"role": "system", "content": "Analysis complete"}],
        "document_metadata": {"filename": "complaint_report.pdf", "page_count": 1},
    }

    with patch("app.api.documents.complaint_graph.invoke", return_value=mock_graph_result) as mock_invoke:
        response = client.post("/api/documents/analyze", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["complaint_data"]["product_name"] == "Paracetamol"
        assert data["complaint_data"]["batch_number"] == "BCH-9999"
        assert data["severity"] == "High"
        assert data["risk_level"] == "Major"
        assert data["document_metadata"]["filename"] == "complaint_report.pdf"
        assert data["document_metadata"]["page_count"] == 1

        mock_invoke.assert_called_once()
        invoked_state = mock_invoke.call_args[0][0]
        assert invoked_state["source_type"] == "pdf_upload"
        assert "Customer reported severe defect" in invoked_state["input_text"]


def test_api_analyze_multi_page_pdf_success():
    pdf_bytes = generate_test_pdf([
        "Page 1: Complaint submitted for Ibuprofen 400mg.",
        "Page 2: Batch lot number BCH-5555 manufacturing date 2024-01-01."
    ])
    files = {
        "file": ("multi_report.pdf", pdf_bytes, "application/pdf")
    }

    mock_graph_result = {
        "input_text": "Page 1: Complaint submitted for Ibuprofen 400mg.\n\nPage 2: Batch lot number BCH-5555 manufacturing date 2024-01-01.",
        "source_type": "pdf_upload",
        "complaint_data": {
            "product_name": "Ibuprofen",
            "product_strength": "400mg",
            "batch_number": "BCH-5555",
            "complaint_source": "pdf_upload",
        },
        "missing_fields": [],
        "validation_errors": [],
        "severity": "Medium",
        "risk_level": "Minor",
        "confidence": 0.90,
        "document_metadata": {"filename": "multi_report.pdf", "page_count": 2},
    }

    with patch("app.api.documents.complaint_graph.invoke", return_value=mock_graph_result) as mock_invoke:
        response = client.post("/api/documents/analyze", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["complaint_data"]["product_name"] == "Ibuprofen"
        assert data["document_metadata"]["page_count"] == 2

        invoked_state = mock_invoke.call_args[0][0]
        assert "Page 1: Complaint" in invoked_state["input_text"]
        assert "Page 2: Batch" in invoked_state["input_text"]


def test_api_analyze_invalid_pdf_rejected():
    files = {
        "file": ("document.docx", b"Not a PDF file content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }
    response = client.post("/api/documents/analyze", files=files)
    assert response.status_code == 400
    assert "Only PDF files are accepted" in response.json()["detail"]


def test_api_analyze_empty_pdf_rejected():
    files = {
        "file": ("empty.pdf", b"", "application/pdf")
    }
    response = client.post("/api/documents/analyze", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_api_analyze_pdf_no_extractable_text_rejected():
    blank_pdf = generate_blank_pdf()
    files = {
        "file": ("blank.pdf", blank_pdf, "application/pdf")
    }
    response = client.post("/api/documents/analyze", files=files)
    assert response.status_code == 400
    assert "no extractable text" in response.json()["detail"].lower()
