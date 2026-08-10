from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class CopilotMessage(Base):
    __tablename__ = "copilot_messages"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True, index=True)
    
    role = Column(String, nullable=False)  # user, assistant, system
    message = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    complaint = relationship("Complaint", back_populates="copilot_messages")

    def __repr__(self):
        return f"<CopilotMessage(id={self.id}, role='{self.role}', complaint_id={self.complaint_id})>"
