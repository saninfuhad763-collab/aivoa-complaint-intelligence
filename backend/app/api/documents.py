"""
POST /api/documents/extract-text
POST /api/documents/analyze

Endpoints for extracting text from uploaded PDF documents and connecting them
to the LangGraph AI complaint analysis pipeline.

Processing is performed in-memory; uploaded files are not stored on disk or database.
"""
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from pydantic import BaseModel, Field

from app.ai import complaint_graph
from app.services.pdf_service import extract_text_from_pdf
from app.schemas.analysis import ComplaintAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


class PDFExtractResponse(BaseModel):
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    page_count: int = Field(..., description="Number of pages in the PDF")
    text: str = Field(..., description="Extracted text from all readable pages")


async def _read_and_extract_pdf(file: UploadFile) -> dict:
    """
    Helper function to validate and extract text from an uploaded PDF.
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
        return extract_text_from_pdf(content, filename=filename)
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
    result = await _read_and_extract_pdf(file)
    return PDFExtractResponse(**result)


@router.post(
    "/analyze",
    response_model=ComplaintAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract PDF text and analyse with LangGraph + Groq",
    description="Upload a PDF file to extract text and execute AI complaint extraction and risk assessment.",
)
async def analyze_pdf_document(
    file: UploadFile = File(...)
) -> ComplaintAnalysisResponse:
    """
    Accept a PDF upload, extract text, and pass it through the LangGraph AI workflow.
    """
    pdf_info = await _read_and_extract_pdf(file)
    extracted_text = (pdf_info.get("text") or "").strip()

    if not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF file contains no extractable text."
        )

    initial_state = {
        "input_text": extracted_text,
        "source_type": "pdf_upload",
        "complaint_data": {},
        "missing_fields": [],
        "validation_errors": [],
        "messages": [],
        "document_metadata": {
            "filename": pdf_info.get("filename"),
            "page_count": pdf_info.get("page_count"),
        },
    }

    try:
        result = complaint_graph.invoke(initial_state)
    except Exception as exc:
        logger.error(
            "LangGraph analysis pipeline failed for PDF '%s': %s",
            pdf_info.get("filename"),
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI analysis pipeline encountered an unexpected error. Please try again."
        ) from exc

    return ComplaintAnalysisResponse(
        complaint_data=result.get("complaint_data") or {},
        missing_fields=result.get("missing_fields") or [],
        validation_errors=result.get("validation_errors") or [],
        complaint_category=result.get("complaint_category"),
        severity=result.get("severity"),
        risk_level=result.get("risk_level"),
        initial_risk_assessment=result.get("initial_risk_assessment"),
        suggested_next_action=result.get("suggested_next_action"),
        confidence=result.get("confidence"),
        messages=result.get("messages") or [],
        document_metadata=result.get("document_metadata") or {
            "filename": pdf_info.get("filename"),
            "page_count": pdf_info.get("page_count"),
        },
    )
