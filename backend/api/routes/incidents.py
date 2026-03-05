"""
API de Incidentes y Priorización (B-08)

Endpoints para:
- Listar incidentes con filtros
- Obtener detalle de incidente
- Actualizar estado de incidente
- Recalcular prioridad
- Asignar brigada
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
from models.brigade import Brigade
from schemas.incident import (
    IncidentStatusEnum,
    PriorityLevelEnum,
    DamageTypeEnum,
    SeverityLevelEnum,
    UpdateIncidentStatusRequest,
    AssignBrigadeRequest,
    RecalculatePriorityResponse,
    IncidentBriefResponse,
    IncidentDetailResponse,
    IncidentListResponse,
    IncidentStatsResponse
)
from services.priority_service import get_priority_service


router = APIRouter()


@router.get("/", response_model=IncidentListResponse)
def list_incidents(
    # Filtros
    status: Optional[List[IncidentStatusEnum]] = Query(None, description="Filtrar por estados"),
    priority: Optional[List[PriorityLevelEnum]] = Query(None, description="Filtrar por prioridades"),
    damage_type: Optional[DamageTypeEnum] = Query(None, description="Filtrar por tipo de daño"),
    severity: Optional[SeverityLevelEnum] = Query(None, description="Filtrar por severidad"),
    brigade_id: Optional[int] = Query(None, description="Filtrar por brigada asignada"),
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
    - Brigada asignada
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
    
    if brigade_id is not None:
        filters.append(Incident.assigned_brigade_id == brigade_id)
    
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
            "assigned_brigade_id": incident.assigned_brigade_id,
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


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
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
        "assigned_brigade_id": incident.assigned_brigade_id,
        "assigned_at": incident.assigned_at,
        "estimated_repair_hours": incident.estimated_repair_hours,
        "started_at": incident.started_at,
        "completed_at": incident.completed_at,
        "verified_at": incident.verified_at,
        "is_verified": incident.is_verified,
        "verified_by": incident.verified_by,
        "verification_notes": incident.verification_notes,
        "before_image_url": incident.before_image_url,
        "after_image_url": incident.after_image_url,
        "notes": incident.notes,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at
    }
    
    return IncidentDetailResponse(**incident_dict)


@router.patch("/{incident_id}/status", response_model=IncidentDetailResponse)
def update_incident_status(
    incident_id: int,
    request: UpdateIncidentStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Actualiza el estado de un incidente con validación de transiciones
    
    Transiciones válidas:
    - OPEN → ASSIGNED, CLOSED
    - ASSIGNED → IN_PROGRESS, OPEN
    - IN_PROGRESS → RESOLVED, ASSIGNED
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


@router.post("/{incident_id}/recalculate-priority", response_model=RecalculatePriorityResponse)
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
        
        # Información de factores (para transparencia)
        factors = {
            "severity_weight": priority_service.WEIGHT_SEVERITY,
            "age_weight": priority_service.WEIGHT_AGE,
            "damage_type_weight": priority_service.WEIGHT_DAMAGE_TYPE,
            "location_weight": priority_service.WEIGHT_LOCATION,
            "duplicates_weight": priority_service.WEIGHT_DUPLICATES,
            "severity_score": priority_service.SEVERITY_SCORES.get(incident.severity, 50),
            "damage_type_score": priority_service.DAMAGE_TYPE_SCORES.get(incident.damage_type, 50),
        }
        
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


@router.post("/{incident_id}/assign-brigade", response_model=IncidentDetailResponse)
def assign_brigade(
    incident_id: int,
    request: AssignBrigadeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Asigna una brigada a un incidente y cambia su estado a ASSIGNED
    
    También permite especificar las horas estimadas de reparación
    """
    # Verificar que el incidente existe
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidente {incident_id} no encontrado"
        )
    
    # Verificar que la brigada existe
    brigade = db.query(Brigade).filter(Brigade.id == request.brigade_id).first()
    if not brigade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brigada {request.brigade_id} no encontrada"
        )
    
    # Actualizar asignación
    incident.assigned_brigade_id = request.brigade_id
    incident.assigned_at = datetime.utcnow()
    
    if request.estimated_hours:
        incident.estimated_repair_hours = request.estimated_hours
    
    # Cambiar estado a ASSIGNED (si está en OPEN)
    if incident.status == IncidentStatus.OPEN:
        incident.status = IncidentStatus.ASSIGNED
    
    incident.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(incident)
    
    # Retornar detalle actualizado
    return get_incident(incident_id, db, current_user)


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
        by_status.get("assigned", 0) +
        by_status.get("in_progress", 0)
    )
    resolved_count = (
        by_status.get("resolved", 0) +
        by_status.get("verified", 0) +
        by_status.get("closed", 0)
    )
    
    # TTR: tiempo promedio desde created_at hasta assigned_at
    assigned_incidents = db.query(Incident).filter(
        and_(
            Incident.assigned_at.isnot(None),
            Incident.created_at.isnot(None)
        )
    ).all()
    
    if assigned_incidents:
        ttr_hours_list = [
            (inc.assigned_at - inc.created_at).total_seconds() / 3600
            for inc in assigned_incidents
            if inc.assigned_at >= inc.created_at
        ]
        avg_ttr_hours = round(sum(ttr_hours_list) / len(ttr_hours_list), 2) if ttr_hours_list else None
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
