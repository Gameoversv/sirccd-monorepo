"""
Rutas de Deduplicación (B-07) - Detección de reportes duplicados
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from PIL import Image
import io

from db.session import get_db
from api.deps import get_current_active_user, ActiveUser, SupervisorUser, DbSession
from services.deduplication_service import get_deduplication_service, DeduplicationService
from schemas.deduplication import (
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    SimilarReportsResponse,
    DeduplicationStats,
    IndexRebuildResponse,
    SpatialClusteringResponse,
    ClusterResolveRequest,
    ClusterResolveResponse,
)
from services.spatial_clustering_service import SpatialClusteringService, get_clustering_params as _clustering_params

router = APIRouter(prefix="/deduplication", tags=["Deduplicación"])


@router.post(
    "/check",
    response_model=DuplicateCheckResponse,
    summary="Verificar si un reporte es duplicado",
    description="""
    Determina si un nuevo reporte es duplicado de uno existente mediante:
    - **Similitud visual multimodelo**: ResNet/CLIP + FAISS
    - **Proximidad geográfica**: Distancia Haversine entre coordenadas
    - **Similitud textual**: comparación de descripciones (si se envía)
    
        **Estrategia:**
        - Se buscan los top-K reportes visualmente más similares por modelo
        - Se filtran por tipo de daño y ventana temporal
        - Se calcula score fusionado (visual + geo + texto)
        - Se considera duplicado por:
            * Reglas legacy (distancia visual y geográfica)
            * O score fusionado >= umbral configurado
    
    **Uso típico:** 
    Antes de crear un nuevo reporte, verificar si ya existe uno similar para evitar duplicados.
    """
)
async def check_duplicate(
    current_user: ActiveUser,
    db: DbSession,
    image: UploadFile = File(..., description="Imagen del reporte"),
    latitude: float = Form(..., description="Latitud WGS84"),
    longitude: float = Form(..., description="Longitud WGS84"),
    damage_type: str = Form(..., description="Tipo de daño (bache, grieta)"),
    description: Optional[str] = Form(None, description="Descripción textual opcional para score fusionado"),
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
            description=description,
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
    
    Retorna una lista ordenada por score fusionado que incluye:
    - ID del reporte
    - Distancias visuales por modelo
    - Distancia geográfica (metros)
    - Score fusionado
    - Metadatos del reporte original
    
    **Útil para:**
    - Análisis exploratorio
    - Validación manual de duplicados
    - Clustering de reportes relacionados
    """
)
async def find_similar_reports(
    current_user: ActiveUser,
    db: DbSession,
    image: UploadFile = File(..., description="Imagen del reporte"),
    latitude: float = Form(..., description="Latitud WGS84"),
    longitude: float = Form(..., description="Longitud WGS84"),
    damage_type: str = Form(..., description="Tipo de daño (bache, grieta)"),
    description: Optional[str] = Form(None, description="Descripción textual opcional para score fusionado"),
    top_k: int = Form(10, description="Número de resultados", ge=1, le=50),
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
            top_k=top_k,
            description=description,
        )
        
        # Formatear respuesta
        results = []
        for candidate in similar_reports:
            report = candidate.report
            from geoalchemy2.shape import to_shape
            point = to_shape(report.location)
            
            results.append({
                "report_id": report.id,
                "visual_distance": candidate.visual_distance,
                "visual_similarity": candidate.visual_similarity,
                "geo_distance": candidate.geo_distance,
                "geo_similarity": candidate.geo_similarity,
                "text_similarity": candidate.text_similarity,
                "fused_score": candidate.fused_score,
                "model_distances": candidate.model_distances,
                "model_similarities": candidate.model_similarities,
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
    
     **ADVERTENCIA:** Esta operación puede tardar varios minutos dependiendo 
    del número de reportes. El servicio seguirá funcionando durante la reconstrucción
    pero puede tener rendimiento degradado.
    
    **Requiere:** Permisos de administrador
    """
)
async def rebuild_index(
    current_user: SupervisorUser,
    db: DbSession,
    batch_size: int = Form(100, description="Tamaño de batch", ge=10, le=1000),
):
    """
    Reconstruye el índice FAISS
    
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
    current_user: ActiveUser,
    db: DbSession,
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
    current_user: SupervisorUser,
    db: DbSession,
):
    """
    Guarda el índice FAISS en disco

    Returns:
        Confirmación y ruta del archivo
    """
    try:

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


# ── M-13: Spatial Clustering ──────────────────────────────────────────────────

@router.get(
    "/clusters",
    response_model=SpatialClusteringResponse,
    summary="Detectar clusters espaciales de reportes duplicados (M-13)",
    description="""
    Ejecuta DBSCAN geoespacial sobre todos los reportes activos y agrupa los que
    reportan el mismo daño físico.

    **Diferencia con /check (M-11):**
    - `/check` evalúa si UN reporte nuevo es duplicado de uno existente.
    - `/clusters` analiza TODA la base de datos y encuentra grupos de reportes
      que ya existen y describen el mismo daño.

    **Algoritmo:** DBSCAN con métrica Haversine.
    - `eps_meters`: radio máximo para que dos reportes sean vecinos.
    - `min_samples`: mínimo de reportes para formar un cluster.
    - Reportes fuera de cualquier cluster se clasifican como *noise*.

    **Uso típico:**
    - Revisión periódica del dashboard para detectar acumulaciones de reportes.
    - Antes de ejecutar `/clusters/resolve` para limpiar duplicados en batch.
    """,
)
async def get_spatial_clusters(
    current_user: ActiveUser,
    db: DbSession,
    eps_meters: Optional[float] = None,
    min_samples: Optional[int] = None,
    damage_type: Optional[str] = None,
    time_window_days: Optional[int] = None,
):
    try:
        eps, minsamp, window = _clustering_params(db, eps_meters, min_samples, time_window_days)
        svc = SpatialClusteringService(
            db=db,
            eps_meters=eps,
            min_samples=minsamp,
            time_window_days=window,
        )
        result = svc.compute_clusters(damage_type=damage_type)

        return {
            "clusters": [
                {
                    "cluster_id": c.cluster_id,
                    "primary_report_id": c.primary_report_id,
                    "member_count": c.member_count,
                    "centroid_lat": c.centroid_lat,
                    "centroid_lon": c.centroid_lon,
                    "damage_type": c.damage_type,
                    "radius_m": c.radius_m,
                    "members": [
                        {
                            "report_id": m.report_id,
                            "latitude": m.latitude,
                            "longitude": m.longitude,
                            "damage_type": m.damage_type,
                            "severity": m.severity,
                            "confidence": m.confidence,
                            "status": m.status,
                            "created_at": m.created_at,
                            "is_primary": m.is_primary,
                        }
                        for m in c.members
                    ],
                    "oldest_report_at": c.oldest_report_at,
                    "newest_report_at": c.newest_report_at,
                }
                for c in result.clusters
            ],
            "noise_report_ids": result.noise_report_ids,
            "total_reports_analyzed": result.total_reports_analyzed,
            "total_clustered": result.total_clustered,
            "total_noise": result.total_noise,
            "eps_meters": result.eps_meters,
            "min_samples": result.min_samples,
            "damage_type_filter": result.damage_type_filter,
            "time_window_days": result.time_window_days,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ejecutando clustering espacial: {str(e)}",
        )


@router.post(
    "/clusters/resolve",
    response_model=ClusterResolveResponse,
    summary="Resolver cluster: marcar duplicados como rechazados (M-13)",
    description="""
    Dado un `cluster_id` retornado por `/clusters`, marca todos los reportes
    **no-primarios** del cluster como `REJECTED` con razón de rechazo automática.

    El **reporte primario** se determina por mayor confianza ML; en empate,
    el más antiguo prevalece.

    **Requiere:** Permisos de supervisor.
    """,
)
async def resolve_cluster(
    body: ClusterResolveRequest,
    current_user: SupervisorUser,
    db: DbSession,
):
    try:
        eps, minsamp, window = _clustering_params(db, body.eps_meters, body.min_samples, body.time_window_days)
        svc = SpatialClusteringService(
            db=db,
            eps_meters=eps,
            min_samples=minsamp,
            time_window_days=window,
        )
        result = svc.resolve_cluster(
            cluster_id=body.cluster_id,
            damage_type=body.damage_type,
        )

        return {
            "primary_report_id": result["primary_report_id"],
            "resolved_ids": result["resolved_ids"],
            "skipped_ids": result["skipped_ids"],
            "clusters_processed": None,
            "total_resolved": None,
            "cluster_summaries": None,
            "message": result["message"],
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resolviendo cluster: {str(e)}",
        )


@router.post(
    "/clusters/resolve-all",
    response_model=ClusterResolveResponse,
    summary="Resolver todos los clusters en batch (M-13)",
    description="""
    Resuelve **todos** los clusters detectados de una sola operación.

    Útil para limpieza periódica de la BD. Cada cluster conserva su reporte
    primario; el resto se marca como `REJECTED`.

    **Requiere:** Permisos de supervisor.
    """,
)
async def resolve_all_clusters(
    current_user: SupervisorUser,
    db: DbSession,
    eps_meters: Optional[float] = None,
    min_samples: Optional[int] = None,
    damage_type: Optional[str] = None,
    time_window_days: Optional[int] = None,
    min_cluster_size: int = 2,
):
    try:
        eps, minsamp, window = _clustering_params(db, eps_meters, min_samples, time_window_days)
        svc = SpatialClusteringService(
            db=db,
            eps_meters=eps,
            min_samples=minsamp,
            time_window_days=window,
        )
        result = svc.resolve_all_clusters(
            damage_type=damage_type,
            min_cluster_size=min_cluster_size,
        )

        return {
            "primary_report_id": None,
            "resolved_ids": result["resolved_ids"],
            "skipped_ids": [],
            "clusters_processed": result["clusters_processed"],
            "total_resolved": result["total_resolved"],
            "cluster_summaries": result["cluster_summaries"],
            "message": (
                f"{result['clusters_processed']} clusters procesados, "
                f"{result['total_resolved']} reportes marcados como duplicados"
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en resolución batch: {str(e)}",
        )
