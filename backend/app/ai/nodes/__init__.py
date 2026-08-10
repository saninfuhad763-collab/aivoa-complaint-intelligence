from typing import Dict, Any, List
from app.ai.state import ComplaintState

# List of key complaint fields used for completeness validation
CORE_COMPLAINT_FIELDS = [
    "customer_name",
    "product_name",
    "batch_number",
    "complaint_type",
    "complaint_description",
]


def normalize_input(state: ComplaintState) -> Dict[str, Any]:
    """
    Step 1: Normalize incoming text/source information.
    Prepares raw user input for downstream processing.
    """
    raw_text = state.get("input_text", "") or ""
    normalized_text = raw_text.strip()
    source_type = state.get("source_type", "text") or "text"

    existing_messages = state.get("messages", []) or []
    initial_message = {
        "role": "user",
        "content": normalized_text,
    }

    return {
        "input_text": normalized_text,
        "source_type": source_type,
        "messages": existing_messages + [initial_message] if not existing_messages else existing_messages,
    }


def extract_complaint(state: ComplaintState) -> Dict[str, Any]:
    """
    Step 2: Establish the structured extraction contract.
    For foundation phase: Deterministic placeholder logic (no LLM/Groq call).
    """
    input_text = state.get("input_text", "")
    existing_data = state.get("complaint_data") or {}

    # Simple deterministic fallback extraction contract placeholder
    extracted = {
        "complaint_number": existing_data.get("complaint_number", ""),
        "complaint_source": state.get("source_type", "text"),
        "customer_name": existing_data.get("customer_name"),
        "product_name": existing_data.get("product_name"),
        "product_strength": existing_data.get("product_strength"),
        "batch_number": existing_data.get("batch_number"),
        "manufacturing_date": existing_data.get("manufacturing_date"),
        "expiry_date": existing_data.get("expiry_date"),
        "affected_quantity": existing_data.get("affected_quantity"),
        "affected_quantity_unit": existing_data.get("affected_quantity_unit"),
        "complaint_type": existing_data.get("complaint_type"),
        "complaint_date": existing_data.get("complaint_date"),
        "complaint_description": existing_data.get("complaint_description") or input_text,
        "status": existing_data.get("status", "NEW"),
    }

    return {"complaint_data": extracted}


def validate_complaint(state: ComplaintState) -> Dict[str, Any]:
    """
    Step 3: Inspect available complaint data, identify missing fields,
    and accumulate validation warnings/errors without inventing data.
    """
    complaint_data = state.get("complaint_data", {}) or {}
    missing_fields: List[str] = []
    validation_errors: List[str] = []

    for field in CORE_COMPLAINT_FIELDS:
        val = complaint_data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing_fields.append(field)

    if missing_fields:
        validation_errors.append(
            f"Missing required complaint details: {', '.join(missing_fields)}"
        )

    # Validate quantity if provided
    qty = complaint_data.get("affected_quantity")
    if qty is not None and isinstance(qty, (int, float)) and qty < 0:
        validation_errors.append("affected_quantity must be non-negative")

    return {
        "missing_fields": missing_fields,
        "validation_errors": validation_errors,
    }


def classify_complaint(state: ComplaintState) -> Dict[str, Any]:
    """
    Step 4: Categorize/classify the complaint based on extracted data.
    Deterministic placeholder logic for foundation phase.
    """
    complaint_data = state.get("complaint_data", {}) or {}
    category = complaint_data.get("complaint_type") or "Quality Defect"

    return {
        "complaint_category": category,
    }


def assess_risk(state: ComplaintState) -> Dict[str, Any]:
    """
    Step 5: Perform AI risk assessment.
    Deterministic baseline logic for foundation phase.
    """
    validation_errors = state.get("validation_errors", [])
    missing_fields = state.get("missing_fields", [])

    if len(missing_fields) >= 3:
        severity = "Medium"
        risk_level = "Minor"
        assessment = "Preliminary intake: Multiple fields missing. Further investigation required."
        confidence = 0.5
    else:
        severity = "Low"
        risk_level = "Minor"
        assessment = "Standard complaint intake processed."
        confidence = 0.8

    return {
        "severity": severity,
        "risk_level": risk_level,
        "initial_risk_assessment": assessment,
        "confidence": confidence,
    }


def recommend_action(state: ComplaintState) -> Dict[str, Any]:
    """
    Step 6: Recommend next QA workflow action based on risk assessment.
    """
    severity = state.get("severity", "Low")
    
    if severity in ("High", "Critical"):
        action = "Initiate immediate QA investigation, log CAPA workflow, and notify Quality Manager."
    else:
        action = "Log complaint, verify batch records, and await standard QA review."

    return {
        "suggested_next_action": action,
    }


def finalize_result(state: ComplaintState) -> Dict[str, Any]:
    """
    Step 7: Finalize state into clean structured format ready for API consumption.
    """
    complaint_data = dict(state.get("complaint_data", {}))
    
    # Enrich complaint_data with assessed risk fields if not present
    complaint_data["severity"] = complaint_data.get("severity") or state.get("severity")
    complaint_data["risk_level"] = complaint_data.get("risk_level") or state.get("risk_level")
    complaint_data["initial_risk_assessment"] = complaint_data.get("initial_risk_assessment") or state.get("initial_risk_assessment")
    complaint_data["suggested_next_action"] = complaint_data.get("suggested_next_action") or state.get("suggested_next_action")
    complaint_data["ai_confidence"] = complaint_data.get("ai_confidence") or state.get("confidence")

    return {
        "complaint_data": complaint_data,
    }
