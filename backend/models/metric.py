"""
Modelo de Métrica
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text

from db.base import Base
from sqlalchemy.orm import relationship


class Metric(Base):
    """
    Modelo de Métrica
    
    Almacena métricas y estadísticas sobre incidentes y operaciones.
    """
    __tablename__ = "metrics"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Incidente relacionado (opcional)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True, index=True)
    
    # Tipo de métrica
    metric_type = Column(String(100), nullable=False, index=True)
    # Ejemplos: 'response_time', 'resolution_time', 'detection_accuracy', 
    #           'citizen_satisfaction', 'cost_estimation', 'traffic_impact'
    
    # Valor de la métrica
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)  # 'hours', 'minutes', 'percent', 'score', 'dollars'
    
    # Contexto adicional
    category = Column(String(100), nullable=True, index=True)  # 'performance', 'quality', 'cost'
    subcategory = Column(String(100), nullable=True)
    
    # Metadatos
    metadata_json = Column(Text, nullable=True)  # JSON con información adicional
    notes = Column(Text, nullable=True)
    
    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    incident = relationship("Incident", back_populates="metrics")
    
    def __repr__(self):
        return f"<Metric {self.metric_type}: {self.value} {self.unit}>"
