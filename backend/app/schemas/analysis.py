"""
Analysis request/response schemas for POST /api/complaints/analyze.

These schemas sit between FastAPI and the LangGraph workflow.
They expose the final ComplaintState result without leaking internal
LangGraph/Groq implementation details.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class ComplaintAnalysisRequest(BaseModel):
    """
    Payload accepted by POST /api/complaints/analyze.

    input_text   — raw complaint text from the user or extracted from PDF.
    source_type  — origin channel; must be compatible with ComplaintState.source_type
                   and the existing complaint_source allowed values.
    """
    input_text: str = Field(..., description="Raw complaint text to analyse")
    source_type: str = Field(
        default="text",
        description="Origin channel: text | email | web_form | pdf_upload | phone | letter | other",
    )

    @field_validator("input_text")
    @classmethod
    def input_text_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("input_text must not be empty or whitespace-only")
        return v.strip()

    @field_validator("source_type")
    @classmethod
    def source_type_normalise(cls, v: str) -> str:
        allowed = {"text", "email", "web_form", "pdf_upload", "phone", "letter", "other"}
        normalised = v.strip().lower() if v else "text"
        if normalised not in allowed:
            # Accept without hard-failing — downstream nodes will use "other" semantics.
            return "other"
        return normalised


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class ComplaintAnalysisResponse(BaseModel):
    """
    Structured result returned by POST /api/complaints/analyze.

    Maps the final ComplaintState produced by finalize_result onto a clean
    API contract the frontend can consume directly for form population and
    risk assessment display.

    complaint_data       — extracted complaint fields (keys mirror ComplaintCreate).
    missing_fields       — fields the AI could not find in the input text.
    validation_errors    — soft warnings produced by validate_complaint node.
    complaint_category   — category assigned by classify_complaint node.
    severity             — Low | Medium | High | Critical (assess_risk node).
    risk_level           — Minor | Major | Critical (assess_risk node).
    initial_risk_assessment — human-readable risk narrative.
    suggested_next_action   — recommended QA workflow step.
    confidence           — AI extraction confidence score [0.0 – 1.0].
    messages             — conversation messages threaded through the graph.
    document_metadata    — any document/PDF metadata if present.
    """

    complaint_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted complaint fields ready to populate the complaint form",
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Core fields absent from the input text",
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="Soft validation warnings from the workflow",
    )
    complaint_category: Optional[str] = Field(
        None,
        description="Complaint category assigned by the classify_complaint node",
    )
    severity: Optional[str] = Field(None, description="Assessed severity level")
    risk_level: Optional[str] = Field(None, description="Assessed risk level")
    initial_risk_assessment: Optional[str] = Field(
        None, description="Narrative risk assessment from assess_risk node"
    )
    suggested_next_action: Optional[str] = Field(
        None, description="Recommended next QA action from recommend_action node"
    )
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="AI extraction confidence [0.0 – 1.0]"
    )
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Conversation messages threaded through the LangGraph workflow",
    )
    document_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Document/PDF metadata when source_type is pdf_upload",
    )
