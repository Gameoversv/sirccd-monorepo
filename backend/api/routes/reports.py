"""
Rutas de Reportes - Gestión de reportes ciudadanos
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape

from db.session import get_db
from api.deps import get_current_active_user, ActiveUser, SupervisorUser, DbSession, require_supervisor
from models.user import User
from models.report import Report, ReportStatus, DamageType, SeverityLevel
from models.incident import Incident, IncidentStatus, PriorityLevel
from schemas.report import CreateReportResponse, ReportResponse, UpdateReportStatusRequest
from services.storage import storage_service
from services.queue_service import queue_service


def _public_url(url: str) -> str:
    """Convierte URLs internas de MinIO (minio:9000) a URLs accesibles por el browser (localhost:9000)"""
    if url and "minio:" in url:
        return url.replace("minio:", "localhost:", 1)
    return url
from services.ml_service import ml_service
from services.deduplication_service import get_deduplication_service
from services.priority_service import get_priority_service


router = APIRouter(prefix="/reportes", tags=["Reportes"])


def _resolve_focal_scale_factor(exif_data, fallback: Optional[float]) -> float:
    """Usa EXIF cuando hay focal; si no, usa el factor enviado por la app."""
    has_exif_focal = bool(exif_data.focal_length_35mm or exif_data.focal_length_mm)
    if has_exif_focal or fallback is None:
        return exif_data.zoom_scale_factor
    return max(0.25, min(2.0, float(fallback)))


def _resolve_incident_dedup(db, report, report_image, log):
    """
    Busca un Incident existente para fusionar con el reporte dado.
    Usa geo (30m) + visual gate (cosine similarity >= threshold).
    Fallback a geo-only si las imágenes no están disponibles.
    Retorna el Incident a fusionar, o None para crear uno nuevo.
    """
    from geoalchemy2.functions import ST_DWithin, ST_SetSRID, ST_MakePoint
    from geoalchemy2.shape import to_shape as _to_shape
    from services.deduplication_service import compute_visual_similarity, load_image_from_url
    from core.config import settings

    visual_gate = getattr(settings, "DEDUP_VISUAL_GATE_THRESHOLD", 0.60)

    try:
        pt = _to_shape(report.location)
        geo_candidates = (
            db.query(Incident)
            .filter(
                Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS]),
                ST_DWithin(
                    Incident.location,
                    ST_SetSRID(ST_MakePoint(pt.x, pt.y), 4326),
                    30.0,
                ),
            )
            .order_by(Incident.created_at.asc())
            .all()
        )
    except Exception as geo_err:
        log.warning("Error geo dedup: %s", geo_err)
        return None

    if not geo_candidates:
        return None

    # Sin imagen del reporte nuevo → no podemos verificar visualmente → crear nuevo incidente
    if report_image is None:
        log.info("Reporte %s: sin imagen para dedup visual → nuevo incidente", report.id)
        return None

    for candidate in geo_candidates:
        incident_img = load_image_from_url(candidate.before_image_url) if candidate.before_image_url else None

        if incident_img is None:
            # El incidente candidato no tiene imagen → no podemos verificar → saltar candidato
            log.info("Incidente %s sin imagen, saltando para reporte %s", candidate.id, report.id)
            continue

        similarity = compute_visual_similarity(report_image, incident_img)

        if similarity is None:
            # Embedder no disponible → saltar candidato
            log.warning("Visual check no disponible para reporte %s vs incidente %s, saltando", report.id, candidate.id)
            continue

        print(f" Dedup visual: reporte {report.id} vs incidente {candidate.id} sim={similarity:.3f} (gate={visual_gate})")

        if similarity >= visual_gate:
            log.info("Reporte %s → incidente %s (geo+visual, sim=%.3f)", report.id, candidate.id, similarity)
            return candidate
        else:
            log.info("Reporte %s ≠ incidente %s (sim=%.3f < %.3f)", report.id, candidate.id, similarity, visual_gate)

    return None


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
        import json as _json
        annotated_image_url = None
        model_precision = None
        model_recall = None
        model_map50 = None
        if r.detections_json:
            try:
                det = _json.loads(r.detections_json)
                annotated_image_url = det.get("annotated_image_url")
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
            "image_url": _public_url(r.image_url),
            "annotated_image_url": annotated_image_url,
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

        existing_incident = _resolve_incident_dedup(db, report, report_image_for_dedup, _log)

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
        
        # 3. Detección ML: siempre ejecutar inline (no hay worker RQ activo)
        job_id = None
        ml_ran_inline = False
        priority_service = get_priority_service(db)
        try:
            import tempfile, requests as _req
            from pathlib import Path

            # Resolver ruta local o descargar desde MinIO
            image_local_path = None
            _tmp_file = None

            if image_url.startswith("/storage/images/"):
                relative_path = image_url.replace("/storage/images/", "")
                backend_dir = Path(__file__).resolve().parent.parent.parent
                image_local_path = str(backend_dir / "storage" / "images" / relative_path)
            elif image_url.startswith("http"):
                # Descargar imagen desde MinIO usando el cliente autenticado
                from minio import Minio
                from core.config import settings as _cfg
                _mc = Minio(
                    _cfg.MINIO_ENDPOINT,
                    access_key=_cfg.MINIO_ACCESS_KEY,
                    secret_key=_cfg.MINIO_SECRET_KEY,
                    secure=_cfg.MINIO_SECURE,
                )
                # Extraer bucket y object key de la URL
                # URL format: http://minio:9000/bucket/object/key
                _url_path = image_url.split(_cfg.MINIO_ENDPOINT)[-1].lstrip("/")
                _bucket = _url_path.split("/")[0]
                _object_key = "/".join(_url_path.split("/")[1:])
                _tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                _tmp_file.close()
                _mc.fget_object(_bucket, _object_key, _tmp_file.name)
                image_local_path = _tmp_file.name

            if image_local_path:
                ml_focal_scale_factor = _resolve_focal_scale_factor(
                    exif_data,
                    focal_scale_factor,
                )
                print(
                    f" Ejecutando detección ML inline para reporte {new_report.id} "
                    f"(zoom_factor={ml_focal_scale_factor:.2f})"
                )
                result = ml_service.detect(
                    image_local_path,
                    focal_scale_factor=ml_focal_scale_factor,
                )
                dedup_image = None
                try:
                    from PIL import Image as _PILImage
                    dedup_image = _PILImage.open(image_local_path).convert("RGB")
                    print(f" Imagen cargada para dedup: {image_local_path}")
                except Exception as img_load_err:
                    print(f" Advertencia: no se pudo cargar imagen para deduplicación: {img_load_err}")
                    # Intentar cargar desde URL directamente
                    try:
                        from services.deduplication_service import load_image_from_url
                        dedup_image = load_image_from_url(new_report.image_url)
                        if dedup_image:
                            print(f" Imagen cargada desde URL para dedup")
                    except Exception:
                        pass

                # Generar imagen anotada con bounding boxes
                import json as _json, os as _os
                det_dict = result.to_dict()
                try:
                    backend_dir = Path(__file__).resolve().parent.parent.parent
                    ann_name = f"report_{new_report.id}_det.jpg"
                    annotated_local = str(backend_dir / "storage" / "images" / "annotated" / ann_name)
                    ml_service.annotate_image(image_local_path, result, annotated_local)
                    det_dict["annotated_image_url"] = f"/storage/images/annotated/{ann_name}"
                    print(f" Imagen anotada guardada: {ann_name}")
                except Exception as ann_err:
                    import traceback as _tb
                    print(f" Error generando imagen anotada: {ann_err}")
                    _tb.print_exc()
                finally:
                    # Limpiar archivo temporal si se descargó de MinIO
                    if _tmp_file and _os.path.exists(image_local_path):
                        _os.remove(image_local_path)

                new_report.damage_type = result.damage_type
                new_report.severity = result.severity
                new_report.confidence = result.confidence
                new_report.detections_json = _json.dumps(det_dict)
                new_report.status = ReportStatus.PENDING
                new_report.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(new_report)

                if dedup_image is not None:
                    try:
                        dedup_service = get_deduplication_service(db)
                        dedup_service.add_report_to_index(
                            report=new_report,
                            image=dedup_image,
                            description=description,
                        )
                    except Exception as dedup_err:
                        print(f" Advertencia: no se pudo indexar deduplicación para reporte {new_report.id}: {dedup_err}")

                damage_type = result.damage_type
                severity = result.severity
                confidence = result.confidence
                ml_ran_inline = True
                print(f" Detección inline: {result.damage_type.value} ({result.severity.value}) conf={result.confidence:.2f}")

                # Auto-aprobar si confianza >= 0.75
                AUTO_APPROVE_THRESHOLD = 0.75
                if result.confidence >= AUTO_APPROVE_THRESHOLD:
                    try:
                        new_report.status = ReportStatus.APPROVED
                        new_report.reviewed_at = datetime.utcnow()
                        db.commit()
                        db.refresh(new_report)

                        # Dedup geo+visual para auto-approve (dedup_image ya está en memoria)
                        import logging as _auto_log
                        existing_incident = _resolve_incident_dedup(
                            db, new_report, dedup_image, _auto_log.getLogger(__name__)
                        )
                        if existing_incident:
                            print(f" Auto-aprobado: reporte {new_report.id} → incidente existente {existing_incident.id}")
                            try:
                                pl, sc = priority_service.calculate_priority(existing_incident)
                                existing_incident.priority = pl
                                existing_incident.priority_score = sc
                                db.commit()
                            except Exception:
                                pass
                        else:
                            new_incident = Incident(
                                report_id=new_report.id,
                                reported_by=new_report.user_id,
                                location=new_report.location,
                                address=new_report.address,
                                city=new_report.city,
                                province=new_report.province,
                                damage_type=new_report.damage_type,
                                severity=new_report.severity,
                                priority=PriorityLevel.MEDIA,
                                priority_score=0.0,
                                status=IncidentStatus.OPEN,
                                before_image_url=new_report.image_url,
                                notes=new_report.description,
                            )
                            db.add(new_incident)
                            db.flush()
                            try:
                                pl, sc = priority_service.calculate_priority(new_incident)
                                new_incident.priority = pl
                                new_incident.priority_score = sc
                            except Exception:
                                pass
                            db.commit()
                            print(f" Auto-aprobado: reporte {new_report.id} → nuevo incidente {new_incident.id}")
                    except Exception as auto_err:
                        print(f" Error en auto-aprobación: {auto_err}")
                        db.rollback()

        except Exception as e:
            import traceback
            print(f" Error en detección ML: {e}")
            traceback.print_exc()
        
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
        image_url=_public_url(image_url),
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
        image_url=_public_url(report.image_url),
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
