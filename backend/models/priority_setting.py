"""
Modelo de configuracion de prioridad editable por administradores.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from db.base import Base


class PrioritySetting(Base):
    __tablename__ = "priority_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Pesos del score de prioridad
    weight_severity = Column(Float, nullable=False, default=0.35)
    weight_age = Column(Float, nullable=False, default=0.20)
    weight_damage_type = Column(Float, nullable=False, default=0.15)
    weight_location = Column(Float, nullable=False, default=0.20)
    weight_duplicates = Column(Float, nullable=False, default=0.10)

    # Parametros de radio y ventanas de tiempo
    poi_radius_meters = Column(Integer, nullable=False, default=500)
    duplicate_radius_meters = Column(Integer, nullable=False, default=100)
    duplicate_time_window_days = Column(Integer, nullable=False, default=30)

    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    updated_by_user = relationship("User", foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return (
            f"<PrioritySetting id={self.id} "
            f"weights=({self.weight_severity}, {self.weight_age}, {self.weight_damage_type}, "
            f"{self.weight_location}, {self.weight_duplicates})>"
        )

