"""
Tasks RQ - Cola de tareas para procesamiento en segundo plano
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Agregar el directorio backend al path para imports
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.report import Report, ReportStatus
from services.ml_service import ml_service
from services.deduplication_service import get_deduplication_service

logger = logging.getLogger(__name__)


def process_report_ml_detection(report_id: int, image_local_path: str) -> dict:
    """
    Task RQ: Procesa detección ML para un reporte
    
    Esta función es ejecutada por el worker RQ en segundo plano.
    
    Args:
        report_id: ID del reporte a procesar
        image_local_path: Ruta local a la imagen
    
    Returns:
        dict: Resultado de la detección
        {
            "report_id": int,
            "success": bool,
            "damage_type": str,
            "severity": str,
            "confidence": float,
            "detections_json": str,
            "error": Optional[str]
        }
    """
    logger.info(f" [Task] Procesando reporte ID={report_id}")
    
    db: Optional[Session] = None
    
    try:
        # Crear sesión de BD
        db = SessionLocal()
        
        # Buscar reporte
        report = db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            error_msg = f"Reporte {report_id} no encontrado"
            logger.error(f" {error_msg}")
            return {
                "report_id": report_id,
                "success": False,
                "error": error_msg
            }
        
        # Actualizar estado a PROCESSING
        report.status = ReportStatus.PROCESSING
        db.commit()
        logger.info(f" Reporte {report_id} marcado como PROCESSING")
        
        # Verificar que la imagen existe
        if not os.path.exists(image_local_path):
            error_msg = f"Imagen no encontrada: {image_local_path}"
            logger.error(f" {error_msg}")
            
            # Marcar como error
            report.status = ReportStatus.PENDING
            db.commit()
            
            return {
                "report_id": report_id,
                "success": False,
                "error": error_msg
            }
        
        # Ejecutar detección ML
        logger.info(f" Ejecutando inferencia ML...")
        detection_result = ml_service.detect(image_local_path)

        dedup_image = None
        try:
            from PIL import Image as _PILImage
            dedup_image = _PILImage.open(image_local_path).convert("RGB")
        except Exception as img_err:
            logger.warning(f"No se pudo cargar imagen para deduplicación report_id={report_id}: {img_err}")
        
        # Actualizar reporte con resultados
        report.damage_type = detection_result.damage_type
        report.severity = detection_result.severity
        report.confidence = detection_result.confidence
        report.detections_json = detection_result.to_json()
        report.status = ReportStatus.PENDING  # Volver a pending para revisión humana
        
        db.commit()

        if dedup_image is not None:
            try:
                dedup_service = get_deduplication_service(db)
                dedup_service.add_report_to_index(
                    report=report,
                    image=dedup_image,
                    description=report.description,
                )
            except Exception as dedup_err:
                logger.warning(f"No se pudo indexar deduplicación report_id={report_id}: {dedup_err}")
        
        logger.info(
            f" [Task] Reporte {report_id} procesado exitosamente: "
            f"{detection_result.damage_type.value} ({detection_result.severity.value}) "
            f"- {len(detection_result.bounding_boxes)} detecciones"
        )
        
        return {
            "report_id": report_id,
            "success": True,
            "damage_type": detection_result.damage_type.value,
            "severity": detection_result.severity.value,
            "confidence": detection_result.confidence,
            "detections_json": detection_result.to_json(),
            "num_detections": len(detection_result.bounding_boxes),
        }
        
    except Exception as e:
        logger.error(f" [Task] Error procesando reporte {report_id}: {e}", exc_info=True)
        
        # Intentar actualizar estado del reporte
        if db:
            try:
                report = db.query(Report).filter(Report.id == report_id).first()
                if report:
                    report.status = ReportStatus.PENDING
                    db.commit()
            except Exception:
                pass
        
        return {
            "report_id": report_id,
            "success": False,
            "error": str(e)
        }
        
    finally:
        if db:
            db.close()


def test_task(message: str) -> dict:
    """
    Task de prueba para verificar que RQ funciona
    
    Args:
        message: Mensaje de prueba
    
    Returns:
        dict con el resultado
    """
    logger.info(f" [Test Task] Mensaje recibido: {message}")
    
    return {
        "success": True,
        "message": f"Task procesada: {message}",
        "worker": os.getpid()
    }
