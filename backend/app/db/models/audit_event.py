from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True, index=True)
    
    event_type = Column(String, nullable=False, index=True)  # COMPLAINT_CREATED, RISK_ASSESSED, FIELD_UPDATED, etc.
    description = Column(Text, nullable=True)
    event_metadata = Column("metadata", JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    complaint = relationship("Complaint", back_populates="audit_events")

    def __repr__(self):
        return f"<AuditEvent(id={self.id}, event_type='{self.event_type}', complaint_id={self.complaint_id})>"
