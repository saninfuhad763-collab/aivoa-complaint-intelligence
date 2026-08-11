"""
POST /api/documents/extract-text

Endpoint for extracting text from uploaded PDF documents.
Processing is performed in-memory; uploaded files are not stored on disk or database.
"""
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from pydantic import BaseModel, Field

from app.services.pdf_service import extract_text_from_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


class PDFExtractResponse(BaseModel):
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    page_count: int = Field(..., description="Number of pages in the PDF")
    text: str = Field(..., description="Extracted text from all readable pages")


@router.post(
    "/extract-text",
    response_model=PDFExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract text from an uploaded PDF document",
    description="Upload a PDF file to extract readable text in memory without persistence.",
)
async def extract_pdf_text(
    file: UploadFile = File(...)
) -> PDFExtractResponse:
    """
    Accept a PDF file upload, extract text, and return metadata and text content.
    """
    filename = file.filename or "document.pdf"

    # Validate file extension and MIME content type
    is_pdf_ext = filename.lower().endswith(".pdf")
    content_type = (file.content_type or "").lower()
    is_pdf_mime = any(
        mime in content_type
        for mime in ["application/pdf", "application/x-pdf", "octet-stream"]
    )

    if not (is_pdf_ext or is_pdf_mime):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted."
        )

    try:
        content = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file '%s': %s", filename, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read uploaded file."
        ) from exc

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    try:
        result = extract_text_from_pdf(content, filename=filename)
        return PDFExtractResponse(**result)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        ) from val_err
    except Exception as exc:
        logger.error("Unexpected error during PDF extraction for '%s': %s", filename, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract text from PDF document."
        ) from exc
