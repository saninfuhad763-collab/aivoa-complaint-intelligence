from sqlalchemy import Column, Integer, String, Float, Text, Date, DateTime, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_number = Column(String, unique=True, index=True, nullable=False)
    
    # Core complaint details
    complaint_source = Column(String, nullable=True)  # e.g., email, web_form, pdf_upload
    customer_name = Column(String, nullable=True)
    product_name = Column(String, nullable=True, index=True)
    product_strength = Column(String, nullable=True)
    batch_number = Column(String, nullable=True, index=True)
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    affected_quantity = Column(Float, nullable=True)
    affected_quantity_unit = Column(String, nullable=True)
    complaint_type = Column(String, nullable=True)
    complaint_date = Column(Date, nullable=True)
    complaint_description = Column(Text, nullable=True)
    
    # Risk assessment & AI fields
    severity = Column(String, nullable=True)  # Low, Medium, High, Critical
    risk_level = Column(String, nullable=True)  # Minor, Major, Critical
    initial_risk_assessment = Column(Text, nullable=True)
    suggested_next_action = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    
    # Status & metadata
    status = Column(String, default="NEW", index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    documents = relationship(
        "ComplaintDocument",
        back_populates="complaint",
        cascade="all, delete-orphan"
    )
    copilot_messages = relationship(
        "CopilotMessage",
        back_populates="complaint",
        cascade="all, delete-orphan"
    )
    audit_events = relationship(
        "AuditEvent",
        back_populates="complaint",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Complaint(id={self.id}, complaint_number='{self.complaint_number}', product='{self.product_name}')>"
