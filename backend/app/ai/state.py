from typing import List, Optional, Any, Dict
from typing_extensions import TypedDict


class ComplaintState(TypedDict, total=False):
    """
    Typed state schema for the AIVOA Complaint Intelligence LangGraph workflow.
    Tracks raw input, extracted fields, validation flags, risk scores, and conversation messages.
    """
    input_text: str
    source_type: str  # e.g., "email", "web_form", "pdf_upload", "text"
    complaint_data: Dict[str, Any]
    missing_fields: List[str]
    validation_errors: List[str]
    complaint_category: Optional[str]
    severity: Optional[str]  # Low, Medium, High, Critical
    risk_level: Optional[str]  # Minor, Major, Critical
    initial_risk_assessment: Optional[str]
    suggested_next_action: Optional[str]
    confidence: Optional[float]
    messages: List[Dict[str, Any]]
    document_metadata: Optional[Dict[str, Any]]
