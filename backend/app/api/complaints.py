from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.db.models.complaint import Complaint
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintResponse,
    ComplaintListResponse,
    ComplaintListItem,
)

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new customer complaint.
    """
    # Check if complaint_number already exists
    existing = db.query(Complaint).filter(Complaint.complaint_number == payload.complaint_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Complaint with complaint_number '{payload.complaint_number}' already exists."
        )

    complaint_data = payload.model_dump()
    db_complaint = Complaint(**complaint_data)
    
    try:
        db.add(db_complaint)
        db.commit()
        db.refresh(db_complaint)
        return db_complaint
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error while creating complaint."
        )


@router.get("", response_model=ComplaintListResponse)
def list_complaints(
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    status: Optional[str] = Query(None, description="Filter by complaint status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    product_name: Optional[str] = Query(None, description="Filter by product name"),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of complaints with optional status, severity, and product_name filtering.
    """
    query = db.query(Complaint)

    if status:
        query = query.filter(Complaint.status == status)
    if severity:
        query = query.filter(Complaint.severity == severity)
    if product_name:
        query = query.filter(Complaint.product_name.ilike(f"%{product_name}%"))

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(Complaint.created_at.desc()).offset(offset).limit(page_size).all()

    return ComplaintListResponse(
        items=[ComplaintListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific complaint by ID.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID {complaint_id} not found."
        )
    return complaint


@router.patch("/{complaint_id}", response_model=ComplaintResponse)
def update_complaint(
    complaint_id: int,
    payload: ComplaintUpdate,
    db: Session = Depends(get_db)
):
    """
    Perform a partial update on a complaint. Only supplied fields are updated.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID {complaint_id} not found."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(complaint, field, value)

    try:
        db.commit()
        db.refresh(complaint)
        return complaint
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error during complaint update."
        )


@router.delete("/{complaint_id}", status_code=status.HTTP_200_OK)
def delete_complaint(
    complaint_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a complaint by ID. Cascades deletion to associated documents/messages/audit events.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID {complaint_id} not found."
        )

    db.delete(complaint)
    db.commit()
    return {
        "message": "Complaint deleted successfully",
        "id": complaint_id
    }
