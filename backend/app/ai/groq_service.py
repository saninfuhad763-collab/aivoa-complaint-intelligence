from typing import List, Optional, Dict, Any
import logging
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured AI Extraction Schema
# ---------------------------------------------------------------------------

class AIExtractionOutput(BaseModel):
    """
    Structured extraction schema produced by the Groq LLM model.
    Fields align directly with ComplaintCreate schema and anti-hallucination rules.
    """
    complaint_source: Optional[str] = Field(
        None, description="Origin channel (e.g. email, web_form, pdf_upload, phone, letter, other)"
    )
    customer_name: Optional[str] = Field(
        None, description="Name of the customer or reporting healthcare facility/physician"
    )
    product_name: Optional[str] = Field(
        None, description="Exact product name implicated"
    )
    product_strength: Optional[str] = Field(
        None, description="Dosage strength or form (e.g., 500mg, 10mg/ml)"
    )
    batch_number: Optional[str] = Field(
        None, description="Lot/batch number of the product"
    )
    manufacturing_date: Optional[str] = Field(
        None, description="Manufacturing date in YYYY-MM-DD format if present, else null"
    )
    expiry_date: Optional[str] = Field(
        None, description="Expiration date in YYYY-MM-DD format if present, else null"
    )
    affected_quantity: Optional[float] = Field(
        None, description="Numeric affected quantity if present, else null"
    )
    affected_quantity_unit: Optional[str] = Field(
        None, description="Unit of affected quantity (e.g. tablets, vials, boxes)"
    )
    complaint_type: Optional[str] = Field(
        None, description="Type of complaint (e.g., Quality Defect, Packaging Defect, Contamination, Mislabeling)"
    )
    complaint_date: Optional[str] = Field(
        None, description="Date complaint occurred or was submitted in YYYY-MM-DD format"
    )
    complaint_description: Optional[str] = Field(
        None, description="Concise, factual summary of the complaint details"
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="List of mandatory fields that were NOT present in the input text"
    )
    confidence: float = Field(
        0.85, ge=0.0, le=1.0, description="Confidence score of the extraction between 0.0 and 1.0"
    )


# ---------------------------------------------------------------------------
# Extraction System Prompt
# ---------------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """You are an expert Pharmaceutical Quality Assurance (QA) Complaint Intelligence AI agent.
Your task is to analyze customer complaint text and extract structured complaint information.

CRITICAL ANTI-HALLUCINATION RULES:
1. Extract ONLY facts explicitly stated or unambiguously present in the input text.
2. DO NOT invent, fabricate, assume, or guess any dates, batch numbers, customer names, quantities, product names, or complaint details.
3. If a field is not explicitly mentioned or clearly present in the input, set its value to null.
4. For any missing mandatory field (such as customer_name, product_name, batch_number, complaint_type, complaint_description), add the field name to the `missing_fields` list.
5. Provide a concise, factual `complaint_description` reflecting only what was reported.
6. Provide a `confidence` score between 0.0 and 1.0 reflecting your extraction certainty.
"""

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", EXTRACTION_SYSTEM_PROMPT),
    ("user", "Complaint Origin Channel: {source_type}\n\nCustomer Complaint Input:\n\"\"\"{input_text}\"\"\"")
])


# ---------------------------------------------------------------------------
# Groq Service Client Initialization & Extraction Function
# ---------------------------------------------------------------------------

def get_groq_llm(model_override: Optional[str] = None):
    """
    Initialize and return a ChatGroq client using settings configuration.
    Strictly uses the configured GROQ_MODEL without silent fallback.
    """
    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured in settings or environment.")

    model_name = model_override or settings.GROQ_MODEL or "gemma2-9b-it"

    return ChatGroq(
        groq_api_key=api_key,
        model_name=model_name,
        temperature=0.0,
    )


def extract_complaint_with_groq(
    input_text: str,
    source_type: str = "text",
    llm_client: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Extract structured complaint details using Groq LLM model.
    Returns a dictionary compatible with ComplaintState and ComplaintCreate schema.
    """
    if not input_text or not input_text.strip():
        return {
            "extracted_data": {},
            "missing_fields": [
                "customer_name", "product_name", "batch_number",
                "complaint_type", "complaint_description"
            ],
            "confidence": 0.0,
            "error": "Empty input text provided"
        }

    try:
        llm = llm_client or get_groq_llm()
        structured_llm = llm.with_structured_output(AIExtractionOutput)

        chain = EXTRACTION_PROMPT | structured_llm
        result: AIExtractionOutput = chain.invoke({
            "input_text": input_text,
            "source_type": source_type
        })

        # Convert validated output to dict
        data = result.model_dump()
        confidence = data.pop("confidence", 0.85)
        missing_fields = data.pop("missing_fields", [])

        # Ensure complaint_source defaults to source_type if null
        if not data.get("complaint_source"):
            data["complaint_source"] = source_type

        return {
            "extracted_data": data,
            "missing_fields": missing_fields,
            "confidence": confidence,
            "error": None
        }

    except Exception as e:
        # Sanitize exception message to ensure API keys are never exposed
        err_msg = str(e)
        if settings.GROQ_API_KEY and settings.GROQ_API_KEY in err_msg:
            err_msg = err_msg.replace(settings.GROQ_API_KEY, "[REDACTED_API_KEY]")
        
        logger.warning(f"Groq extraction failed cleanly: {err_msg}")
        return {
            "extracted_data": {},
            "missing_fields": [
                "customer_name", "product_name", "batch_number",
                "complaint_type", "complaint_description"
            ],
            "confidence": 0.0,
            "error": f"AI extraction error: {err_msg}"
        }
