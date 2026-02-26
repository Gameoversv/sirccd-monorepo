"""
Modelo de Brigada
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey, Float
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from db.base import Base


# Tabla de asociación para relación many-to-many entre brigadas y usuarios
brigade_members = Table(
    'brigade_members',
    Base.metadata,
    Column('brigade_id', Integer, ForeignKey('brigades.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('joined_at', DateTime, default=datetime.utcnow, nullable=False),
)


class Brigade(Base):
    """
    Modelo de Brigada
    
    Representa un equipo de trabajo responsable de reparar incidentes viales.
    """
    __tablename__ = "brigades"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Información básica
    name = Column(String(255), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)  # Ejemplo: BRG-001
    
    # Contacto
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)  # Disponible para asignaciones
    
    # Ubicación actual (opcional, para tracking en tiempo real)
    current_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    last_location_update = Column(DateTime, nullable=True)
    
    # Capacidad
    max_concurrent_incidents = Column(Integer, default=5, nullable=False)
    
    # Estadísticas
    total_incidents_resolved = Column(Integer, default=0, nullable=False)
    avg_resolution_hours = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    members = relationship("User", secondary=brigade_members, back_populates="brigade_assignments")
    incidents = relationship("Incident", back_populates="assigned_brigade")
    
    def __repr__(self):
        return f"<Brigade {self.code} - {self.name}>"
