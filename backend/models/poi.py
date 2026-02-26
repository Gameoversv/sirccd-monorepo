"""
Modelo de POI (Point of Interest)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from geoalchemy2 import Geography
import enum

from db.base import Base


class POICategory(str, enum.Enum):
    """Categorías de POI"""
    SCHOOL = "school"
    UNIVERSITY = "university"
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    FIRE_STATION = "fire_station"
    POLICE_STATION = "police_station"
    BRIDGE = "bridge"
    BUS_STATION = "bus_station"
    COMMERCIAL = "commercial"
    OTHER = "other"


class POI(Base):
    """
    Modelo de POI (Point of Interest)
    
    Representa puntos de interés utilizados para priorización de incidentes.
    """
    __tablename__ = "pois"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Información básica
    name = Column(String(500), nullable=False)
    category = Column(SQLEnum(POICategory), nullable=False, index=True)
    
    # Ubicación geoespacial
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    
    # Dirección
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    
    # Metadatos de origen
    source = Column(String(100), nullable=True)  # 'google_places', 'osm', 'manual'
    external_id = Column(String(255), nullable=True)  # ID externo (Google Place ID, OSM ID)
    
    # Ponderación para priorización
    priority_weight = Column(Integer, default=1, nullable=False)  # 1-10
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<POI {self.name} ({self.category})>"
