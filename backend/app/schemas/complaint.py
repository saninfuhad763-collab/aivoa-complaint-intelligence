from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ---------------------------------------------------------------------------
# Allowed value sets — keeps validation logic explicit and easy to explain
# ---------------------------------------------------------------------------

ALLOWED_SEVERITY = {"Low", "Medium", "High", "Critical"}
ALLOWED_RISK_LEVEL = {"Minor", "Major", "Critical"}
ALLOWED_STATUS = {"NEW", "IN_REVIEW", "UNDER_INVESTIGATION", "CLOSED", "REJECTED"}
ALLOWED_COMPLAINT_SOURCE = {"email", "web_form", "pdf_upload", "phone", "letter", "other"}


# ---------------------------------------------------------------------------
# ComplaintCreate — fields a user/copilot submits when logging a new complaint
# ---------------------------------------------------------------------------

class ComplaintCreate(BaseModel):
    """Data required to create a new complaint record."""

    complaint_number: str = Field(..., min_length=1, description="Unique complaint identifier")

    complaint_source: Optional[str] = Field(None, description="Origin channel of the complaint")
    customer_name: Optional[str] = Field(None, description="Name of the reporting customer")
    product_name: Optional[str] = Field(None, description="Name of the implicated product")
    product_strength: Optional[str] = Field(None, description="Strength/dosage form of the product")
    batch_number: Optional[str] = Field(None, description="Batch/lot number")
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    affected_quantity: Optional[float] = Field(None, ge=0, description="Must be non-negative")
    affected_quantity_unit: Optional[str] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[date] = None
    complaint_description: Optional[str] = Field(None, description="Full description of the complaint")

    severity: Optional[str] = None
    risk_level: Optional[str] = None
    initial_risk_assessment: Optional[str] = None
    suggested_next_action: Optional[str] = None
    ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score between 0 and 1")

    status: str = Field(default="NEW", description="Complaint workflow status")

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("complaint_number", "customer_name", "product_name",
                     "batch_number", "complaint_type", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v

    @field_validator("severity", mode="before")
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_SEVERITY:
            raise ValueError(f"severity must be one of {ALLOWED_SEVERITY}")
        return v

    @field_validator("risk_level", mode="before")
    @classmethod
    def validate_risk_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_RISK_LEVEL:
            raise ValueError(f"risk_level must be one of {ALLOWED_RISK_LEVEL}")
        return v

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_STATUS:
            raise ValueError(f"status must be one of {ALLOWED_STATUS}")
        return v

    @field_validator("complaint_source", mode="before")
    @classmethod
    def validate_complaint_source(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_COMPLAINT_SOURCE:
            raise ValueError(f"complaint_source must be one of {ALLOWED_COMPLAINT_SOURCE}")
        return v


# ---------------------------------------------------------------------------
# ComplaintUpdate — all fields optional, used for partial PATCH-style updates
# ---------------------------------------------------------------------------

class ComplaintUpdate(BaseModel):
    """Partial update schema — all fields are optional."""

    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    affected_quantity: Optional[float] = Field(None, ge=0)
    affected_quantity_unit: Optional[str] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[date] = None
    complaint_description: Optional[str] = None

    severity: Optional[str] = None
    risk_level: Optional[str] = None
    initial_risk_assessment: Optional[str] = None
    suggested_next_action: Optional[str] = None
    ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    status: Optional[str] = None

    @field_validator("severity", mode="before")
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_SEVERITY:
            raise ValueError(f"severity must be one of {ALLOWED_SEVERITY}")
        return v

    @field_validator("risk_level", mode="before")
    @classmethod
    def validate_risk_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_RISK_LEVEL:
            raise ValueError(f"risk_level must be one of {ALLOWED_RISK_LEVEL}")
        return v

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_STATUS:
            raise ValueError(f"status must be one of {ALLOWED_STATUS}")
        return v


# ---------------------------------------------------------------------------
# ComplaintResponse — full representation returned from the API
# ---------------------------------------------------------------------------

class ComplaintResponse(BaseModel):
    """Complete complaint schema returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_number: str

    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    affected_quantity: Optional[float] = None
    affected_quantity_unit: Optional[str] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[date] = None
    complaint_description: Optional[str] = None

    severity: Optional[str] = None
    risk_level: Optional[str] = None
    initial_risk_assessment: Optional[str] = None
    suggested_next_action: Optional[str] = None
    ai_confidence: Optional[float] = None

    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# ComplaintListResponse — minimal schema for history/listing views
# ---------------------------------------------------------------------------

class ComplaintListItem(BaseModel):
    """Minimal complaint summary for list/history views."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_number: str
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    complaint_type: Optional[str] = None
    severity: Optional[str] = None
    risk_level: Optional[str] = None
    status: str
    created_at: datetime


class ComplaintListResponse(BaseModel):
    """Paginated list of complaints."""

    items: List[ComplaintListItem]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Duplicate Detection Schemas
# ---------------------------------------------------------------------------

class DuplicateCheckRequest(BaseModel):
    """Payload for checking potential duplicate complaints."""

    product_name: Optional[str] = Field(None, description="Name of the product")
    batch_number: Optional[str] = Field(None, description="Batch/lot number")
    customer_name: Optional[str] = Field(None, description="Customer name")
    exclude_id: Optional[int] = Field(None, description="Complaint ID to exclude (used when editing)")

    @field_validator("product_name", "batch_number", "customer_name", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v


class DuplicateCandidate(BaseModel):
    """Detailed metadata for a candidate duplicate complaint."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_number: str
    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    customer_name: Optional[str] = None
    complaint_type: Optional[str] = None
    status: str
    created_at: datetime
    match_reason: str = Field(..., description="Human-readable explanation of why this complaint matched")
    match_confidence: str = Field(..., description="'high' or 'medium'")


class DuplicateCheckResponse(BaseModel):
    """Response containing matching duplicate candidates."""

    has_duplicates: bool
    duplicates: List[DuplicateCandidate]
