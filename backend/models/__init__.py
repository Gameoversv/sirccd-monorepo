"""
Models module - Modelos de base de datos (SQLAlchemy)

Importa todos los modelos para facilitar el uso de Alembic.
"""

from db.base import Base

# Importar todos los modelos
from .user import User, UserRole
from .report import Report, ReportStatus, DamageType, SeverityLevel
from .incident import Incident, IncidentStatus, PriorityLevel
from .incident_audit_log import IncidentAuditLog
from .poi import POI, POICategory
from .metric import Metric
from .priority_setting import PrioritySetting
from .zone import Zone

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
    # Audit log
    "IncidentAuditLog",
    # POI
    "POI",
    "POICategory",
    # Metric
    "Metric",
    # Priority settings
    "PrioritySetting",
    # Zone
    "Zone",
]
