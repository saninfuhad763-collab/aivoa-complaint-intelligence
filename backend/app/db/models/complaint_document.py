from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ComplaintDocument(Base):
    __tablename__ = "complaint_documents"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    extracted_text = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    complaint = relationship("Complaint", back_populates="documents")

    def __repr__(self):
        return f"<ComplaintDocument(id={self.id}, filename='{self.filename}', complaint_id={self.complaint_id})>"
