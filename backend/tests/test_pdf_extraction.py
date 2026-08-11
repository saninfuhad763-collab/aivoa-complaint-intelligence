"""
Tests for PDF text extraction service and POST /api/documents/extract-text endpoint.

Programmatically generates test PDFs in memory to ensure no external test files
or Groq dependencies are required.
"""
import io
import pytest
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

    for text in pages_text:
        stream_data = f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode("latin1")
        objects.append(
            f"<< /Length {len(stream_data)} >>\nstream\n".encode("latin1")
            + stream_data
            + b"\nendstream\n"
        )
        # Fix stream object wrapping
        objects[-1] = (
            f"{content_offset + pages_text.index(text)} 0 obj\n".encode("latin1")
            + objects[-1]
            + b"endobj\n"
        )

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
# API endpoint tests: POST /api/documents/extract-text
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
