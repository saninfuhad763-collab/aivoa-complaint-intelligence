from datetime import date, datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas import (
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintResponse,
    ComplaintListItem,
    ComplaintListResponse,
)


# ---------------------------------------------------------------------------
# Helper: minimal valid payload for ComplaintCreate
# ---------------------------------------------------------------------------

def valid_create_payload(**overrides) -> dict:
    base = {
        "complaint_number": "COMP-2024-001",
        "complaint_source": "email",
        "customer_name": "Jane Doe",
        "product_name": "MediCure 500",
        "batch_number": "BCH-20241001",
        "affected_quantity": 5.0,
        "ai_confidence": 0.85,
        "severity": "High",
        "risk_level": "Major",
        "status": "NEW",
    }
    base.update(overrides)
    return base


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# ComplaintCreate tests
# ---------------------------------------------------------------------------

def test_complaint_create_valid():
    complaint = ComplaintCreate(**valid_create_payload())
    assert complaint.complaint_number == "COMP-2024-001"
    assert complaint.affected_quantity == 5.0
    assert complaint.ai_confidence == 0.85


def test_complaint_create_strips_whitespace():
    data = valid_create_payload(complaint_number="  COMP-001  ", customer_name="  Alice  ")
    complaint = ComplaintCreate(**data)
    assert complaint.complaint_number == "COMP-001"
    assert complaint.customer_name == "Alice"


def test_complaint_create_negative_quantity_fails():
    with pytest.raises(ValidationError) as exc_info:
        ComplaintCreate(**valid_create_payload(affected_quantity=-1.0))
    errors = exc_info.value.errors()
    assert any("affected_quantity" in str(e) for e in errors)


def test_complaint_create_confidence_above_one_fails():
    with pytest.raises(ValidationError):
        ComplaintCreate(**valid_create_payload(ai_confidence=1.5))


def test_complaint_create_confidence_below_zero_fails():
    with pytest.raises(ValidationError):
        ComplaintCreate(**valid_create_payload(ai_confidence=-0.1))


def test_complaint_create_invalid_severity_fails():
    with pytest.raises(ValidationError):
        ComplaintCreate(**valid_create_payload(severity="UNKNOWN"))


def test_complaint_create_invalid_risk_level_fails():
    with pytest.raises(ValidationError):
        ComplaintCreate(**valid_create_payload(risk_level="Extreme"))


def test_complaint_create_invalid_status_fails():
    with pytest.raises(ValidationError):
        ComplaintCreate(**valid_create_payload(status="OPEN"))


def test_complaint_create_invalid_source_fails():
    with pytest.raises(ValidationError):
        ComplaintCreate(**valid_create_payload(complaint_source="fax"))


def test_complaint_create_optional_fields_default_none():
    complaint = ComplaintCreate(complaint_number="COMP-MIN-001")
    assert complaint.customer_name is None
    assert complaint.product_name is None
    assert complaint.status == "NEW"


# ---------------------------------------------------------------------------
# ComplaintUpdate tests
# ---------------------------------------------------------------------------

def test_complaint_update_all_fields_optional():
    """ComplaintUpdate with no fields should succeed (empty partial update)."""
    update = ComplaintUpdate()
    assert update.status is None
    assert update.severity is None


def test_complaint_update_partial():
    update = ComplaintUpdate(status="IN_REVIEW", severity="Critical")
    assert update.status == "IN_REVIEW"
    assert update.severity == "Critical"
    assert update.product_name is None  # untouched fields remain None


def test_complaint_update_invalid_status_fails():
    with pytest.raises(ValidationError):
        ComplaintUpdate(status="PENDING")


def test_complaint_update_negative_quantity_fails():
    with pytest.raises(ValidationError):
        ComplaintUpdate(affected_quantity=-10.0)


def test_complaint_update_confidence_out_of_range_fails():
    with pytest.raises(ValidationError):
        ComplaintUpdate(ai_confidence=2.0)


# ---------------------------------------------------------------------------
# ComplaintResponse (from_attributes ORM serialization)
# ---------------------------------------------------------------------------

class FakeComplaintORM:
    """Simulates a SQLAlchemy Complaint ORM object."""
    id = 1
    complaint_number = "COMP-2024-001"
    complaint_source = "email"
    customer_name = "Jane Doe"
    product_name = "MediCure 500"
    product_strength = "500mg"
    batch_number = "BCH-20241001"
    manufacturing_date = date(2024, 1, 1)
    expiry_date = date(2026, 1, 1)
    affected_quantity = 5.0
    affected_quantity_unit = "tablets"
    complaint_type = "Quality"
    complaint_date = date(2024, 9, 1)
    complaint_description = "Patient reported unusual odor."
    severity = "High"
    risk_level = "Major"
    initial_risk_assessment = "Possible contamination."
    suggested_next_action = "Initiate investigation."
    ai_confidence = 0.85
    status = "NEW"
    created_at = datetime(2024, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
    updated_at = datetime(2024, 9, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_complaint_response_from_orm():
    """Verify ComplaintResponse can be deserialized from an ORM-like object."""
    response = ComplaintResponse.model_validate(FakeComplaintORM())
    assert response.id == 1
    assert response.complaint_number == "COMP-2024-001"
    assert response.severity == "High"
    assert response.ai_confidence == 0.85
    assert response.status == "NEW"


def test_complaint_response_serializes_to_dict():
    response = ComplaintResponse.model_validate(FakeComplaintORM())
    data = response.model_dump()
    assert data["id"] == 1
    assert data["product_name"] == "MediCure 500"


# ---------------------------------------------------------------------------
# ComplaintListResponse
# ---------------------------------------------------------------------------

class FakeComplaintListORM:
    id = 2
    complaint_number = "COMP-2024-002"
    customer_name = "John Smith"
    product_name = "AlphaTablet"
    complaint_type = "Packaging"
    severity = "Low"
    risk_level = "Minor"
    status = "CLOSED"
    created_at = datetime(2024, 8, 15, 10, 0, 0, tzinfo=timezone.utc)


def test_complaint_list_response():
    item = ComplaintListItem.model_validate(FakeComplaintListORM())
    response = ComplaintListResponse(
        items=[item],
        total=1,
        page=1,
        page_size=20,
    )
    assert response.total == 1
    assert response.items[0].complaint_number == "COMP-2024-002"
    assert response.items[0].status == "CLOSED"
