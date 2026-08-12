"""
Duplicate Complaint Detection Service

Implements rule-based, deterministic duplicate matching against existing PostgreSQL records.

Matching Rules:
1. HIGH CONFIDENCE:
   Matching product_name AND batch_number (case-insensitive, whitespace-trimmed).
2. MEDIUM CONFIDENCE:
   Matching product_name AND customer_name (case-insensitive, whitespace-trimmed), when batch_number differs/absent.

Self-Exclusion:
   If `exclude_id` is specified (e.g. during an update/edit operation), the query excludes `id == exclude_id`.

Result Limit:
   Capped at 5 candidates maximum.
"""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models.complaint import Complaint
from app.schemas.complaint import DuplicateCheckRequest, DuplicateCandidate


def find_duplicate_complaints(
    db: Session,
    request: DuplicateCheckRequest,
    limit: int = 5
) -> List[DuplicateCandidate]:
    """
    Search PostgreSQL for candidate duplicate complaints based on normalized string matching.
    """
    product = (request.product_name or "").strip()
    batch = (request.batch_number or "").strip()
    customer = (request.customer_name or "").strip()
    exclude_id = request.exclude_id

    # If product_name is empty, product-based duplicate detection cannot run.
    if not product:
        return []

    duplicates: List[DuplicateCandidate] = []
    seen_ids = set()

    # Rule 1: High confidence — matching product_name AND batch_number
    if batch:
        high_query = db.query(Complaint).filter(
            func.lower(func.trim(Complaint.product_name)) == product.lower(),
            func.lower(func.trim(Complaint.batch_number)) == batch.lower(),
        )
        if exclude_id is not None:
            high_query = high_query.filter(Complaint.id != exclude_id)

        high_matches = high_query.order_by(Complaint.created_at.desc()).limit(limit).all()

        for comp in high_matches:
            if comp.id not in seen_ids:
                seen_ids.add(comp.id)
                duplicates.append(
                    DuplicateCandidate(
                        id=comp.id,
                        complaint_number=comp.complaint_number,
                        product_name=comp.product_name,
                        batch_number=comp.batch_number,
                        customer_name=comp.customer_name,
                        complaint_type=comp.complaint_type,
                        status=comp.status,
                        created_at=comp.created_at,
                        match_reason="Same product name and batch/lot number.",
                        match_confidence="high",
                    )
                )

    # Rule 2: Medium confidence — matching product_name AND customer_name
    if customer and len(duplicates) < limit:
        med_query = db.query(Complaint).filter(
            func.lower(func.trim(Complaint.product_name)) == product.lower(),
            func.lower(func.trim(Complaint.customer_name)) == customer.lower(),
        )
        if exclude_id is not None:
            med_query = med_query.filter(Complaint.id != exclude_id)

        med_matches = med_query.order_by(Complaint.created_at.desc()).limit(limit * 2).all()

        for comp in med_matches:
            if comp.id not in seen_ids:
                seen_ids.add(comp.id)
                duplicates.append(
                    DuplicateCandidate(
                        id=comp.id,
                        complaint_number=comp.complaint_number,
                        product_name=comp.product_name,
                        batch_number=comp.batch_number,
                        customer_name=comp.customer_name,
                        complaint_type=comp.complaint_type,
                        status=comp.status,
                        created_at=comp.created_at,
                        match_reason="Same product name reported by the same customer.",
                        match_confidence="medium",
                    )
                )
                if len(duplicates) >= limit:
                    break

    return duplicates[:limit]
