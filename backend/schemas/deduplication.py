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
                        "visual_distance": 0.08,
                        "geo_distance": 25.5,
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
                        "geo_distance": 15.3,
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
    geo_distance: float = Field(..., description="Distancia geográfica en metros")
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
                            "geo_distance": 12.3,
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
                            "geo_distance": 45.7,
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
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "index_size": 1523,
                    "embedding_dim": 2048,
                    "visual_threshold": 0.15,
                    "geo_threshold": 50.0,
                    "time_window_days": 30
                }
            ]
        }
    }


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
                        "time_window_days": 30
                    }
                }
            ]
        }
    }
