"""
Rutas de Deduplicación (B-07) - Detección de reportes duplicados
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from PIL import Image
import io

from db.session import get_db
from api.deps import get_current_active_user, ActiveUser
from services.deduplication_service import get_deduplication_service, DeduplicationService
from schemas.deduplication import (
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    SimilarReportsResponse,
    DeduplicationStats,
    IndexRebuildResponse
)

router = APIRouter(prefix="/deduplication", tags=["Deduplicación"])


@router.post(
    "/check",
    response_model=DuplicateCheckResponse,
    summary="Verificar si un reporte es duplicado",
    description="""
    Determina si un nuevo reporte es duplicado de uno existente mediante:
    - **Similitud visual**: Comparación de embeddings de imágenes usando ResNet50 + FAISS
    - **Proximidad geográfica**: Distancia Haversine entre coordenadas
    
    **Estrategia:**
    - Se buscan los top-K reportes visualmente más similares
    - Se filtran por tipo de daño y ventana temporal
    - Se verifica proximidad geográfica
    - Se considera duplicado si AMBOS criterios se cumplen:
      * Distancia visual < umbral (default: 0.15)
      * Distancia geográfica < umbral (default: 50m)
    
    **Uso típico:** 
    Antes de crear un nuevo reporte, verificar si ya existe uno similar para evitar duplicados.
    """
)
async def check_duplicate(
    image: UploadFile = File(..., description="Imagen del reporte"),
    latitude: float = Form(..., description="Latitud WGS84"),
    longitude: float = Form(..., description="Longitud WGS84"),
    damage_type: str = Form(..., description="Tipo de daño (bache, grieta)"),
    visual_threshold: Optional[float] = Form(
        None, 
        description="Umbral de similitud visual (default: 0.15)",
        ge=0.0,
        le=1.0
    ),
    geo_threshold: Optional[float] = Form(
        None,
        description="Umbral de distancia geográfica en metros (default: 50.0)",
        ge=0.0
    ),
    current_user: ActiveUser = None,
    db: Session = Depends(get_db)
):
    """
    Verifica si un reporte es duplicado
    
    Returns:
        DuplicateCheckResponse con:
        - is_duplicate: bool
        - original_report_id: int (si es duplicado)
        - metadata: dict con distancias y umbrales
    """
    try:
        # Cargar imagen
        image_data = await image.read()
        img = Image.open(io.BytesIO(image_data))
        
        # Obtener servicio de deduplicación
        dedup_service = get_deduplication_service(db)
        
        # Verificar duplicado
        is_duplicate, original_report, metadata = dedup_service.is_duplicate(
            image=img,
            latitude=latitude,
            longitude=longitude,
            damage_type=damage_type,
            visual_threshold=visual_threshold,
            geo_threshold=geo_threshold
        )
        
        # Preparar respuesta
        response = {
            "is_duplicate": is_duplicate,
            "original_report_id": original_report.id if original_report else None,
            "metadata": metadata
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verificando duplicado: {str(e)}"
        )


@router.post(
    "/similar",
    response_model=SimilarReportsResponse,
    summary="Buscar reportes similares",
    description="""
    Encuentra los reportes más similares a una imagen y ubicación dadas.
    
    Retorna una lista ordenada por similitud visual que incluye:
    - ID del reporte
    - Distancia visual (L2 en espacio de embeddings)
    - Distancia geográfica (metros)
    - Metadatos del reporte original
    
    **Útil para:**
    - Análisis exploratorio
    - Validación manual de duplicados
    - Clustering de reportes relacionados
    """
)
async def find_similar_reports(
    image: UploadFile = File(..., description="Imagen del reporte"),
    latitude: float = Form(..., description="Latitud WGS84"),
    longitude: float = Form(..., description="Longitud WGS84"),
    damage_type: str = Form(..., description="Tipo de daño (bache, grieta)"),
    top_k: int = Form(10, description="Número de resultados", ge=1, le=50),
    current_user: ActiveUser = None,
    db: Session = Depends(get_db)
):
    """
    Busca reportes similares
    
    Returns:
        Lista de reportes similares con distancias
    """
    try:
        # Cargar imagen
        image_data = await image.read()
        img = Image.open(io.BytesIO(image_data))
        
        # Obtener servicio de deduplicación
        dedup_service = get_deduplication_service(db)
        
        # Buscar similares
        similar_reports = dedup_service.find_similar_reports(
            image=img,
            latitude=latitude,
            longitude=longitude,
            damage_type=damage_type,
            top_k=top_k
        )
        
        # Formatear respuesta
        results = []
        for report, visual_dist, geo_dist in similar_reports:
            from geoalchemy2.shape import to_shape
            point = to_shape(report.location)
            
            results.append({
                "report_id": report.id,
                "visual_distance": visual_dist,
                "geo_distance": geo_dist,
                "damage_type": report.damage_type.value,
                "severity": report.severity.value,
                "confidence": report.confidence,
                "latitude": point.y,
                "longitude": point.x,
                "created_at": report.created_at.isoformat(),
                "status": report.status.value
            })
        
        return {
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error buscando similares: {str(e)}"
        )


@router.post(
    "/index/rebuild",
    response_model=IndexRebuildResponse,
    summary="Reconstruir índice FAISS",
    description="""
    Reconstruye el índice FAISS desde cero usando todos los reportes aprobados.
    
    **Cuándo usar:**
    - Inicialización del sistema
    - Después de actualizar el modelo de embeddings
    - Recuperación de corrupción del índice
    - Después de importar muchos reportes históricos
    
    ⚠️ **ADVERTENCIA:** Esta operación puede tardar varios minutos dependiendo 
    del número de reportes. El servicio seguirá funcionando durante la reconstrucción
    pero puede tener rendimiento degradado.
    
    **Requiere:** Permisos de administrador
    """
)
async def rebuild_index(
    batch_size: int = Form(100, description="Tamaño de batch", ge=10, le=1000),
    current_user: ActiveUser = None,
    db: Session = Depends(get_db)
):
    """
    Reconstruye el índice FAISS
    
    TODO: Agregar verificación de permisos de admin
    
    Returns:
        Estadísticas de la reconstrucción
    """
    try:
        # TODO: Verificar que el usuario sea admin
        # if not current_user.is_admin:
        #     raise HTTPException(403, "Requiere permisos de administrador")
        
        # Obtener servicio
        dedup_service = get_deduplication_service(db)
        
        # Reconstruir índice
        dedup_service.rebuild_index(batch_size=batch_size)
        
        # Obtener estadísticas
        stats = dedup_service.get_statistics()
        
        return {
            "success": True,
            "message": "Índice reconstruido exitosamente",
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reconstruyendo índice: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=DeduplicationStats,
    summary="Obtener estadísticas del servicio",
    description="""
    Retorna estadísticas del servicio de deduplicación:
    - Tamaño del índice (número de reportes indexados)
    - Dimensión de embeddings
    - Umbrales configurados
    - Ventana temporal
    """
)
async def get_stats(
    current_user: ActiveUser = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas del servicio
    
    Returns:
        Estadísticas de configuración y estado
    """
    try:
        dedup_service = get_deduplication_service(db)
        stats = dedup_service.get_statistics()
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.post(
    "/index/save",
    summary="Guardar índice FAISS en disco",
    description="""
    Persiste el índice FAISS actual en disco.
    
    Útil para:
    - Backup del índice
    - Preservar estado antes de mantenimiento
    - Compartir índice entre instancias
    
    **Requiere:** Permisos de administrador
    """
)
async def save_index(
    current_user: ActiveUser = None,
    db: Session = Depends(get_db)
):
    """
    Guarda el índice FAISS en disco
    
    Returns:
        Confirmación y ruta del archivo
    """
    try:
        # TODO: Verificar permisos de admin
        
        from core.config import settings
        index_path = getattr(settings, 'FAISS_INDEX_PATH', './storage/faiss_index.bin')
        
        dedup_service = get_deduplication_service(db)
        dedup_service.save_index(index_path)
        
        return {
            "success": True,
            "message": "Índice guardado exitosamente",
            "path": index_path
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error guardando índice: {str(e)}"
        )
