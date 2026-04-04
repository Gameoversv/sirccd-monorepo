"""
API de Incidentes y Priorización (B-08)

Endpoints para:
- Listar incidentes con filtros
- Obtener detalle de incidente
- Actualizar estado de incidente
- Recalcular prioridad
- Obtener estadísticas
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from geoalchemy2.functions import ST_X, ST_Y
from datetime import datetime, timedelta
import math

from db.session import get_db
from api.deps import get_current_active_user
from models.user import User
from models.incident import Incident, IncidentStatus, PriorityLevel
from schemas.incident import (
    IncidentStatusEnum,
    PriorityLevelEnum,
    DamageTypeEnum,
    SeverityLevelEnum,
    UpdateIncidentStatusRequest,
    RecalculatePriorityResponse,
    IncidentBriefResponse,
    IncidentDetailResponse,
    IncidentListResponse,
    IncidentStatsResponse
)
from services.priority_service import get_priority_service
from core.config import settings


def _public_url(url: str | None) -> str | None:
    if url and "minio:9000" in url:
        return url.replace("minio:9000", "localhost:9000")
    return url


router = APIRouter()


@router.get("/", response_model=IncidentListResponse)
def list_incidents(
    # Filtros
    status: Optional[List[IncidentStatusEnum]] = Query(None, description="Filtrar por estados"),
    priority: Optional[List[PriorityLevelEnum]] = Query(None, description="Filtrar por prioridades"),
    damage_type: Optional[DamageTypeEnum] = Query(None, description="Filtrar por tipo de daño"),
    severity: Optional[SeverityLevelEnum] = Query(None, description="Filtrar por severidad"),
    city: Optional[str] = Query(None, max_length=100, description="Filtrar por ciudad"),
    is_verified: Optional[bool] = Query(None, description="Filtrar por verificación"),
    
    # Paginación y ordenamiento
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=500, description="Máximo de registros"),
    sort_by: str = Query("priority_score", description="Campo de ordenamiento"),
    sort_order: str = Query("desc", description="Orden (asc/desc)"),
    
    # Dependencias
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista incidentes con filtros avanzados y paginación
    
    Permite filtrar por:
    - Estado (múltiples)
    - Prioridad (múltiples)
    - Tipo de daño
    - Severidad
    - Ciudad
    - Estado de verificación
    
    Ordenamiento configurable por priority_score, created_at, o updated_at
    """
    # Construir query base
    query = db.query(Incident)
    
    # Aplicar filtros
    filters = []
    
    if status:
        # Convertir enums a valores del modelo
        status_values = [IncidentStatus(s.value) for s in status]
        filters.append(Incident.status.in_(status_values))
    
    if priority:
        priority_values = [PriorityLevel(p.value) for p in priority]
        filters.append(Incident.priority.in_(priority_values))
    
    if damage_type:
        from models.report import DamageType
        filters.append(Incident.damage_type == DamageType(damage_type.value))
    
    if severity:
        from models.report import SeverityLevel
        filters.append(Incident.severity == SeverityLevel(severity.value))
    
    if city:
        filters.append(Incident.city.ilike(f"%{city}%"))
    
    if is_verified is not None:
        filters.append(Incident.is_verified == is_verified)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Contar total
    total = query.count()
    
    # Aplicar ordenamiento
    if sort_order.lower() == "desc":
        order_func = desc
    else:
        order_func = asc
    
    if sort_by == "priority_score":
        query = query.order_by(order_func(Incident.priority_score))
    elif sort_by == "created_at":
        query = query.order_by(order_func(Incident.created_at))
    elif sort_by == "updated_at":
        query = query.order_by(order_func(Incident.updated_at))
    else:
        # Default: ordenar por prioridad
        query = query.order_by(desc(Incident.priority_score))
    
    # Aplicar paginación
    incidents = query.offset(skip).limit(limit).all()
    
    # Extraer coordenadas y convertir a response
    incidents_response = []
    for incident in incidents:
        # Extraer lat/lon de la geometría PostGIS
        lat = db.scalar(ST_Y(incident.location))
        lon = db.scalar(ST_X(incident.location))
        
        incident_dict = {
            "id": incident.id,
            "report_id": incident.report_id,
            "damage_type": incident.damage_type,
            "severity": incident.severity,
            "priority": incident.priority,
            "priority_score": incident.priority_score,
            "status": incident.status,
            "latitude": lat,
            "longitude": lon,
            "address": incident.address,
            "city": incident.city,
            "created_at": incident.created_at,
            "updated_at": incident.updated_at
        }
        incidents_response.append(IncidentBriefResponse(**incident_dict))
    
    # Calcular paginación
    page_size = limit
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    
    return IncidentListResponse(
        total=total,
        incidents=incidents_response,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{incident_id:int}", response_model=IncidentDetailResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el detalle completo de un incidente
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidente {incident_id} no encontrado"
        )
    
    # Extraer coordenadas
    lat = db.scalar(ST_Y(incident.location))
    lon = db.scalar(ST_X(incident.location))
    
    incident_dict = {
        "id": incident.id,
        "report_id": incident.report_id,
        "reported_by": incident.reported_by,
        "latitude": lat,
        "longitude": lon,
        "address": incident.address,
        "city": incident.city,
        "province": incident.province,
        "damage_type": incident.damage_type,
        "severity": incident.severity,
        "priority": incident.priority,
        "priority_score": incident.priority_score,
        "status": incident.status,
        "estimated_repair_hours": incident.estimated_repair_hours,
        "started_at": incident.started_at,
        "completed_at": incident.completed_at,
        "verified_at": incident.verified_at,
        "is_verified": incident.is_verified,
        "verified_by": incident.verified_by,
        "verification_notes": incident.verification_notes,
        "before_image_url": _public_url(incident.before_image_url),
        "after_image_url": _public_url(incident.after_image_url),
        "notes": incident.notes,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at
    }
    
    return IncidentDetailResponse(**incident_dict)


@router.patch("/{incident_id:int}/status", response_model=IncidentDetailResponse)
def update_incident_status(
    incident_id: int,
    request: UpdateIncidentStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Actualiza el estado de un incidente con validación de transiciones
    
    Transiciones válidas:
    - OPEN → IN_PROGRESS, CLOSED
    - IN_PROGRESS → RESOLVED, OPEN
    - RESOLVED → VERIFIED, IN_PROGRESS
    - VERIFIED → CLOSED, RESOLVED
    - CLOSED → (estado final)
    """
    priority_service = get_priority_service(db)
    
    try:
        # Convertir enum a modelo
        new_status = IncidentStatus(request.status.value)
        
        incident = priority_service.update_incident_status(
            incident_id=incident_id,
            new_status=new_status,
            notes=request.notes,
            user_id=current_user.id
        )
        
        # Retornar detalle actualizado
        return get_incident(incident_id, db, current_user)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar estado: {str(e)}"
        )


@router.post("/{incident_id:int}/recalculate-priority", response_model=RecalculatePriorityResponse)
def recalculate_priority(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Recalcula el score de prioridad de un incidente
    
    El cálculo considera:
    - Severidad del daño (35%)
    - Tiempo transcurrido (20%)
    - Tipo de daño (15%)
    - Proximidad a POIs importantes (20%)
    - Reportes duplicados en el área (10%)
    
    Retorna el nuevo score, nivel de prioridad y factores considerados
    """
    priority_service = get_priority_service(db)
    
    # Obtener incidente actual
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidente {incident_id} no encontrado"
        )
    
    old_priority = incident.priority
    old_score = incident.priority_score
    
    try:
        # Recalcular
        updated_incident = priority_service.recalculate_priority(incident_id)
        
        new_priority = updated_incident.priority
        new_score = updated_incident.priority_score
        
        # Determinar si hubo cambio
        changed = (old_priority != new_priority) or (old_score != new_score)
        
        factors = priority_service.calculate_priority_breakdown(updated_incident)
        
        return RecalculatePriorityResponse(
            incident_id=incident_id,
            old_priority=old_priority,
            old_score=old_score,
            new_priority=new_priority,
            new_score=new_score,
            changed=changed,
            factors=factors
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al recalcular prioridad: {str(e)}"
        )


@router.get("/stats/overview", response_model=IncidentStatsResponse)
def get_incident_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene estadísticas generales de incidentes
    
    Incluye:
    - Total de incidentes
    - Distribución por estado
    - Distribución por prioridad
    - Distribución por tipo de daño
    - Promedios de score y tiempo de resolución
    """
    # Total
    total_incidents = db.query(func.count(Incident.id)).scalar()
    
    # Por estado
    by_status = {}
    for status in IncidentStatus:
        count = db.query(func.count(Incident.id)).filter(
            Incident.status == status
        ).scalar()
        by_status[status.value] = count or 0
    
    # Por prioridad
    by_priority = {}
    for priority in PriorityLevel:
        count = db.query(func.count(Incident.id)).filter(
            Incident.priority == priority
        ).scalar()
        by_priority[priority.value] = count or 0
    
    # Por tipo de daño
    from models.report import DamageType
    by_damage_type = {}
    for damage_type in DamageType:
        count = db.query(func.count(Incident.id)).filter(
            Incident.damage_type == damage_type
        ).scalar()
        by_damage_type[damage_type.value] = count or 0
    
    # Score promedio
    avg_priority_score = db.query(func.avg(Incident.priority_score)).scalar()
    if avg_priority_score:
        avg_priority_score = round(float(avg_priority_score), 2)
    
    # Tiempo promedio de resolución (solo incidentes completados)
    completed_incidents = db.query(Incident).filter(
        and_(
            Incident.started_at.isnot(None),
            Incident.completed_at.isnot(None)
        )
    ).all()
    
    if completed_incidents:
        total_hours = sum(
            (inc.completed_at - inc.started_at).total_seconds() / 3600
            for inc in completed_incidents
        )
        avg_resolution_hours = round(total_hours / len(completed_incidents), 2)
    else:
        avg_resolution_hours = None
    
    # Contadores específicos
    pending_assignment = by_status.get("open", 0)
    in_progress = by_status.get("in_progress", 0)
    
    # Activos vs Resueltos
    active_count = (
        by_status.get("open", 0) +
        by_status.get("in_progress", 0)
    )
    resolved_count = (
        by_status.get("resolved", 0) +
        by_status.get("verified", 0) +
        by_status.get("closed", 0)
    )
    
    # TTR: tiempo promedio desde creación hasta completado
    completed_incidents = db.query(Incident).filter(
        Incident.completed_at.isnot(None)
    ).all()
    if completed_incidents:
        ttr_values = [
            (inc.completed_at - inc.created_at).total_seconds() / 3600
            for inc in completed_incidents
        ]
        avg_ttr_hours = round(sum(ttr_values) / len(ttr_values), 1)
    else:
        avg_ttr_hours = None

    # SLA compliance: % de incidentes completados dentro de 48 horas
    SLA_HOURS = 48
    completed_for_sla = db.query(Incident).filter(
        and_(
            Incident.started_at.isnot(None),
            Incident.completed_at.isnot(None)
        )
    ).all()
    
    if completed_for_sla:
        within_sla = sum(
            1 for inc in completed_for_sla
            if (inc.completed_at - inc.started_at).total_seconds() / 3600 <= SLA_HOURS
        )
        sla_compliance_pct = round(within_sla / len(completed_for_sla) * 100, 1)
    else:
        sla_compliance_pct = None
    
    return IncidentStatsResponse(
        total_incidents=total_incidents or 0,
        by_status=by_status,
        by_priority=by_priority,
        by_damage_type=by_damage_type,
        avg_priority_score=avg_priority_score,
        avg_resolution_hours=avg_resolution_hours,
        pending_assignment=pending_assignment,
        in_progress=in_progress,
        active_count=active_count,
        resolved_count=resolved_count,
        avg_ttr_hours=avg_ttr_hours,
        sla_compliance_pct=sla_compliance_pct
    )


# ============================================
# Heatmap — P-01
# ============================================

SEVERITY_WEIGHT = {"baja": 0.3, "media": 0.6, "alta": 1.0}

@router.get("/heatmap")
def get_heatmap_data(
    weight_by: str = Query(
        "frequency",
        regex="^(frequency|severity|age)$",
        description="Criterio de peso: frequency, severity o age",
    ),
    status: Optional[List[IncidentStatusEnum]] = Query(None),
    damage_type: Optional[DamageTypeEnum] = Query(None),
    severity: Optional[SeverityLevelEnum] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Devuelve puntos [lat, lng, intensity] para la capa de calor.

    weight_by:
      - frequency: todas las intensidades iguales (1.0)
      - severity:  baja=0.3, media=0.6, alta=1.0
      - age:       más antiguo → más intenso (normalizado 0.2-1.0)
    """
    query = db.query(Incident)

    filters_list = []
    if status:
        status_values = [IncidentStatus(s.value) for s in status]
        filters_list.append(Incident.status.in_(status_values))
    if damage_type:
        from models.report import DamageType
        filters_list.append(Incident.damage_type == DamageType(damage_type.value))
    if severity:
        from models.report import SeverityLevel as SL
        filters_list.append(Incident.severity == SL(severity.value))
    if filters_list:
        query = query.filter(and_(*filters_list))

    incidents = query.all()

    if not incidents:
        return {"points": [], "weight_by": weight_by, "count": 0}

    now = datetime.utcnow()

    # Pre-compute age range for normalisation
    if weight_by == "age":
        ages = [(now - inc.created_at).total_seconds() for inc in incidents]
        max_age = max(ages) if ages else 1
        max_age = max_age if max_age > 0 else 1

    points = []
    for idx, inc in enumerate(incidents):
        lat = db.scalar(ST_Y(inc.location))
        lon = db.scalar(ST_X(inc.location))
        if lat is None or lon is None:
            continue

        if weight_by == "severity":
            intensity = SEVERITY_WEIGHT.get(inc.severity.value if hasattr(inc.severity, 'value') else inc.severity, 0.5)
        elif weight_by == "age":
            age_secs = (now - inc.created_at).total_seconds()
            intensity = 0.2 + 0.8 * (age_secs / max_age)
        else:
            intensity = 1.0

        points.append([round(lat, 6), round(lon, 6), round(intensity, 3)])

    return {"points": points, "weight_by": weight_by, "count": len(points)}
