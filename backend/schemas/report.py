"""
Schemas Pydantic para Reportes
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
import json as _json
from enum import Enum


# Enums que coinciden con el modelo
class ReportStatusEnum(str, Enum):
    """Estados de un reporte"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"


class DamageTypeEnum(str, Enum):
    """Tipos de daño detectado"""
    BACHE = "bache"
    GRIETA = "grieta"


class SeverityLevelEnum(str, Enum):
    """Niveles de severidad"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


# ============================================
# Request Schemas
# ============================================

class CreateReportRequest(BaseModel):
    """
    Schema para crear un nuevo reporte
    
    Nota: La imagen se recibe como multipart/form-data,
    no como parte del JSON. Este schema maneja los campos de texto.
    """
    # Coordenadas GPS (obligatorias)
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitud (WGS84)",
        examples=[-34.603722]
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitud (WGS84)",
        examples=[-58.381592]
    )
    
    # Descripción (opcional)
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Descripción del problema reportado",
        examples=["Bache grande en la calle frente al parque"]
    )
    
    # Dirección (opcional, puede ser auto-detectada por geocoding)
    address: Optional[str] = Field(
        None,
        max_length=500,
        description="Dirección aproximada",
        examples=["Av. Corrientes 1234, Buenos Aires"]
    )
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="Ciudad",
        examples=["Buenos Aires"]
    )
    province: Optional[str] = Field(
        None,
        max_length=100,
        description="Provincia/Estado",
        examples=["Buenos Aires"]
    )
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Limpia y valida la descripción"""
        if v:
            # Remover espacios extra
            v = " ".join(v.split())
            # Verificar longitud mínima si se proporciona
            if len(v) < 3:
                raise ValueError("La descripción debe tener al menos 3 caracteres")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "latitude": -34.603722,
                "longitude": -58.381592,
                "description": "Bache profundo que afecta el tránsito",
                "address": "Av. Corrientes 1234",
                "city": "Buenos Aires",
                "province": "Buenos Aires"
            }
        }
    )


class UpdateReportStatusRequest(BaseModel):
    """Schema para actualizar el estado de un reporte"""
    status: ReportStatusEnum = Field(..., description="Nuevo estado del reporte")
    rejection_reason: Optional[str] = Field(
        None,
        max_length=1000,
        description="Razón del rechazo (solo si status=REJECTED)"
    )


# ============================================
# Response Schemas
# ============================================

class ReportResponse(BaseModel):
    """Schema para la respuesta de un reporte"""
    id: int = Field(..., description="ID único del reporte")
    user_id: int = Field(..., description="ID del usuario que reportó")
    
    # Ubicación
    latitude: float = Field(..., description="Latitud (WGS84)")
    longitude: float = Field(..., description="Longitud (WGS84)")
    address: Optional[str] = Field(None, description="Dirección")
    city: Optional[str] = Field(None, description="Ciudad")
    province: Optional[str] = Field(None, description="Provincia")
    
    # Detección ML
    damage_type: DamageTypeEnum = Field(..., description="Tipo de daño detectado")
    severity: SeverityLevelEnum = Field(..., description="Nivel de severidad")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza de la detección (0-1)")
    
    # Imagen
    image_url: str = Field(..., description="URL de la imagen")
    image_width: Optional[int] = Field(None, description="Ancho de la imagen en píxeles")
    image_height: Optional[int] = Field(None, description="Alto de la imagen en píxeles")
    
    # Detecciones (bounding boxes)
    detections_json: Optional[str] = Field(None, description="JSON con las detecciones")

    # Campos derivados de detections_json (calculados por validador)
    annotated_image_url: Optional[str] = Field(None, description="URL imagen con bounding boxes")
    model_precision: Optional[float] = Field(None, description="Precisión del modelo en validación")
    model_recall: Optional[float] = Field(None, description="Recall del modelo en validación")
    model_map50: Optional[float] = Field(None, description="mAP50 del modelo en validación")
    
    # Estado
    status: ReportStatusEnum = Field(..., description="Estado actual del reporte")
    description: Optional[str] = Field(None, description="Descripción del usuario")
    rejection_reason: Optional[str] = Field(None, description="Razón de rechazo")
    
    # Timestamps
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")
    reviewed_at: Optional[datetime] = Field(None, description="Fecha de revisión")

    @model_validator(mode='after')
    def _extract_detection_fields(self):
        if self.detections_json:
            try:
                det = _json.loads(self.detections_json)
                if self.annotated_image_url is None:
                    self.annotated_image_url = det.get('annotated_image_url')
                if self.model_precision is None:
                    self.model_precision = det.get('model_precision')
                if self.model_recall is None:
                    self.model_recall = det.get('model_recall')
                if self.model_map50 is None:
                    self.model_map50 = det.get('model_map50')
            except Exception:
                pass
        return self
    
    model_config = ConfigDict(from_attributes=True)


class CreateReportResponse(BaseModel):
    """
    Schema para la respuesta inmediata después de crear un reporte
    
    Incluye información básica + resultado de detección ML
    """
    id: int = Field(..., description="ID único del reporte creado")
    status: ReportStatusEnum = Field(..., description="Estado inicial del reporte")
    
    # Resultado de detección (puede estar pendiente si status=processing)
    damage_type: DamageTypeEnum = Field(..., description="Tipo de daño detectado")
    severity: SeverityLevelEnum = Field(..., description="Severidad detectada")
    confidence: float = Field(..., description="Confianza de la detección (0-1)")
    
    # URLs
    image_url: str = Field(..., description="URL de la imagen subida")
    
    # Info básica
    latitude: float = Field(..., description="Latitud")
    longitude: float = Field(..., description="Longitud")
    description: Optional[str] = Field(None, description="Descripción del usuario")
    
    created_at: datetime = Field(..., description="Fecha de creación")
    
    # B-06: Job ID para seguimiento de procesamiento asíncrono
    job_id: Optional[str] = Field(None, description="ID del job RQ para seguimiento")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 123,
                "status": "processing",
                "damage_type": "bache",
                "severity": "media",
                "confidence": 0.5,
                "image_url": "http://localhost:9000/sirccd-images/reports/2026/03/02/abc123_image.jpg",
                "latitude": -34.603722,
                "longitude": -58.381592,
                "description": "Bache profundo en la vía principal",
                "created_at": "2026-03-02T18:30:00",
                "job_id": "abc123-def456-ghi789"
            }
        }
    )


class ReportListResponse(BaseModel):
    """Schema para lista de reportes con paginación"""
    total: int = Field(..., description="Total de reportes")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    reports: List[ReportResponse] = Field(..., description="Lista de reportes")
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# ML Detection Schemas
# ============================================

class BoundingBox(BaseModel):
    """Bounding box de una detección"""
    x1: float = Field(..., description="Coordenada X superior izquierda")
    y1: float = Field(..., description="Coordenada Y superior izquierda")
    x2: float = Field(..., description="Coordenada X inferior derecha")
    y2: float = Field(..., description="Coordenada Y inferior derecha")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza de la detección")
    class_name: str = Field(..., description="Nombre de la clase detectada")


class DetectionResult(BaseModel):
    """Resultado de detección ML"""
    damage_type: DamageTypeEnum = Field(..., description="Tipo de daño detectado")
    severity: SeverityLevelEnum = Field(..., description="Severidad calculada")
    confidence: float = Field(..., description="Confianza promedio")
    detections: List[BoundingBox] = Field(..., description="Lista de bounding boxes")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "damage_type": "bache",
                "severity": "alta",
                "confidence": 0.87,
                "detections": [
                    {
                        "x1": 100.5,
                        "y1": 200.3,
                        "x2": 350.7,
                        "y2": 450.9,
                        "confidence": 0.87,
                        "class_name": "pothole"
                    }
                ]
            }
        }
    )
