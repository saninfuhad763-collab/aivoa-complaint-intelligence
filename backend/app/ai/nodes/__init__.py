from typing import Dict, Any, List
from app.ai.state import ComplaintState
from app.core.config import settings
from app.ai.groq_service import extract_complaint_with_groq

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
    Step 2: Structured complaint extraction.
    Uses Groq / gemma2-9b-it model if GROQ_API_KEY is configured,
    otherwise falls back cleanly to deterministic extraction placeholder.
    """
    input_text = state.get("input_text", "") or ""
    source_type = state.get("source_type", "text") or "text"
    existing_data = state.get("complaint_data") or {}

    # If GROQ_API_KEY is configured and we have input text, run real Groq extraction
    if settings.GROQ_API_KEY and input_text:
        ai_res = extract_complaint_with_groq(input_text=input_text, source_type=source_type)
        extracted = ai_res.get("extracted_data", {})

        # Merge with existing data if pre-filled fields exist
        merged_data = {
            "complaint_number": existing_data.get("complaint_number") or extracted.get("complaint_number", ""),
            "complaint_source": existing_data.get("complaint_source") or extracted.get("complaint_source") or source_type,
            "customer_name": existing_data.get("customer_name") or extracted.get("customer_name"),
            "product_name": existing_data.get("product_name") or extracted.get("product_name"),
            "product_strength": existing_data.get("product_strength") or extracted.get("product_strength"),
            "batch_number": existing_data.get("batch_number") or extracted.get("batch_number"),
            "manufacturing_date": existing_data.get("manufacturing_date") or extracted.get("manufacturing_date"),
            "expiry_date": existing_data.get("expiry_date") or extracted.get("expiry_date"),
            "affected_quantity": existing_data.get("affected_quantity") if existing_data.get("affected_quantity") is not None else extracted.get("affected_quantity"),
            "affected_quantity_unit": existing_data.get("affected_quantity_unit") or extracted.get("affected_quantity_unit"),
            "complaint_type": existing_data.get("complaint_type") or extracted.get("complaint_type"),
            "complaint_date": existing_data.get("complaint_date") or extracted.get("complaint_date"),
            "complaint_description": existing_data.get("complaint_description") or extracted.get("complaint_description") or input_text,
            "status": existing_data.get("status", "NEW"),
        }

        res_update: Dict[str, Any] = {"complaint_data": merged_data}
        if "confidence" in ai_res:
            res_update["confidence"] = ai_res["confidence"]
        if ai_res.get("error"):
            res_update["validation_errors"] = [ai_res["error"]]
        return res_update

    # Fallback deterministic extraction contract placeholder (when no GROQ_API_KEY)
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
    missing_fields: List[str] = list(state.get("missing_fields", []) or [])
    validation_errors: List[str] = list(state.get("validation_errors", []) or [])

    for field in CORE_COMPLAINT_FIELDS:
        val = complaint_data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            if field not in missing_fields:
                missing_fields.append(field)

    if missing_fields and not any("Missing required complaint details" in e for e in validation_errors):
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


import re as _re


def _keyword_present(text: str, keyword: str) -> bool:
    """
    Return True only when the keyword appears in a clause/sentence that does NOT
    contain a negation word (no, not, without, none, never) BEFORE the keyword.

    Uses sentence-level detection (split on . ! ?) instead of a fixed-width
    character window, so comma-separated negation lists like:
        "no contamination, adverse event, potency issue, or safety concern"
    correctly negate ALL items regardless of their position in the list.
    """
    _negation = _re.compile(
        r'\b(no|not|none|without|never|non|no sign of|no evidence of|'
        r'no report of|no indication of)\b',
        _re.IGNORECASE
    )
    # Split text into sentences/clauses on sentence terminators
    clauses = _re.split(r'[.!?]', text)
    for clause in clauses:
        if keyword not in clause:
            continue
        # Find each occurrence of the keyword inside this clause
        for m in _re.finditer(_re.escape(keyword), clause):
            before_keyword = clause[:m.start()]
            if _negation.search(before_keyword):
                continue  # keyword is negated in this clause — skip
            return True   # at least one non-negated occurrence found
    return False


def assess_risk(state: ComplaintState) -> Dict[str, Any]:
    """
    Step 5: Perform AI risk assessment using a deterministic, complaint-sensitive
    pharmaceutical risk decision matrix based on complaint substance.

    Uses negation-aware keyword matching to avoid false positives when safety
    terms are explicitly negated (e.g., "no contamination", "no adverse event").
    """
    complaint_data = state.get("complaint_data", {}) or {}
    input_text = (state.get("input_text") or "").lower()
    description = (complaint_data.get("complaint_description") or "").lower()
    complaint_type = (complaint_data.get("complaint_type") or "").lower()
    qty = complaint_data.get("affected_quantity")
    missing_fields = state.get("missing_fields", []) or []

    combined_text = f"{input_text} {description} {complaint_type}".strip()

    # 1. Critical severity signals (contamination, safety hazard, toxic, severe adverse event)
    critical_keywords = [
        "contamination", "contaminate", "foreign matter", "particle", "glass",
        "adverse event", "anaphylaxis", "hospitalized", "hospitalisation",
        "death", "fatal", "poison", "toxic", "organ failure", "expired product"
    ]
    is_critical = any(_keyword_present(combined_text, kw) for kw in critical_keywords)

    # 2. High severity signals (dosage, labeling, potency, large affected quantity)
    high_keywords = [
        "mislabeling", "mislabel", "mislabelled", "dosage error", "potency",
        "efficacy", "strength failure", "subpotent", "superpotent"
    ]
    is_high = (
        any(_keyword_present(combined_text, kw) for kw in high_keywords)
        or (qty is not None and isinstance(qty, (int, float)) and qty >= 100)
    )

    # 3. Medium severity signals (packaging, discoloration, odor, physical defect)
    medium_keywords = [
        "packaging", "seal", "discoloration", "discoloured", "odor", "odour",
        "damage", "broken", "leak", "leaking", "crack", "cracked", "chip", "chipped"
    ]
    is_medium = (
        any(_keyword_present(combined_text, kw) for kw in medium_keywords)
        or len(missing_fields) >= 3
    )

    # 4. Decision matrix evaluation
    if is_critical:
        severity = "Critical"
        risk_level = "Critical"
        assessment = "Critical safety event detected: potential product contamination, foreign matter, or high-impact adverse patient safety risk."
    elif is_high:
        severity = "High"
        risk_level = "Major"
        assessment = "High-risk quality defect identified affecting dosage integrity, labeling compliance, or product potency/efficacy."
    elif is_medium:
        severity = "Medium"
        risk_level = "Major" if len(missing_fields) >= 3 else "Minor"
        assessment = "Moderate quality defect identified requiring standard batch record verification and warehouse containment."
    else:
        severity = "Low"
        risk_level = "Minor"
        assessment = "Standard routine complaint intake processed with low direct risk impact."

    # 5. Confidence calculation
    # Missing information reduces confidence/readiness, NOT risk severity.
    base_confidence = state.get("confidence")
    if base_confidence is None or not isinstance(base_confidence, (int, float)):
        base_confidence = 0.85

    penalty = len(missing_fields) * 0.10
    final_confidence = max(0.30, round(base_confidence - penalty, 2))

    return {
        "severity": severity,
        "risk_level": risk_level,
        "initial_risk_assessment": assessment,
        "confidence": final_confidence,
    }


def recommend_action(state: ComplaintState) -> Dict[str, Any]:
    """
    Step 6: Recommend next QA workflow action based on evaluated risk severity.
    """
    severity = state.get("severity", "Low")

    if severity == "Critical":
        action = "Initiate immediate QA investigation, place lot on immediate quality hold, quarantine inventory, and notify Quality Director & Regulatory Affairs."
    elif severity == "High":
        action = "Initiate QA investigation, place affected batch on quality hold, notify Quality Manager, and perform retain sample testing."
    elif severity == "Medium":
        action = "Verify batch manufacturing records, inspect warehouse stock, and log standard QA investigation."
    else:
        action = "Log complaint, verify batch records, and await routine QA review."

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
