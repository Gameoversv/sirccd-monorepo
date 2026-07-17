"""
Procesamiento posterior de un reporte: deteccion ML, imagen anotada,
indexado de deduplicacion y auto-aprobacion con creacion/fusion de incidentes.

Vive fuera de la ruta HTTP para que lo pueda ejecutar el worker RQ. La ruta
solo encola; nada de esto corre dentro de la peticion del usuario.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from typing import Optional

from PIL import Image
from sqlalchemy.orm import Session

from core.config import settings
from models.incident import Incident, IncidentStatus, PriorityLevel
from models.report import Report, ReportStatus
from services.deduplication_service import (
    compute_visual_similarity,
    get_deduplication_service,
    load_image_from_url,
)
from services.ml_service import ml_service
from services.priority_service import get_priority_service
from services.storage import storage_service

logger = logging.getLogger(__name__)

AUTO_APPROVE_THRESHOLD = 0.75
GEO_DEDUP_RADIUS_METERS = 30.0


def resolve_incident_dedup(
    db: Session,
    report: Report,
    report_image: Optional[Image.Image],
) -> Optional[Incident]:
    """
    Busca un Incident existente para fusionar con el reporte dado.

    Usa geo (30m) + gate visual (similitud coseno >= umbral). Devuelve el
    Incident a fusionar, o None para crear uno nuevo.
    """
    from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
    from geoalchemy2.shape import to_shape

    visual_gate = getattr(settings, "DEDUP_VISUAL_GATE_THRESHOLD", 0.60)

    try:
        point = to_shape(report.location)
        geo_candidates = (
            db.query(Incident)
            .filter(
                Incident.status.in_(
                    [IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS]
                ),
                ST_DWithin(
                    Incident.location,
                    ST_SetSRID(ST_MakePoint(point.x, point.y), 4326),
                    GEO_DEDUP_RADIUS_METERS,
                ),
            )
            .order_by(Incident.created_at.asc())
            .all()
        )
    except Exception as geo_err:
        logger.warning("Error geo dedup: %s", geo_err)
        return None

    if not geo_candidates:
        return None

    # Sin imagen no se puede verificar visualmente: mejor crear incidente nuevo
    # que fusionar a ciegas por cercania.
    if report_image is None:
        logger.info(
            "Reporte %s: sin imagen para dedup visual, nuevo incidente",
            report.id,
        )
        return None

    for candidate in geo_candidates:
        incident_img = (
            load_image_from_url(candidate.before_image_url)
            if candidate.before_image_url
            else None
        )
        if incident_img is None:
            logger.info(
                "Incidente %s sin imagen, saltando para reporte %s",
                candidate.id,
                report.id,
            )
            continue

        similarity = compute_visual_similarity(report_image, incident_img)
        if similarity is None:
            logger.warning(
                "Visual check no disponible para reporte %s vs incidente %s",
                report.id,
                candidate.id,
            )
            continue

        if similarity >= visual_gate:
            logger.info(
                "Reporte %s -> incidente %s (geo+visual, sim=%.3f)",
                report.id,
                candidate.id,
                similarity,
            )
            return candidate

        logger.info(
            "Reporte %s != incidente %s (sim=%.3f < %.3f)",
            report.id,
            candidate.id,
            similarity,
            visual_gate,
        )

    return None


def _resolve_local_image(image_url: str) -> tuple[Optional[str], bool]:
    """
    Deja la imagen del reporte en disco local y devuelve (ruta, es_temporal).

    El worker corre en otro contenedor que el backend, asi que las imagenes en
    MinIO hay que bajarlas; no se puede asumir un /tmp compartido.
    """
    from pathlib import Path

    if image_url.startswith("/storage/images/"):
        relative = image_url.replace("/storage/images/", "")
        backend_dir = Path(__file__).resolve().parent.parent
        local = backend_dir / "storage" / "images" / relative
        return (str(local), False) if local.exists() else (None, False)

    content = storage_service.download_image_bytes(image_url)
    if content is None:
        return None, False

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    try:
        tmp.write(content)
    finally:
        tmp.close()
    return tmp.name, True


def _store_annotated_image(report_id: int, image_path: str, result) -> Optional[str]:
    """
    Genera la imagen anotada y la sube al almacenamiento compartido.

    Va a MinIO y no al disco local porque quien la genera es el worker: un
    archivo escrito en su contenedor no lo puede servir el backend.
    """
    annotated_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    annotated_tmp.close()
    try:
        ml_service.annotate_image(image_path, result, annotated_tmp.name)
        with open(annotated_tmp.name, "rb") as fh:
            content = fh.read()
        return storage_service.upload_bytes(
            f"annotated/report_{report_id}_det.jpg", content
        )
    except Exception as err:
        logger.warning("No se pudo generar imagen anotada de %s: %s", report_id, err)
        return None
    finally:
        if os.path.exists(annotated_tmp.name):
            os.remove(annotated_tmp.name)


def _auto_approve(db: Session, report: Report, dedup_image: Optional[Image.Image]) -> None:
    """Aprueba el reporte y lo fusiona con un incidente existente o crea uno."""
    priority_service = get_priority_service(db)

    report.status = ReportStatus.APPROVED
    report.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(report)

    existing = resolve_incident_dedup(db, report, dedup_image)
    if existing:
        # Persistir la membresía: el reporte fusionado apunta al reporte primario
        # del incidente. Así el incidente puede listar todos sus reportes
        # (original + detección) sin buscarlos en la pestaña de reportes.
        report.duplicate_of_report_id = existing.report_id
        logger.info(
            "Auto-aprobado: reporte %s -> incidente existente %s (duplicado de reporte %s)",
            report.id,
            existing.id,
            existing.report_id,
        )
        incident = existing
    else:
        incident = Incident(
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
        db.add(incident)
        db.flush()
        logger.info(
            "Auto-aprobado: reporte %s -> nuevo incidente %s", report.id, incident.id
        )

    try:
        level, score = priority_service.calculate_priority(incident)
        incident.priority = level
        incident.priority_score = score
    except Exception as prio_err:
        logger.warning("No se pudo calcular prioridad de %s: %s", incident.id, prio_err)

    db.commit()


def process_report_detection(
    db: Session,
    report_id: int,
    focal_scale_factor: Optional[float] = None,
) -> dict:
    """
    Ejecuta el pipeline completo de deteccion sobre un reporte ya persistido.

    [focal_scale_factor] se resuelve en la capa HTTP, donde todavia existe el
    EXIF: la imagen almacenada va sin metadatos (D-08), asi que aqui ya no se
    puede recuperar la focal.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"report_id": report_id, "success": False, "error": "Reporte no encontrado"}

    image_path, is_temp = _resolve_local_image(report.image_url)
    if not image_path:
        report.status = ReportStatus.PENDING
        db.commit()
        return {
            "report_id": report_id,
            "success": False,
            "error": f"No se pudo resolver la imagen: {report.image_url}",
        }

    try:
        report.status = ReportStatus.PROCESSING
        db.commit()

        logger.info(
            "Detectando en reporte %s (zoom_factor=%.2f)",
            report_id,
            focal_scale_factor or 1.0,
        )
        result = ml_service.detect(image_path, focal_scale_factor=focal_scale_factor)

        dedup_image = None
        try:
            dedup_image = Image.open(image_path).convert("RGB")
        except Exception as img_err:
            logger.warning(
                "No se pudo cargar imagen para dedup de %s: %s", report_id, img_err
            )

        detections = result.to_dict()
        annotated_url = _store_annotated_image(report_id, image_path, result)
        if annotated_url:
            detections["annotated_image_url"] = annotated_url

        report.damage_type = result.damage_type
        report.severity = result.severity
        report.confidence = result.confidence
        report.detections_json = json.dumps(detections)
        report.status = ReportStatus.PENDING
        report.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(report)

        if dedup_image is not None:
            try:
                get_deduplication_service(db).add_report_to_index(
                    report=report,
                    image=dedup_image,
                    description=report.description,
                )
            except Exception as dedup_err:
                logger.warning(
                    "No se pudo indexar dedup de %s: %s", report_id, dedup_err
                )

        logger.info(
            "Reporte %s: %s (%s) conf=%.2f",
            report_id,
            result.damage_type.value,
            result.severity.value,
            result.confidence,
        )

        if result.confidence >= AUTO_APPROVE_THRESHOLD:
            try:
                _auto_approve(db, report, dedup_image)
            except Exception as auto_err:
                logger.error("Error en auto-aprobacion de %s: %s", report_id, auto_err)
                db.rollback()

        return {
            "report_id": report_id,
            "success": True,
            "damage_type": result.damage_type.value,
            "severity": result.severity.value,
            "confidence": result.confidence,
            "num_detections": len(result.bounding_boxes),
        }

    except Exception as err:
        logger.error("Error procesando reporte %s: %s", report_id, err, exc_info=True)
        db.rollback()
        try:
            report.status = ReportStatus.PENDING
            db.commit()
        except Exception:
            db.rollback()
        return {"report_id": report_id, "success": False, "error": str(err)}

    finally:
        if is_temp and os.path.exists(image_path):
            os.remove(image_path)
