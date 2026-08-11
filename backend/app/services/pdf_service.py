"""
PDF text extraction service using pypdf.

Provides in-memory PDF parsing to extract page text and metadata
without saving files to disk or exposing filesystem paths.
"""
import io
import logging
from typing import Dict, Any
from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes, filename: str = "document.pdf") -> Dict[str, Any]:
    """
    Extract text and page count from raw PDF bytes.

    Args:
        file_bytes: Binary contents of the uploaded PDF.
        filename: Original filename for reporting.

    Returns:
        Dict containing:
            - filename: str
            - page_count: int
            - text: str

    Raises:
        ValueError: If file is empty, not a valid PDF, or unreadable.
    """
    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    try:
        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)
        
        page_count = len(reader.pages)
        if page_count == 0:
            raise ValueError("PDF contains no pages.")

        extracted_pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_pages.append(page_text.strip())

        full_text = "\n\n".join(extracted_pages).strip()

        return {
            "filename": filename,
            "page_count": page_count,
            "text": full_text
        }
    except (PdfReadError, Exception) as exc:
        if isinstance(exc, ValueError):
            raise
        logger.error("Failed to parse PDF file '%s': %s", filename, exc)
        raise ValueError("Invalid or corrupted PDF file.") from exc
