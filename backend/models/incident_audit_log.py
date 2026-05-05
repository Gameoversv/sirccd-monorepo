from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from db.base import Base


class IncidentAuditLog(Base):
    __tablename__ = "incident_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(
        Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    event_type = Column(String(50), nullable=False, index=True)
    field_name = Column(String(100), nullable=True)
    old_value = Column(String(500), nullable=True)
    new_value = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    incident = relationship("Incident", back_populates="audit_logs")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<IncidentAuditLog {self.id} incident={self.incident_id} event={self.event_type}>"
