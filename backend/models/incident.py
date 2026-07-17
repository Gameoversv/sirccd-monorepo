"""
Modelo de Incidente
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
import enum

from db.base import Base
from models.report import DamageType, SeverityLevel


class IncidentStatus(str, enum.Enum):
    """Estados de un incidente"""
    OPEN = "open"                 # Abierto
    IN_PROGRESS = "in_progress"   # En progreso de reparación
    RESOLVED = "resolved"         # Resuelto/reparado
    VERIFIED = "verified"         # Verificado por supervisor
    CLOSED = "closed"             # Cerrado


class PriorityLevel(str, enum.Enum):
    """Niveles de prioridad"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class Incident(Base):
    """
    Modelo de Incidente
    
    Representa un incidente vial confirmado que requiere reparación.
    Se crea a partir de un reporte aprobado.
    """
    __tablename__ = "incidents"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Reporte original
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, unique=True, index=True)
    
    # Usuario que reportó
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Ubicación geoespacial (heredada del reporte)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    
    # Tipo y severidad
    damage_type = Column(SQLEnum(DamageType), nullable=False, index=True)
    severity = Column(SQLEnum(SeverityLevel), nullable=False, index=True)
    
    # Priorización
    priority = Column(SQLEnum(PriorityLevel), nullable=False, index=True)
    priority_score = Column(Float, nullable=True)  # Score calculado por algoritmo
    # Desglose de factores persistido: evita recalcular (descarga de imágenes +
    # similitud visual ResNet50) en cada apertura del incidente. Se rellena al
    # recalcular la prioridad o vía backfill. Null => se computa un desglose
    # rápido (sin dedup visual) al vuelo.
    priority_breakdown = Column(JSON, nullable=True)
    
    # Estado
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False, index=True)
    
    # Tiempos
    estimated_repair_hours = Column(Float, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Verificación
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Imágenes adicionales
    before_image_url = Column(String(500), nullable=True)
    after_image_url = Column(String(500), nullable=True)
    
    # Notas y comentarios
    notes = Column(Text, nullable=True)
    
    # SLA (P-06)
    sla_deadline = Column(DateTime, nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    original_report = relationship("Report", back_populates="incident")
    reported_by_user = relationship("User", back_populates="incidents", foreign_keys=[reported_by])
    metrics = relationship("Metric", back_populates="incident", cascade="all, delete-orphan")
    audit_logs = relationship("IncidentAuditLog", back_populates="incident", cascade="all, delete-orphan", order_by="IncidentAuditLog.created_at")
    
    def __repr__(self):
        return f"<Incident {self.id} - {self.damage_type} - {self.status} - Priority: {self.priority}>"
