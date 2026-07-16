"""
Rutas de Reportes - Gestión de reportes ciudadanos
"""

import json as _json
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape

from db.session import get_db
from api.deps import (
    get_current_active_user,
    ActiveUser,
    OptionalUser,
    SupervisorUser,
    DbSession,
    require_supervisor,
)
from core.image_tokens import sign_image_url, verify_image_signature
from models.user import User
from models.report import Report, ReportStatus, DamageType, SeverityLevel
from models.incident import Incident, IncidentStatus, PriorityLevel
from schemas.report import CreateReportResponse, ReportResponse, UpdateReportStatusRequest
from services.storage import storage_service
from services.queue_service import queue_service
from services.report_processing_service import resolve_incident_dedup
from services.ml_service import ml_service
from services.deduplication_service import get_deduplication_service
from services.priority_service import get_priority_service


router = APIRouter(prefix="/reportes", tags=["Reportes"])

_SCOPE = "reportes"


def _image_url(report_id: int, variant: str = "original") -> str:
    """URL firmada del proxy. El bucket de MinIO es privado (S-03)."""
    return sign_image_url(_SCOPE, report_id, variant)


def _annotated_image_url(report: Report) -> Optional[str]:
    """URL firmada de la imagen con bounding boxes, si el worker la generó."""
    if not report.detections_json:
        return None
    try:
        det = _json.loads(report.detections_json)
    except ValueError:
        return None
    if not det.get("annotated_image_url"):
        return None
    return _image_url(report.id, "annotated")


def _resolve_focal_scale_factor(exif_data, fallback: Optional[float]) -> float:
    """Usa EXIF cuando hay focal; si no, usa el factor enviado por la app."""
    has_exif_focal = bool(exif_data.focal_length_35mm or exif_data.focal_length_mm)
    if has_exif_focal or fallback is None:
        return exif_data.zoom_scale_factor
    return max(0.25, min(2.0, float(fallback)))


# ── List reports ──────────────────────────────────────────────────────────────

@router.get("", summary="Listar reportes con filtros y paginación")
def list_reports(
    db: DbSession,
    current_user: ActiveUser,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    damage_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
):
    query = db.query(Report)

    # Ciudadanos solo ven sus propios reportes
    if current_user.role.value == "ciudadano":
        query = query.filter(Report.user_id == current_user.id)

    if status_filter:
        query = query.filter(Report.status == ReportStatus(status_filter))
    if damage_type:
        query = query.filter(Report.damage_type == DamageType(damage_type))
    if severity:
        query = query.filter(Report.severity == SeverityLevel(severity))
    if search:
        query = query.filter(
            Report.description.ilike(f"%{search}%")
            | Report.address.ilike(f"%{search}%")
            | Report.city.ilike(f"%{search}%")
        )

    total = query.count()

    order = desc if sort_order == "desc" else asc
    col = getattr(Report, sort_by, Report.created_at)
    query = query.order_by(order(col))

    reports = query.offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for r in reports:
        point = to_shape(r.location)

        # Parse detections_json to extract derived fields
        model_precision = None
        model_recall = None
        model_map50 = None
        if r.detections_json:
            try:
                det = _json.loads(r.detections_json)
                model_precision = det.get("model_precision")
                model_recall = det.get("model_recall")
                model_map50 = det.get("model_map50")
            except Exception:
                pass

        items.append({
            "id": r.id,
            "user_id": r.user_id,
            "latitude": point.y,
            "longitude": point.x,
            "address": r.address,
            "city": r.city,
            "province": r.province,
            "damage_type": r.damage_type.value,
            "severity": r.severity.value,
            "confidence": r.confidence,
            "image_url": _image_url(r.id),
            "annotated_image_url": _annotated_image_url(r),
            "model_precision": model_precision,
            "model_recall": model_recall,
            "model_map50": model_map50,
            "detections_json": r.detections_json,
            "status": r.status.value,
            "description": r.description,
            "created_at": r.created_at.isoformat() + "Z",
            "updated_at": r.updated_at.isoformat() + "Z",
        })

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, -(-total // per_page)),
        "items": items,
    }


# ── Review (approve / reject) ────────────────────────────────────────────────

@router.patch(
    "/{report_id}/review",
    summary="Aprobar o rechazar un reporte (SUPERVISOR+)",
)
def review_report(
    report_id: int,
    body: UpdateReportStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Reporte no encontrado")

    if body.status not in ("approved", "rejected"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Solo se puede aprobar o rechazar")

    report.status = ReportStatus(body.status)
    report.reviewed_at = datetime.utcnow()
    if body.rejection_reason:
        report.rejection_reason = body.rejection_reason

    # If approved → buscar incidente cercano (dedup geo) o crear uno nuevo
    incident_id = None
    if body.status == "approved":
        import logging as _logging
        _log = _logging.getLogger(__name__)

        priority_service = get_priority_service(db)

        # Dedup geo+visual: buscar incidente cercano y verificar similitud visual
        report_image_for_dedup = None
        try:
            from services.deduplication_service import load_image_from_url
            report_image_for_dedup = load_image_from_url(report.image_url)
        except Exception:
            pass

        existing_incident = resolve_incident_dedup(db, report, report_image_for_dedup)

        if existing_incident:
            # Asociar reporte al incidente existente en lugar de crear uno nuevo
            incident_id = existing_incident.id
            _log.info(
                "Reporte %s asociado a incidente existente %s (dedup geo, <30m)",
                report.id, existing_incident.id,
            )
            # Recalcular prioridad del incidente existente (nuevo reporte puede subir score)
            try:
                priority_level, score = priority_service.calculate_priority(existing_incident)
                existing_incident.priority = priority_level
                existing_incident.priority_score = score
            except Exception as prio_err:
                _log.warning("Error recalculando prioridad para incidente %s: %s", existing_incident.id, prio_err)
        else:
            new_incident = Incident(
                report_id=report.id,
                reported_by=report.user_id,
                location=report.location,
                address=report.address,
                city=report.city,
                province=report.province,
                damage_type=report.damage_type,
                severity=report.severity,
                priority=PriorityLevel.MEDIA,
                priority_score=0.0,
                status=IncidentStatus.OPEN,
                before_image_url=report.image_url,
                notes=report.description,
            )
            db.add(new_incident)
            db.flush()

            try:
                priority_level, score = priority_service.calculate_priority(new_incident)
                new_incident.priority = priority_level
                new_incident.priority_score = score
            except Exception as prio_err:
                _log.warning("Error calculando prioridad para incidente %s: %s", new_incident.id, prio_err)

            incident_id = new_incident.id

    db.commit()

    return {
        "id": report.id,
        "status": report.status.value,
        "reviewed_at": (report.reviewed_at.isoformat() + "Z") if report.reviewed_at else None,
        "incident_id": incident_id,
    }


def _mock_ml_detection(image_url: str) -> tuple[DamageType, SeverityLevel, float]:
    """
    Mock de detección ML - Retorna detección simulada
    
    TODO: Reemplazar con llamada real al modelo YOLO cuando esté disponible
    
    Args:
        image_url: URL de la imagen a analizar
    
    Returns:
        Tuple[DamageType, SeverityLevel, float]: (tipo, severidad, confianza)
    """
    import random
    
    # Simulación simple: aleatorizar resultados
    damage_type = random.choice([DamageType.BACHE, DamageType.GRIETA])
    severity = random.choice([SeverityLevel.BAJA, SeverityLevel.MEDIA, SeverityLevel.ALTA])
    confidence = round(random.uniform(0.5, 0.95), 2)
    
    return damage_type, severity, confidence


@router.post(
    "",
    response_model=CreateReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo reporte",
    description="""
    Crea un nuevo reporte de daño vial con foto, GPS y descripción.
    
    **Proceso:**
    1. Valida y sube la imagen a storage (MinIO/local)
    2. Ejecuta detección ML para identificar tipo y severidad
    3. Guarda metadatos en base de datos
    4. Retorna ID del reporte y resultado de detección
    
    **Requisitos:**
    - Usuario autenticado y activo
    - Imagen válida (JPG, PNG, WEBP, max 10MB)
    - Coordenadas GPS válidas (WGS84)
    
    **Nota:** La detección ML puede tardar unos segundos.
    El estado inicial es 'processing' hasta que se complete el análisis.
    """
)
async def create_report(
    # Dependencias
    db: DbSession,
    current_user: ActiveUser,
    
    # Imagen (multipart/form-data)
    image: UploadFile = File(
        ...,
        description="Imagen del daño vial (JPG, PNG, WEBP, max 10MB)"
    ),
    
    # Coordenadas GPS (form fields)
    latitude: float = Form(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitud en formato WGS84",
        examples=[-34.603722]
    ),
    longitude: float = Form(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitud en formato WGS84",
        examples=[-58.381592]
    ),
    
    # Campos opcionales
    description: Optional[str] = Form(
        None,
        max_length=2000,
        description="Descripción del problema"
    ),
    address: Optional[str] = Form(
        None,
        max_length=500,
        description="Dirección aproximada"
    ),
    city: Optional[str] = Form(
        None,
        max_length=100,
        description="Ciudad"
    ),
    province: Optional[str] = Form(
        None,
        max_length=100,
        description="Provincia/Estado"
    ),
    focal_scale_factor: Optional[float] = Form(
        None,
        ge=0.25,
        le=2.0,
        description="Factor opcional de normalizacion por zoom enviado por la app movil"
    ),
) -> CreateReportResponse:
    """
    Crea un nuevo reporte con imagen, GPS y descripción
    """
    
    # 1. Validar y subir imagen (con anonimización automática B-05)
    try:
        image_url, image_width, image_height, anonymization_stats, exif_data = await storage_service.upload_image(
            file=image,
            folder="reports",
            anonymize=True  # B-05: SIEMPRE anonimizar antes de guardar
        )

        # Log de anonimización
        if anonymization_stats.get('anonymized'):
            print(f" Imagen anonimizada: {anonymization_stats['regions_blurred']} regiones "
                  f"({anonymization_stats['faces_detected']} rostros, {anonymization_stats['plates_detected']} placas)")

        # Coordenadas: EXIF GPS tiene prioridad sobre las del usuario al momento de subir.
        # Razón: el usuario puede subir una foto tomada hace tiempo en otro lugar.
        # EXIF GPS = dónde se tomó la foto = dónde está el bache real.
        report_latitude = latitude
        report_longitude = longitude
        location_source = "user"

        if exif_data.gps_latitude is not None and exif_data.gps_longitude is not None:
            report_latitude = exif_data.gps_latitude
            report_longitude = exif_data.gps_longitude
            location_source = "exif"
            print(
                f"ℹ  Usando coordenadas EXIF ({report_latitude:.6f}, {report_longitude:.6f}) "
                f"en lugar de coordenadas del usuario ({latitude:.6f}, {longitude:.6f})"
            )
        else:
            print(f"ℹ  Sin GPS en EXIF — usando coordenadas del usuario ({latitude:.6f}, {longitude:.6f})")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la imagen: {str(e)}"
        )
    
    # 2. Crear reporte en base de datos con valores placeholder
    # Los valores reales serán actualizados por el worker ML
    try:
        # Valores placeholder mientras se procesa
        damage_type = DamageType.BACHE
        severity = SeverityLevel.MEDIA
        confidence = 0.0
        
        # Crear geometría PostGIS (POINT)
        # Formato WKT: POINT(longitude latitude) — nota el orden lon/lat
        location_wkt = f"POINT({report_longitude} {report_latitude})"
        location = WKTElement(location_wkt, srid=4326)
        
        new_report = Report(
            user_id=current_user.id,
            location=location,
            address=address,
            city=city,
            province=province,
            damage_type=damage_type,
            severity=severity,
            confidence=confidence,
            image_url=image_url,
            image_width=image_width,
            image_height=image_height,
            description=description,
            status=ReportStatus.PROCESSING,  # Inicialmente en procesamiento
            detections_json=None,  # Se llenará por el worker
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        # 3. Detección ML: se encola para el worker RQ.
        # Corría inline y la petición tardaba ~42s, por encima del timeout de
        # 30s del cliente móvil: el reporte se creaba igual, pero la app lo
        # daba por fallido y reintentaba, duplicando reportes.
        # El factor de zoom se resuelve aquí, donde todavía existe el EXIF: la
        # imagen almacenada va sin metadatos (D-08).
        job = queue_service.enqueue_ml_detection(
            report_id=new_report.id,
            focal_scale_factor=_resolve_focal_scale_factor(
                exif_data,
                focal_scale_factor,
            ),
        )
        job_id = job.id if job else None

        if job is None:
            # El reporte queda en PROCESSING y sin detección. No se ejecuta
            # inline como respaldo: eso reintroduciría el timeout que este
            # cambio elimina. Queda para revisión manual.
            print(
                f" Advertencia: no se pudo encolar detección ML para "
                f"reporte {new_report.id}"
            )
        else:
            print(f" Detección ML encolada para reporte {new_report.id}: job {job_id}")


    except Exception as e:
        db.rollback()
        # Intentar eliminar imagen si falló la BD
        try:
            await storage_service.delete_image(image_url)
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el reporte: {str(e)}"
        )
    
    # 4. Preparar respuesta
    return CreateReportResponse(
        id=new_report.id,
        status=new_report.status,
        damage_type=damage_type,
        severity=severity,
        confidence=confidence,
        image_url=_image_url(new_report.id),
        latitude=report_latitude,
        longitude=report_longitude,
        description=description,
        created_at=new_report.created_at,
        job_id=job_id
    )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Obtener reporte por ID",
    description="Obtiene los detalles completos de un reporte específico"
)
async def get_report(
    report_id: int,
    db: DbSession,
    current_user: ActiveUser,
) -> ReportResponse:
    """Obtiene un reporte por su ID"""
    
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reporte {report_id} no encontrado"
        )

    if current_user.role.value == "ciudadano" and report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este reporte"
        )

    # Extraer coordenadas del campo Geography
    # report.location es un WKBElement, necesitamos convertirlo
    point = to_shape(report.location)
    latitude = point.y
    longitude = point.x
    
    # Construir respuesta
    return ReportResponse(
        id=report.id,
        user_id=report.user_id,
        latitude=latitude,
        longitude=longitude,
        address=report.address,
        city=report.city,
        province=report.province,
        damage_type=report.damage_type,
        severity=report.severity,
        confidence=report.confidence,
        image_url=_image_url(report.id),
        annotated_image_url=_annotated_image_url(report),
        image_width=report.image_width,
        image_height=report.image_height,
        detections_json=report.detections_json,
        status=report.status,
        description=report.description,
        rejection_reason=report.rejection_reason,
        created_at=report.created_at,
        updated_at=report.updated_at,
        reviewed_at=report.reviewed_at
    )


@router.get(
    "/{report_id}/image",
    summary="Servir la imagen de un reporte",
    description=(
        "Descarga la imagen desde MinIO y la reenvía. El bucket es privado, "
        "así que este proxy es el único acceso: se autoriza con el token o "
        "con la firma de corta duración que incluyen las URLs del API."
    ),
    responses={
        200: {"content": {"image/*": {}}, "description": "Bytes de la imagen"},
        401: {"description": "Sin token ni firma válida"},
        404: {"description": "Reporte o imagen no encontrada"},
    },
)
def get_report_image(
    report_id: int,
    db: DbSession,
    current_user: OptionalUser,
    variant: str = Query("original", pattern="^(original|annotated)$"),
    exp: Optional[int] = Query(None),
    sig: Optional[str] = Query(None),
) -> Response:
    """Sirve la imagen original o la anotada de un reporte."""

    has_signature = verify_image_signature(_SCOPE, report_id, variant, exp, sig)

    if not has_signature and current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere token o una URL firmada válida",
            headers={"WWW-Authenticate": "Bearer"},
        )

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reporte {report_id} no encontrado",
        )

    # La firma ya autoriza esta imagen concreta; sin ella se aplican las mismas
    # reglas de visibilidad que en GET /reportes/{id}.
    if not has_signature and current_user.role.value == "ciudadano" \
            and report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este reporte",
        )

    object_url = _resolve_image_object(report, variant)
    if not object_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El reporte {report_id} no tiene imagen '{variant}'",
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


def _resolve_image_object(report: Report, variant: str) -> Optional[str]:
    """Devuelve la URL almacenada del objeto para la variante pedida."""
    if variant == "original":
        return report.image_url

    if not report.detections_json:
        return None
    try:
        det = _json.loads(report.detections_json)
    except ValueError:
        return None
    return det.get("annotated_image_url")


@router.get(
    "/jobs/{job_id}/status",
    summary="Obtener estado de job ML",
    description="Consulta el estado de procesamiento ML de un job RQ (B-06)"
)
async def get_job_status(
    job_id: str,
    current_user: SupervisorUser,
) -> dict:
    """
    Obtiene el estado de un job de procesamiento ML
    
    Útil para hacer polling y saber cuándo terminó el procesamiento.
    """
    try:
        status_info = queue_service.get_job_status(job_id)
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job no encontrado: {str(e)}"
        )


@router.get(
    "/queue/stats",
    summary="Estadísticas de la cola ML",
    description="Obtiene estadísticas de la cola de procesamiento ML (B-06)"
)
async def get_queue_stats(
    current_user: SupervisorUser,
) -> dict:
    """
    Obtiene estadísticas de la cola RQ
    
    Muestra trabajos encolados, en proceso, completados y fallidos.
    """
    try:
        stats = queue_service.get_queue_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.post(
    "/verify-image",
    summary="Verificar privacidad de imagen",
    description="""
    Analiza una imagen en busca de elementos sensibles (rostros, placas).

    **Uso:** Llamar antes de subir un reporte para advertir al usuario si la imagen
    contiene información que será anonimizada automáticamente por el servidor.

    **Nota:** Este endpoint NO modifica la imagen. La anonimización real ocurre al
    crear el reporte (POST /reportes).
    """
)
async def verify_image_privacy(
    current_user: ActiveUser,
    image: UploadFile = File(..., description="Imagen a verificar (JPG, PNG, WEBP)"),
):
    """
    Detecta rostros y placas en la imagen sin modificarla.
    Retorna advertencias si encuentra elementos sensibles.
    """
    import io
    import cv2
    import numpy as np
    from services.anonymizer import ImageAnonymizer

    # Validar tipo
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if image.content_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Formato no soportado: {image.content_type}",
        )

    # Leer bytes
    content = await image.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La imagen supera el límite de 10MB",
        )

    try:
        # Decodificar imagen para OpenCV
        arr = np.frombuffer(content, np.uint8)
        img_cv = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        if img_cv is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se pudo decodificar la imagen",
            )

        # Detectar elementos sensibles
        anonymizer = ImageAnonymizer()
        faces = anonymizer.detect_faces(img_cv)
        plates = (
            anonymizer.detect_plates_cascade(img_cv)
            if anonymizer.plate_cascade
            else anonymizer.detect_plates_basic(img_cv)
        )

        faces_count = len(faces)
        plates_count = len(plates)
        is_clean = faces_count == 0 and plates_count == 0

        regions = [
            {"type": r.type, "x": r.x, "y": r.y, "w": r.w, "h": r.h}
            for r in faces + plates
        ]

        warnings = []
        if faces_count:
            warnings.append(
                f"Se detectaron {faces_count} rostro(s). Serán difuminados automáticamente al enviar."
            )
        if plates_count:
            warnings.append(
                f"Se detectaron {plates_count} placa(s) vehicular(es). Serán difuminadas automáticamente al enviar."
            )

        return {
            "is_clean": is_clean,
            "faces_detected": faces_count,
            "plates_detected": plates_count,
            "regions": regions,
            "warnings": warnings,
            "message": (
                "La imagen no contiene elementos sensibles detectados."
                if is_clean
                else "La imagen contiene elementos sensibles que serán anonimizados automáticamente."
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        # Si falla la detección (ej. OpenCV no disponible), devolver resultado limpio con aviso
        return {
            "is_clean": True,
            "faces_detected": 0,
            "plates_detected": 0,
            "regions": [],
            "warnings": [],
            "message": "Verificación no disponible; la anonimización se aplicará en el servidor.",
            "error": str(e),
        }
