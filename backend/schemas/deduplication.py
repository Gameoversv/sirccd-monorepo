"""
Schemas de Deduplicación (B-07)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DuplicateCheckRequest(BaseModel):
    """Request para verificar duplicados"""
    # Nota: image se maneja como UploadFile en el endpoint
    latitude: float = Field(..., description="Latitud WGS84", ge=-90, le=90)
    longitude: float = Field(..., description="Longitud WGS84", ge=-180, le=180)
    damage_type: str = Field(..., description="Tipo de daño (bache, grieta)")
    visual_threshold: Optional[float] = Field(None, description="Umbral visual", ge=0, le=1)
    geo_threshold: Optional[float] = Field(None, description="Umbral geográfico (metros)", ge=0)


class DuplicateCheckResponse(BaseModel):
    """Response de verificación de duplicados"""
    is_duplicate: bool = Field(..., description="Si es un duplicado")
    original_report_id: Optional[int] = Field(None, description="ID del reporte original si es duplicado")
    metadata: Dict[str, Any] = Field(..., description="Metadatos de la verificación")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "is_duplicate": True,
                    "original_report_id": 123,
                    "metadata": {
                        "reason": "duplicate_found",
                        "decision_mode": "fusion_score",
                        "visual_distance": 0.08,
                        "visual_similarity": 0.96,
                        "geo_distance": 25.5,
                        "geo_similarity": 0.60,
                        "text_similarity": 0.74,
                        "fused_score": 0.84,
                        "fusion_threshold": 0.72,
                        "model_distances": {
                            "resnet50": 0.08,
                            "clip-vit-base-patch32": 0.12
                        },
                        "model_similarities": {
                            "resnet50": 0.96,
                            "clip-vit-base-patch32": 0.94
                        },
                        "age_days": 5,
                        "visual_threshold": 0.15,
                        "geo_threshold": 50.0
                    }
                },
                {
                    "is_duplicate": False,
                    "original_report_id": None,
                    "metadata": {
                        "reason": "no_duplicate",
                        "closest_report_id": 456,
                        "visual_distance": 0.22,
                        "visual_similarity": 0.89,
                        "geo_distance": 15.3,
                        "geo_similarity": 0.74,
                        "text_similarity": 0.31,
                        "fused_score": 0.58,
                        "fusion_threshold": 0.72,
                        "visual_threshold": 0.15,
                        "geo_threshold": 50.0
                    }
                }
            ]
        }
    }


class SimilarReport(BaseModel):
    """Reporte similar encontrado"""
    report_id: int = Field(..., description="ID del reporte")
    visual_distance: float = Field(..., description="Distancia visual L2")
    visual_similarity: Optional[float] = Field(None, description="Similitud visual primaria normalizada [0,1]")
    geo_distance: float = Field(..., description="Distancia geográfica en metros")
    geo_similarity: Optional[float] = Field(None, description="Similitud geográfica normalizada [0,1]")
    text_similarity: Optional[float] = Field(None, description="Similitud textual normalizada [0,1]")
    fused_score: Optional[float] = Field(None, description="Score fusionado multimodal [0,1]")
    model_distances: Optional[Dict[str, float]] = Field(None, description="Distancias por modelo visual")
    model_similarities: Optional[Dict[str, float]] = Field(None, description="Similitudes por modelo visual")
    damage_type: str = Field(..., description="Tipo de daño")
    severity: str = Field(..., description="Nivel de severidad")
    confidence: float = Field(..., description="Confianza de detección ML")
    latitude: float = Field(..., description="Latitud")
    longitude: float = Field(..., description="Longitud")
    created_at: str = Field(..., description="Fecha de creación (ISO 8601)")
    status: str = Field(..., description="Estado del reporte")


class SimilarReportsResponse(BaseModel):
    """Response de búsqueda de reportes similares"""
    count: int = Field(..., description="Número de resultados")
    results: List[SimilarReport] = Field(..., description="Lista de reportes similares")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "count": 3,
                    "results": [
                        {
                            "report_id": 789,
                            "visual_distance": 0.05,
                            "visual_similarity": 0.97,
                            "geo_distance": 12.3,
                            "geo_similarity": 0.78,
                            "text_similarity": 0.66,
                            "fused_score": 0.88,
                            "model_distances": {
                                "resnet50": 0.05,
                                "clip-vit-base-patch32": 0.11
                            },
                            "model_similarities": {
                                "resnet50": 0.97,
                                "clip-vit-base-patch32": 0.94
                            },
                            "damage_type": "bache",
                            "severity": "alta",
                            "confidence": 0.92,
                            "latitude": 19.4515,
                            "longitude": -70.6974,
                            "created_at": "2026-03-01T10:30:00",
                            "status": "approved"
                        },
                        {
                            "report_id": 456,
                            "visual_distance": 0.12,
                            "visual_similarity": 0.94,
                            "geo_distance": 45.7,
                            "geo_similarity": 0.40,
                            "text_similarity": 0.31,
                            "fused_score": 0.68,
                            "damage_type": "bache",
                            "severity": "media",
                            "confidence": 0.85,
                            "latitude": 19.4512,
                            "longitude": -70.6970,
                            "created_at": "2026-02-28T15:20:00",
                            "status": "approved"
                        }
                    ]
                }
            ]
        }
    }


class DeduplicationStats(BaseModel):
    """Estadísticas del servicio de deduplicación"""
    index_size: int = Field(..., description="Número de reportes indexados")
    embedding_dim: int = Field(..., description="Dimensión de embeddings")
    visual_threshold: float = Field(..., description="Umbral de similitud visual")
    geo_threshold: float = Field(..., description="Umbral de distancia geográfica (metros)")
    time_window_days: int = Field(..., description="Ventana temporal en días")
    active_models: Optional[List[str]] = Field(None, description="Modelos visuales activos")
    model_dimensions: Optional[Dict[str, int]] = Field(None, description="Dimensiones por modelo")
    model_backends: Optional[Dict[str, str]] = Field(None, description="Backend efectivo por modelo")
    model_index_sizes: Optional[Dict[str, int]] = Field(None, description="Tamaño de índice por modelo")
    fusion_score_threshold: Optional[float] = Field(None, description="Umbral del score fusionado")
    weights: Optional[Dict[str, float]] = Field(None, description="Pesos del score fusionado")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "index_size": 1523,
                    "embedding_dim": 2048,
                    "visual_threshold": 0.15,
                    "geo_threshold": 50.0,
                    "time_window_days": 30,
                    "active_models": ["resnet50", "clip-vit-base-patch32"],
                    "model_dimensions": {
                        "resnet50": 2048,
                        "clip-vit-base-patch32": 512
                    },
                    "model_backends": {
                        "resnet50": "torchvision",
                        "clip-vit-base-patch32": "clip"
                    },
                    "model_index_sizes": {
                        "resnet50": 1523,
                        "clip-vit-base-patch32": 1523
                    },
                    "fusion_score_threshold": 0.72,
                    "weights": {
                        "visual_primary": 0.45,
                        "visual_secondary": 0.25,
                        "geo": 0.20,
                        "text": 0.10
                    }
                }
            ]
        }
    }


# ── M-13: Spatial Clustering ─────────────────────────────────────────────────

class ClusterMemberSchema(BaseModel):
    """Miembro de un cluster espacial"""
    report_id: int = Field(..., description="ID del reporte")
    latitude: float = Field(..., description="Latitud")
    longitude: float = Field(..., description="Longitud")
    damage_type: str = Field(..., description="Tipo de daño")
    severity: str = Field(..., description="Severidad")
    confidence: float = Field(..., description="Confianza ML [0,1]")
    status: str = Field(..., description="Estado del reporte")
    created_at: str = Field(..., description="Fecha de creación (ISO 8601)")
    is_primary: bool = Field(..., description="Si es el reporte primario del cluster")


class SpatialClusterSchema(BaseModel):
    """Un cluster de reportes geoespacialmente agrupados"""
    cluster_id: int = Field(..., description="ID interno del cluster (de DBSCAN)")
    primary_report_id: int = Field(..., description="Reporte con mayor confianza ML en el cluster")
    member_count: int = Field(..., description="Número de reportes en el cluster")
    centroid_lat: float = Field(..., description="Latitud del centroide del cluster")
    centroid_lon: float = Field(..., description="Longitud del centroide del cluster")
    damage_type: str = Field(..., description="Tipo de daño predominante")
    radius_m: float = Field(..., description="Radio máximo del cluster desde el centroide (metros)")
    members: List[ClusterMemberSchema] = Field(..., description="Reportes miembro del cluster")
    oldest_report_at: Optional[str] = Field(None, description="Fecha del reporte más antiguo")
    newest_report_at: Optional[str] = Field(None, description="Fecha del reporte más reciente")


class SpatialClusteringResponse(BaseModel):
    """Response de clustering espacial M-13"""
    clusters: List[SpatialClusterSchema] = Field(..., description="Clusters detectados")
    noise_report_ids: List[int] = Field(..., description="Reportes sin cluster (ruido DBSCAN)")
    total_reports_analyzed: int = Field(..., description="Total de reportes analizados")
    total_clustered: int = Field(..., description="Total de reportes en algún cluster")
    total_noise: int = Field(..., description="Total de reportes noise")
    eps_meters: float = Field(..., description="Radio DBSCAN usado (metros)")
    min_samples: int = Field(..., description="min_samples DBSCAN usado")
    damage_type_filter: Optional[str] = Field(None, description="Filtro de tipo de daño aplicado")
    time_window_days: Optional[int] = Field(None, description="Ventana temporal aplicada (días)")


class ClusterResolveRequest(BaseModel):
    """Request para resolver un cluster (marcar duplicados)"""
    cluster_id: int = Field(..., description="ID del cluster a resolver")
    damage_type: Optional[str] = Field(None, description="Tipo de daño (para re-computar clusters)")
    eps_meters: Optional[float] = Field(None, description="Radio DBSCAN (metros). Si omitido usa ajuste de admin.", gt=0)
    min_samples: Optional[int] = Field(None, description="min_samples DBSCAN. Si omitido usa ajuste de admin.", ge=2)
    time_window_days: Optional[int] = Field(None, description="Ventana temporal (días). Si omitido usa ajuste de admin.")


class ClusterResolveSummary(BaseModel):
    """Resultado de resolución de un cluster individual"""
    cluster_id: int
    primary_report_id: int
    resolved: int
    skipped: int


class ClusterResolveResponse(BaseModel):
    """Response de resolución de cluster(s)"""
    primary_report_id: Optional[int] = Field(None, description="Reporte primario (resolución de cluster único)")
    resolved_ids: List[int] = Field(..., description="IDs de reportes marcados como duplicados")
    skipped_ids: List[int] = Field(default_factory=list, description="IDs ya rechazados previamente")
    clusters_processed: Optional[int] = Field(None, description="Clusters procesados (modo batch)")
    total_resolved: Optional[int] = Field(None, description="Total resueltos (modo batch)")
    cluster_summaries: Optional[List[ClusterResolveSummary]] = Field(None, description="Resumen por cluster (modo batch)")
    message: str = Field(..., description="Descripción del resultado")


# ── End M-13 ─────────────────────────────────────────────────────────────────


class IndexRebuildResponse(BaseModel):
    """Response de reconstrucción de índice"""
    success: bool = Field(..., description="Si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    statistics: DeduplicationStats = Field(..., description="Estadísticas post-reconstrucción")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Índice reconstruido exitosamente",
                    "statistics": {
                        "index_size": 1523,
                        "embedding_dim": 2048,
                        "visual_threshold": 0.15,
                        "geo_threshold": 50.0,
                        "time_window_days": 30,
                        "active_models": ["resnet50", "clip-vit-base-patch32"]
                    }
                }
            ]
        }
    }
