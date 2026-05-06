"""
Schemas Pydantic para Incidentes (B-08)
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ============================================
# Enums
# ============================================

class IncidentStatusEnum(str, Enum):
    """Estados del ciclo de vida de un incidente"""
    OPEN = "open"                 # Nuevo/Abierto
    IN_PROGRESS = "in_progress"   # En proceso de reparación
    RESOLVED = "resolved"         # Resuelto/reparado
    VERIFIED = "verified"         # Verificado por supervisor
    CLOSED = "closed"             # Cerrado


class PriorityLevelEnum(str, Enum):
    """Niveles de prioridad"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class DamageTypeEnum(str, Enum):
    """Tipos de daño"""
    BACHE = "bache"
    GRIETA = "grieta"


class SeverityLevelEnum(str, Enum):
    """Niveles de severidad"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


# ============================================
# Request Schemas
# ============================================

class UpdateIncidentStatusRequest(BaseModel):
    """Request para actualizar el estado de un incidente"""
    status: IncidentStatusEnum = Field(
        ...,
        description="Nuevo estado del incidente"
    )
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Notas opcionales sobre el cambio de estado"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "in_progress",
                    "notes": "Iniciando trabajo en el sitio"
                }
            ]
        }
    )


class IncidentFilterParams(BaseModel):
    """Parámetros de filtrado para listar incidentes"""
    status: Optional[List[IncidentStatusEnum]] = Field(
        None,
        description="Filtrar por estados (múltiples permitidos)"
    )
    priority: Optional[List[PriorityLevelEnum]] = Field(
        None,
        description="Filtrar por niveles de prioridad (múltiples permitidos)"
    )
    damage_type: Optional[DamageTypeEnum] = Field(
        None,
        description="Filtrar por tipo de daño"
    )
    severity: Optional[SeverityLevelEnum] = Field(
        None,
        description="Filtrar por nivel de severidad"
    )
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="Filtrar por ciudad"
    )
    is_verified: Optional[bool] = Field(
        None,
        description="Filtrar por estado de verificación"
    )
    skip: int = Field(
        0,
        ge=0,
        description="Número de registros a saltar (paginación)"
    )
    limit: int = Field(
        50,
        ge=1,
        le=500,
        description="Número máximo de registros a retornar"
    )
    sort_by: Optional[str] = Field(
        "priority_score",
        description="Campo por el cual ordenar (priority_score, created_at, updated_at)"
    )
    sort_order: Optional[str] = Field(
        "desc",
        description="Orden de clasificación (asc, desc)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": ["open", "in_progress"],
                    "priority": ["alta", "critica"],
                    "skip": 0,
                    "limit": 20,
                    "sort_by": "priority_score",
                    "sort_order": "desc"
                }
            ]
        }
    )


# ============================================
# Response Schemas
# ============================================

class RecalculatePriorityResponse(BaseModel):
    """Response al recalcular prioridad"""
    incident_id: int = Field(..., description="ID del incidente")
    old_priority: PriorityLevelEnum = Field(..., description="Prioridad anterior")
    old_score: Optional[float] = Field(None, description="Score anterior")
    new_priority: PriorityLevelEnum = Field(..., description="Nueva prioridad")
    new_score: float = Field(..., description="Nuevo score calculado (0-100)")
    changed: bool = Field(..., description="Indica si hubo cambio de prioridad")
    factors: dict = Field(
        ...,
        description="Factores considerados en el cálculo"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "incident_id": 123,
                    "old_priority": "media",
                    "old_score": 45.5,
                    "new_priority": "alta",
                    "new_score": 72.3,
                    "changed": True,
                    "factors": {
                        "severity_weight": 0.35,
                        "age_weight": 0.20,
                        "location_weight": 0.20,
                        "nearby_pois": 3,
                        "nearby_duplicates": 2
                    }
                }
            ]
        }
    )


class IncidentBriefResponse(BaseModel):
    """Response breve de un incidente (para listas)"""
    id: int
    report_id: int
    damage_type: DamageTypeEnum
    severity: SeverityLevelEnum
    priority: PriorityLevelEnum
    priority_score: Optional[float]
    status: IncidentStatusEnum
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str]
    city: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class IncidentDetailResponse(BaseModel):
    """Response detallado de un incidente"""
    id: int
    report_id: int
    reported_by: int
    
    # Ubicación
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str]
    city: Optional[str]
    province: Optional[str]
    
    # Tipo y severidad
    damage_type: DamageTypeEnum
    severity: SeverityLevelEnum
    
    # Priorización
    priority: PriorityLevelEnum
    priority_score: Optional[float]
    
    # Estado
    status: IncidentStatusEnum

    # Tiempos
    estimated_repair_hours: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    verified_at: Optional[datetime]
    
    # Verificación
    is_verified: bool
    verified_by: Optional[int]
    verification_notes: Optional[str]
    
    # Imágenes
    before_image_url: Optional[str]
    after_image_url: Optional[str]
    
    # Notas
    notes: Optional[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 123,
                    "report_id": 456,
                    "reported_by": 789,
                    "latitude": -34.603722,
                    "longitude": -58.381592,
                    "address": "Av. Corrientes 1234",
                    "city": "Buenos Aires",
                    "province": "Buenos Aires",
                    "damage_type": "bache",
                    "severity": "alta",
                    "priority": "critica",
                    "priority_score": 85.5,
                    "status": "in_progress",
                    "estimated_repair_hours": 4.0,
                    "started_at": None,
                    "completed_at": None,
                    "verified_at": None,
                    "is_verified": False,
                    "verified_by": None,
                    "verification_notes": None,
                    "before_image_url": "https://storage/images/before_123.jpg",
                    "after_image_url": None,
                    "notes": "Bache profundo en zona céntrica",
                    "created_at": "2026-03-01T08:30:00Z",
                    "updated_at": "2026-03-03T10:00:00Z"
                }
            ]
        }
    )


class IncidentListResponse(BaseModel):
    """Response para lista de incidentes con paginación"""
    total: int = Field(..., description="Total de incidentes que cumplen los filtros")
    incidents: List[IncidentBriefResponse] = Field(..., description="Lista de incidentes")
    page: int = Field(..., description="Página actual (basado en skip/limit)")
    page_size: int = Field(..., description="Tamaño de página")
    total_pages: int = Field(..., description="Total de páginas disponibles")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total": 156,
                    "incidents": [
                        {
                            "id": 123,
                            "report_id": 456,
                            "damage_type": "bache",
                            "severity": "alta",
                            "priority": "critica",
                            "priority_score": 85.5,
                            "status": "in_progress",
                            "latitude": -34.603722,
                            "longitude": -58.381592,
                            "address": "Av. Corrientes 1234",
                            "city": "Buenos Aires",
                            "created_at": "2026-03-01T08:30:00Z",
                            "updated_at": "2026-03-03T10:00:00Z"
                        }
                    ],
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 8
                }
            ]
        }
    )


# ============================================
# Audit Log Schemas (P-07)
# ============================================

class AuditLogEntry(BaseModel):
    id: int
    incident_id: int
    user_id: Optional[int]
    event_type: str
    field_name: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    total: int
    entries: List[AuditLogEntry]


class SLAStatusEnum(str, Enum):
    """Estado SLA de un incidente"""
    NOT_STARTED = "not_started"
    ON_TRACK = "on_track"
    WARNING = "warning"
    OVERDUE = "overdue"
    COMPLETED = "completed"


class SLAStatusResponse(BaseModel):
    """SLA status de un incidente"""
    incident_id: int
    status: SLAStatusEnum
    sla_deadline: Optional[datetime] = None
    hours_remaining: Optional[float] = None
    sla_hours: float
    priority: str
    started_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SLAExpiringItem(BaseModel):
    incident_id: int
    status: SLAStatusEnum
    sla_deadline: Optional[datetime] = None
    hours_remaining: Optional[float] = None
    sla_hours: float
    priority: str
    address: Optional[str] = None
    city: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SLAExpiringResponse(BaseModel):
    expiring_count: int
    overdue_count: int
    items: List[SLAExpiringItem]


class SLAConfigResponse(BaseModel):
    id: int
    sla_hours_baja: float
    sla_hours_media: float
    sla_hours_alta: float
    sla_hours_critica: float
    warning_threshold_pct: float
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateSLAConfigRequest(BaseModel):
    sla_hours_baja: Optional[float] = Field(None, gt=0)
    sla_hours_media: Optional[float] = Field(None, gt=0)
    sla_hours_alta: Optional[float] = Field(None, gt=0)
    sla_hours_critica: Optional[float] = Field(None, gt=0)
    warning_threshold_pct: Optional[float] = Field(None, gt=0, le=1)


class IncidentStatsResponse(BaseModel):
    """Estadísticas de incidentes"""
    total_incidents: int
    by_status: dict = Field(..., description="Conteo por estado")
    by_priority: dict = Field(..., description="Conteo por prioridad")
    by_damage_type: dict = Field(..., description="Conteo por tipo de daño")
    avg_priority_score: Optional[float] = Field(None, description="Score promedio de prioridad")
    avg_resolution_hours: Optional[float] = Field(None, description="Horas promedio de resolución")
    pending_assignment: int = Field(..., description="Incidentes sin asignar (OPEN)")
    in_progress: int = Field(..., description="Incidentes en progreso")
    active_count: int = Field(0, description="Incidentes activos (open + assigned + in_progress)")
    resolved_count: int = Field(0, description="Incidentes resueltos/cerrados (resolved + verified + closed)")
    avg_ttr_hours: Optional[float] = Field(None, description="Tiempo promedio de asignación (TTR) en horas")
    sla_compliance_pct: Optional[float] = Field(None, description="Porcentaje de incidentes resueltos dentro del SLA (48h)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_incidents": 156,
                    "by_status": {
                        "open": 23,
                        "in_progress": 32,
                        "resolved": 28,
                        "verified": 18,
                        "closed": 10
                    },
                    "by_priority": {
                        "baja": 15,
                        "media": 48,
                        "alta": 62,
                        "critica": 31
                    },
                    "by_damage_type": {
                        "bache": 98,
                        "grieta": 58
                    },
                    "avg_priority_score": 58.7,
                    "avg_resolution_hours": 36.5,
                    "pending_assignment": 23,
                    "in_progress": 32
                }
            ]
        }
    )
