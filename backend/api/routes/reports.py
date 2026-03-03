"""
Rutas de Reportes - Gestión de reportes ciudadanos
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

from db.session import get_db
from api.deps import get_current_active_user, ActiveUser
from models.report import Report, ReportStatus, DamageType, SeverityLevel
from schemas.report import CreateReportResponse, ReportResponse
from services.storage import storage_service
from services.queue_service import queue_service


router = APIRouter(prefix="/reportes", tags=["Reportes"])


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
    
    # Dependencias
    db: Session = Depends(get_db),
    current_user: ActiveUser = None  # ActiveUser ya incluye Depends
) -> CreateReportResponse:
    """
    Crea un nuevo reporte con imagen, GPS y descripción
    """
    
    # 1. Validar y subir imagen (con anonimización automática B-05)
    try:
        image_url, image_width, image_height, anonymization_stats = await storage_service.upload_image(
            file=image,
            folder="reports",
            anonymize=True  # B-05: SIEMPRE anonimizar antes de guardar
        )
        
        # Log de anonimización
        if anonymization_stats.get('anonymized'):
            print(f"🔒 Imagen anonimizada: {anonymization_stats['regions_blurred']} regiones "
                  f"({anonymization_stats['faces_detected']} rostros, {anonymization_stats['plates_detected']} placas)")
    
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
        # Formato WKT: POINT(longitude latitude) - nota el orden!
        location_wkt = f"POINT({longitude} {latitude})"
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
        
        # 3. Encolar tarea de detección ML (B-06: procesamiento asíncrono)
        job_id = None
        try:
            # Construir ruta local a la imagen
            # Formato de image_url: "/storage/images/reports/2026/03/03/abc123_file.jpg"
            from pathlib import Path
            
            if image_url.startswith("/storage/images/"):
                # Extraer ruta relativa
                relative_path = image_url.replace("/storage/images/", "")
                
                # Construir ruta absoluta (backend/storage/images/...)
                backend_dir = Path(__file__).resolve().parent.parent.parent
                image_local_path = str(backend_dir / "storage" / "images" / relative_path)
                
                # Encolar job para procesamiento ML
                job = queue_service.enqueue_ml_detection(
                    report_id=new_report.id,
                    image_local_path=image_local_path
                )
                
                if job:
                    job_id = job.id
                    print(f"✅ Job ML encolado: {job_id} para reporte {new_report.id}")
                else:
                    print(f"⚠️ No se pudo encolar job ML para reporte {new_report.id}")
            
        except Exception as e:
            # Si falla el encolado, no bloquear la creación del reporte
            print(f"⚠️ Error al encolar job ML: {e}")
            # El reporte queda en PROCESSING, puede reprocesarse manualmente
        
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
        status=ReportStatus.PROCESSING,
        damage_type=damage_type,  # Placeholder
        severity=severity,  # Placeholder
        confidence=confidence,  # 0.0 hasta que se procese
        image_url=image_url,
        latitude=latitude,
        longitude=longitude,
        description=description,
        created_at=new_report.created_at,
        job_id=job_id  # B-06: ID del job RQ para seguimiento
    )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Obtener reporte por ID",
    description="Obtiene los detalles completos de un reporte específico"
)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: ActiveUser = None  # ActiveUser ya incluye Depends
) -> ReportResponse:
    """Obtiene un reporte por su ID"""
    
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reporte {report_id} no encontrado"
        )
    
    # Extraer coordenadas del campo Geography
    # report.location es un WKBElement, necesitamos convertirlo
    from geoalchemy2.shape import to_shape
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
        image_url=report.image_url,
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
    current_user: ActiveUser = None
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
    current_user: ActiveUser = None
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
