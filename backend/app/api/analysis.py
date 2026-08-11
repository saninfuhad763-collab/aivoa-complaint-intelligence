"""
POST /api/complaints/analyze

Exposes the existing LangGraph complaint workflow through a single FastAPI route.

Architecture:
    FastAPI route
        → complaint_graph.invoke(initial_state)
            → normalize_input
            → extract_complaint  (Groq llama-3.3-70b-versatile)
            → validate_complaint
            → classify_complaint
            → assess_risk
            → recommend_action
            → finalize_result
        → ComplaintAnalysisResponse

The route does NOT call Groq directly and does NOT write to the database.
Persisting a reviewed complaint is the responsibility of POST /api/complaints.
"""
import logging
from fastapi import APIRouter, HTTPException, status

from app.ai import complaint_graph
from app.schemas.analysis import ComplaintAnalysisRequest, ComplaintAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/complaints", tags=["AI Analysis"])


@router.post(
    "/analyze",
    response_model=ComplaintAnalysisResponse,
    summary="Analyse a complaint with LangGraph + Groq",
    description=(
        "Accepts raw complaint text, runs it through the full LangGraph workflow "
        "(extract → validate → classify → assess_risk → recommend_action), "
        "and returns a structured analysis result. "
        "This endpoint is stateless — it does not persist anything to the database."
    ),
)
def analyze_complaint(request: ComplaintAnalysisRequest) -> ComplaintAnalysisResponse:
    """
    Run the LangGraph complaint analysis pipeline on the supplied text.

    The graph handles:
    - AI-powered field extraction via Groq (when GROQ_API_KEY is set)
    - Deterministic fallback when GROQ_API_KEY is absent
    - Structured validation of extracted fields
    - Risk assessment and action recommendation

    Returns a ComplaintAnalysisResponse suitable for populating the
    frontend complaint form and risk assessment panel.
    """
    initial_state = {
        "input_text": request.input_text,
        "source_type": request.source_type,
        "complaint_data": {},
        "missing_fields": [],
        "validation_errors": [],
        "messages": [],
    }

    try:
        result = complaint_graph.invoke(initial_state)
    except Exception as exc:
        # Log the real error server-side for debugging.
        # Never surface stack traces, API keys, or provider internals to the client.
        logger.error("LangGraph analysis pipeline failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI analysis pipeline encountered an unexpected error. Please try again.",
        ) from exc

    # Map final ComplaintState onto the clean API response.
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
        document_metadata=result.get("document_metadata"),
    )
