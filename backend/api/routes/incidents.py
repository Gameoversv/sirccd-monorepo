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
from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from geoalchemy2.functions import ST_X, ST_Y, ST_Within
from datetime import datetime, timedelta, date
import math

from db.session import get_db
from api.deps import get_current_active_user, get_optional_user, require_supervisor, require_admin
from core.image_tokens import sign_image_url, verify_image_signature
import json as _json
from models.user import User, UserRole
from models.incident import Incident, IncidentStatus, PriorityLevel
from models.report import Report
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
    IncidentStatsResponse,
    AuditLogEntry,
    AuditLogListResponse,
    SLAStatusResponse,
    SLAExpiringResponse,
    SLAExpiringItem,
    SLAStatusEnum,
    SLAConfigResponse,
    UpdateSLAConfigRequest,
)
from models.incident_audit_log import IncidentAuditLog
from services.priority_service import get_priority_service
from services.storage import storage_service
from core.config import settings


router = APIRouter()

_SCOPE = "incidents"


def _image_url(incident_id: int, variant: str, stored_url: str | None) -> str | None:
    """URL firmada del proxy. El bucket de MinIO es privado (S-03)."""
    if not stored_url:
        return None
    return sign_image_url(_SCOPE, incident_id, variant)


# Scope del proxy de imágenes de reportes (ver api/routes/reports.py).
_REPORTS_SCOPE = "reportes"


def _report_annotated_url(report: Report) -> str | None:
    """URL firmada de la detección (bounding boxes) si el worker la generó."""
    if not report.detections_json:
        return None
    try:
        det = _json.loads(report.detections_json)
    except ValueError:
        return None
    if not det.get("annotated_image_url"):
        return None
    return sign_image_url(_REPORTS_SCOPE, report.id, "annotated")


def _member_reports(db: Session, incident: Incident) -> list[dict]:
    """
    Reportes agrupados en el incidente: el primario más los duplicados que
    apuntan a él (M-13). Cada uno con su original y su detección firmadas, para
    poder revisarlos desde el incidente sin ir a la pestaña de reportes.
    """
    reports = (
        db.query(Report)
        .filter(
            or_(
                Report.id == incident.report_id,
                Report.duplicate_of_report_id == incident.report_id,
            )
        )
        .all()
    )
    # Primario primero, luego duplicados por id ascendente.
    reports.sort(key=lambda r: (r.id != incident.report_id, r.id))

    return [
        {
            "report_id": r.id,
            "is_primary": r.id == incident.report_id,
            "status": r.status,
            "created_at": r.created_at,
            "original_image_url": sign_image_url(_REPORTS_SCOPE, r.id, "original")
            if r.image_url
            else None,
            "annotated_image_url": _report_annotated_url(r),
        }
        for r in reports
    ]


@router.get("/", response_model=IncidentListResponse)
def list_incidents(
    # Filtros
    status: Optional[List[IncidentStatusEnum]] = Query(None, description="Filtrar por estados"),
    priority: Optional[List[PriorityLevelEnum]] = Query(None, description="Filtrar por prioridades"),
    damage_type: Optional[DamageTypeEnum] = Query(None, description="Filtrar por tipo de daño"),
    severity: Optional[SeverityLevelEnum] = Query(None, description="Filtrar por severidad"),
    city: Optional[str] = Query(None, max_length=100, description="Filtrar por ciudad"),
    is_verified: Optional[bool] = Query(None, description="Filtrar por verificación"),
    date_from: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    zone_id: Optional[int] = Query(None, description="Filtrar por zona administrativa"),
    
    # Paginación y ordenamiento
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=500, description="Máximo de registros"),
    sort_by: str = Query("priority_score", description="Campo de ordenamiento"),
    sort_order: str = Query("desc", description="Orden (asc/desc)"),
    
    # Dependencias
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor)
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

    if date_from is not None:
        filters.append(Incident.created_at >= datetime.combine(date_from, datetime.min.time()))

    if date_to is not None:
        filters.append(Incident.created_at <= datetime.combine(date_to, datetime.max.time()))

    if zone_id is not None:
        from models.zone import Zone
        zone = db.query(Zone).filter(Zone.id == zone_id).first()
        if zone is not None:
            filters.append(ST_Within(Incident.location, zone.boundary))

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
    current_user: User = Depends(require_supervisor)
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
        "before_image_url": _image_url(incident.id, "before", incident.before_image_url),
        "after_image_url": _image_url(incident.id, "after", incident.after_image_url),
        "member_reports": _member_reports(db, incident),
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
    current_user: User = Depends(require_supervisor)
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


@router.patch("/{incident_id:int}/details")
def update_incident_details(
    incident_id: int,
    estimated_repair_hours: Optional[float] = Form(None),
    after_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor)
):
    """Actualiza tiempo estimado y/o foto después del incidente"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")
    if estimated_repair_hours is not None:
        old_hours = incident.estimated_repair_hours
        incident.estimated_repair_hours = estimated_repair_hours
        audit_entry = IncidentAuditLog(
            incident_id=incident_id,
            user_id=current_user.id,
            event_type="manual_update",
            field_name="estimated_repair_hours",
            old_value=str(old_hours) if old_hours is not None else None,
            new_value=str(estimated_repair_hours),
        )
        db.add(audit_entry)
    db.commit()
    db.refresh(incident)
    return {
        "id": incident_id,
        "estimated_repair_hours": incident.estimated_repair_hours,
        "after_image_url": _image_url(incident.id, "after", incident.after_image_url),
    }


@router.post("/{incident_id:int}/after-image")
async def upload_after_image(
    incident_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor)
):
    """Sube la foto 'después' de un incidente"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente no encontrado")
    try:
        image_url, _, _, _, _ = await storage_service.upload_image(file=image, folder="after", anonymize=False)
        incident.after_image_url = image_url
        audit_entry = IncidentAuditLog(
            incident_id=incident_id,
            user_id=current_user.id,
            event_type="image_uploaded",
            field_name="after_image_url",
            new_value=image_url,
        )
        db.add(audit_entry)
        db.commit()
        return {
            "id": incident_id,
            "after_image_url": _image_url(incident.id, "after", image_url),
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{incident_id:int}/image",
    summary="Servir la imagen antes/después de un incidente",
    description=(
        "Descarga la imagen desde MinIO y la reenvía. El bucket es privado, "
        "así que este proxy es el único acceso: se autoriza con el token o "
        "con la firma de corta duración que incluyen las URLs del API."
    ),
    responses={
        200: {"content": {"image/*": {}}, "description": "Bytes de la imagen"},
        401: {"description": "Sin token ni firma válida"},
        404: {"description": "Incidente o imagen no encontrada"},
    },
)
def get_incident_image(
    incident_id: int,
    variant: str = Query("before", pattern="^(before|after)$"),
    exp: Optional[int] = Query(None),
    sig: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Sirve la foto 'antes' o 'después' de un incidente."""

    has_signature = verify_image_signature(_SCOPE, incident_id, variant, exp, sig)

    # Los incidentes solo los ve personal de la alcaldía; sin firma se exige
    # el mismo rol que en GET /incidents/{id}.
    if not has_signature and (
        current_user is None
        or current_user.role not in (UserRole.SUPERVISOR, UserRole.ADMIN)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere token de supervisor o una URL firmada válida",
            headers={"WWW-Authenticate": "Bearer"},
        )

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidente {incident_id} no encontrado",
        )

    object_url = (
        incident.before_image_url if variant == "before" else incident.after_image_url
    )
    if not object_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El incidente {incident_id} no tiene imagen '{variant}'",
        )

    content = storage_service.read_image_bytes(object_url)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La imagen no está disponible en el almacenamiento",
        )

    return Response(
        content=content,
        media_type=storage_service.guess_content_type(object_url),
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.post("/{incident_id:int}/recalculate-priority", response_model=RecalculatePriorityResponse)
def recalculate_priority(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor)
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
        updated_incident = priority_service.recalculate_priority(incident_id, user_id=current_user.id)
        
        new_priority = updated_incident.priority
        new_score = updated_incident.priority_score
        
        # Determinar si hubo cambio
        changed = (old_priority != new_priority) or (old_score != new_score)
        
        # recalculate_priority ya persistió el desglose exacto; reutilizarlo
        # evita una segunda pasada de dedup visual.
        factors = updated_incident.priority_breakdown or priority_service.calculate_priority_breakdown(
            updated_incident, visual_dedup=False
        )

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


@router.get("/{incident_id:int}/priority-breakdown")
def get_priority_breakdown(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor)
):
    """
    Obtiene el desglose de prioridad.

    Devuelve el desglose persistido (calculado con dedup visual al recalcular la
    prioridad o vía backfill). Si el incidente aún no lo tiene, computa un
    desglose rápido al vuelo (sin descargas de imágenes ni ResNet50) para no
    bloquear la apertura del incidente; ese factor de duplicados es aproximado
    hasta el próximo recálculo.
    """
    priority_service = get_priority_service(db)
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incidente {incident_id} no encontrado")
    try:
        stored = incident.priority_breakdown
        if stored:
            return {
                "incident_id": incident_id,
                "priority": incident.priority,
                "priority_score": incident.priority_score,
                "factors": stored,
                "stale": False,
            }

        factors = priority_service.calculate_priority_breakdown(incident, visual_dedup=False)
        return {
            "incident_id": incident_id,
            "priority": incident.priority,
            "priority_score": incident.priority_score,
            "factors": factors,
            "stale": True,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/stats/overview", response_model=IncidentStatsResponse)
def get_incident_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor)
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

    # SLA compliance: % de incidentes completados dentro de su deadline SLA (P-06)
    from services.sla_service import get_sla_hours as _get_sla_hours
    completed_for_sla = db.query(Incident).filter(
        and_(
            Incident.started_at.isnot(None),
            Incident.completed_at.isnot(None)
        )
    ).all()

    if completed_for_sla:
        within_sla = 0
        for inc in completed_for_sla:
            # Usar sla_deadline si existe, sino calcular con horas configuradas
            if inc.sla_deadline:
                within_sla += 1 if inc.completed_at <= inc.sla_deadline else 0
            else:
                sla_h = _get_sla_hours(db, inc.priority)
                elapsed = (inc.completed_at - inc.started_at).total_seconds() / 3600
                within_sla += 1 if elapsed <= sla_h else 0
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
# Bitácora / Auditoría — P-07
# ============================================

@router.get("/{incident_id:int}/audit", response_model=AuditLogListResponse)
def get_incident_audit_log(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor),
):
    """Retorna la bitácora completa de cambios de un incidente"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidente {incident_id} no encontrado",
        )

    entries = (
        db.query(IncidentAuditLog)
        .filter(IncidentAuditLog.incident_id == incident_id)
        .order_by(IncidentAuditLog.created_at.asc())
        .all()
    )

    return AuditLogListResponse(total=len(entries), entries=entries)


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


# ============================================
# SLA — P-06
# ============================================

@router.get("/sla/expiring", response_model=SLAExpiringResponse)
def get_sla_expiring(
    within_hours: float = Query(4.0, gt=0, description="Ventana de tiempo en horas"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor),
):
    """
    Incidentes que vencerán su SLA dentro de `within_hours` horas,
    más los que ya están vencidos.
    """
    from services.sla_service import get_expiring_incidents, get_overdue_incidents, get_sla_info

    expiring = get_expiring_incidents(db, within_hours=within_hours)
    overdue = get_overdue_incidents(db)

    items: list[SLAExpiringItem] = []
    for inc in overdue:
        info = get_sla_info(inc, db)
        items.append(SLAExpiringItem(
            incident_id=inc.id,
            status=SLAStatusEnum(info["status"]),
            sla_deadline=info["sla_deadline"],
            hours_remaining=info["hours_remaining"],
            sla_hours=info["sla_hours"],
            priority=info["priority"],
            address=inc.address,
            city=inc.city,
        ))
    for inc in expiring:
        info = get_sla_info(inc, db)
        items.append(SLAExpiringItem(
            incident_id=inc.id,
            status=SLAStatusEnum(info["status"]),
            sla_deadline=info["sla_deadline"],
            hours_remaining=info["hours_remaining"],
            sla_hours=info["sla_hours"],
            priority=info["priority"],
            address=inc.address,
            city=inc.city,
        ))

    return SLAExpiringResponse(
        expiring_count=len(expiring),
        overdue_count=len(overdue),
        items=items,
    )


@router.get("/{incident_id:int}/sla", response_model=SLAStatusResponse)
def get_incident_sla(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor),
):
    """Estado SLA de un incidente específico."""
    from services.sla_service import get_sla_info

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incidente {incident_id} no encontrado")

    info = get_sla_info(incident, db)
    return SLAStatusResponse(
        incident_id=info["incident_id"],
        status=SLAStatusEnum(info["status"]),
        sla_deadline=info["sla_deadline"],
        hours_remaining=info["hours_remaining"],
        sla_hours=info["sla_hours"],
        priority=info["priority"],
        started_at=info["started_at"],
    )


@router.get("/sla/config", response_model=SLAConfigResponse)
def get_sla_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor),
):
    """Obtiene la configuración activa de SLAs."""
    from models.sla_config import SLAConfig
    from services.sla_service import DEFAULT_SLA_HOURS, DEFAULT_WARNING_THRESHOLD
    from models.incident import PriorityLevel

    cfg = db.query(SLAConfig).order_by(SLAConfig.id.asc()).first()
    if cfg is None:
        # Retorna defaults sin persistir
        from datetime import datetime as _dt
        return SLAConfigResponse(
            id=0,
            sla_hours_baja=DEFAULT_SLA_HOURS[PriorityLevel.BAJA],
            sla_hours_media=DEFAULT_SLA_HOURS[PriorityLevel.MEDIA],
            sla_hours_alta=DEFAULT_SLA_HOURS[PriorityLevel.ALTA],
            sla_hours_critica=DEFAULT_SLA_HOURS[PriorityLevel.CRITICA],
            warning_threshold_pct=DEFAULT_WARNING_THRESHOLD,
            updated_at=_dt.utcnow(),
        )
    return cfg


@router.put("/sla/config", response_model=SLAConfigResponse)
def update_sla_config(
    request: UpdateSLAConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Actualiza (o crea) la configuración de SLAs. Solo ADMIN."""

    from models.sla_config import SLAConfig

    cfg = db.query(SLAConfig).order_by(SLAConfig.id.asc()).first()
    if cfg is None:
        cfg = SLAConfig(updated_by=current_user.id)
        db.add(cfg)

    if request.sla_hours_baja is not None:
        cfg.sla_hours_baja = request.sla_hours_baja
    if request.sla_hours_media is not None:
        cfg.sla_hours_media = request.sla_hours_media
    if request.sla_hours_alta is not None:
        cfg.sla_hours_alta = request.sla_hours_alta
    if request.sla_hours_critica is not None:
        cfg.sla_hours_critica = request.sla_hours_critica
    if request.warning_threshold_pct is not None:
        cfg.warning_threshold_pct = request.warning_threshold_pct
    cfg.updated_by = current_user.id

    db.commit()
    db.refresh(cfg)
    return cfg


@router.post("/sla/check")
def trigger_sla_check(
    current_user: User = Depends(require_admin),
):
    """Encola manualmente el job de verificación de SLAs. Solo ADMIN."""

    try:
        from services.queue_service import get_queue_service
        svc = get_queue_service()
        job = svc.queue.enqueue("tasks.sla_tasks.check_sla_alerts")
        return {"queued": True, "job_id": job.id if job else None}
    except Exception as exc:
        return {"queued": False, "error": str(exc)}
