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
from services.report_processing_service import process_report_detection

logger = logging.getLogger(__name__)


def process_report_ml_detection(
    report_id: int,
    focal_scale_factor: Optional[float] = None,
) -> dict:
    """
    Task RQ: procesa la detección ML de un reporte en segundo plano.

    La imagen no se pasa por argumento: el worker corre en otro contenedor que
    la API, asi que no comparten /tmp. process_report_detection la resuelve
    desde report.image_url (MinIO o disco local).

    Args:
        report_id: ID del reporte a procesar
        focal_scale_factor: Factor de zoom ya resuelto por la capa HTTP, donde
            todavia existe el EXIF (la imagen almacenada va sin metadatos).

    Returns:
        dict con el resultado de la detección
    """
    logger.info(f"[Task] Procesando reporte ID={report_id}")

    db: Optional[Session] = None
    try:
        db = SessionLocal()
        return process_report_detection(
            db,
            report_id=report_id,
            # El factor termina en `focal_scale_factor ** 2` al evaluar la
            # severidad: un None (job encolado sin EXIF resuelto) reventaría la
            # detección entera, así que se normaliza al valor neutro.
            focal_scale_factor=focal_scale_factor if focal_scale_factor is not None else 1.0,
        )
    except Exception as e:
        logger.error(f"[Task] Error procesando reporte {report_id}: {e}", exc_info=True)
        return {"report_id": report_id, "success": False, "error": str(e)}
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
