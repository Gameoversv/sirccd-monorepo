"""
Modelo de configuración de SLAs por nivel de prioridad (P-06)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from db.base import Base


class SLAConfig(Base):
    __tablename__ = "sla_configs"

    id = Column(Integer, primary_key=True, index=True)

    # Horas máximas por nivel de prioridad
    sla_hours_baja = Column(Float, nullable=False, default=72.0)
    sla_hours_media = Column(Float, nullable=False, default=48.0)
    sla_hours_alta = Column(Float, nullable=False, default=24.0)
    sla_hours_critica = Column(Float, nullable=False, default=8.0)

    # Porcentaje del SLA consumido a partir del cual se emite advertencia (0-1)
    warning_threshold_pct = Column(Float, nullable=False, default=0.8)

    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    updated_by_user = relationship("User", foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return (
            f"<SLAConfig id={self.id} "
            f"baja={self.sla_hours_baja}h media={self.sla_hours_media}h "
            f"alta={self.sla_hours_alta}h critica={self.sla_hours_critica}h>"
        )
