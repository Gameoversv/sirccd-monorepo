"""
Models module - Modelos de base de datos (SQLAlchemy)

Importa todos los modelos para facilitar el uso de Alembic.
"""

from db.base import Base

# Importar todos los modelos
from .user import User, UserRole
from .report import Report, ReportStatus, DamageType, SeverityLevel
from .incident import Incident, IncidentStatus, PriorityLevel
from .brigade import Brigade, brigade_members
from .poi import POI, POICategory
from .metric import Metric

__all__ = [
    "Base",
    # User
    "User",
    "UserRole",
    # Report
    "Report",
    "ReportStatus",
    "DamageType",
    "SeverityLevel",
    # Incident
    "Incident",
    "IncidentStatus",
    "PriorityLevel",
    # Brigade
    "Brigade",
    "brigade_members",
    # POI
    "POI",
    "POICategory",
    # Metric
    "Metric",
]
