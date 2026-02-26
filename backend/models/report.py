"""
Modelo de Reporte
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
import enum

from db.base import Base


class ReportStatus(str, enum.Enum):
    """Estados de un reporte"""
    PENDING = "pending"           # Pendiente de revisión
    APPROVED = "approved"         # Aprobado, convertido a incidente
    REJECTED = "rejected"         # Rechazado (falso positivo, duplicado, etc.)
    PROCESSING = "processing"     # En proceso de análisis


class DamageType(str, enum.Enum):
    """Tipos de daño detectado"""
    BACHE = "bache"
    GRIETA = "grieta"


class SeverityLevel(str, enum.Enum):
    """Niveles de severidad"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class Report(Base):
    """
    Modelo de Reporte
    
    Representa un reporte ciudadano de daño vial con detección ML.
    """
    __tablename__ = "reports"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Usuario que reporta
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Ubicación geoespacial (SRID 4326 - WGS84)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    
    # Dirección (opcional, obtenida por geocoding reverso)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    
    # Detección ML
    damage_type = Column(SQLEnum(DamageType), nullable=False)
    severity = Column(SQLEnum(SeverityLevel), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    
    # Metadatos de imagen
    image_url = Column(String(500), nullable=False)  # URL en MinIO
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    
    # Bounding boxes (JSON string)
    detections_json = Column(Text, nullable=True)
    
    # Estado y descripción
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING, nullable=False, index=True)
    description = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Relaciones
    user = relationship("User", back_populates="reports")
    incident = relationship("Incident", back_populates="original_report", uselist=False)
    
    def __repr__(self):
        return f"<Report {self.id} - {self.damage_type} ({self.severity}) - {self.status}>"
