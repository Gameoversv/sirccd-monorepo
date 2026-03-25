"""
Schemas Pydantic para Exportaciones (B-09)
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


# ============================================
# Enums
# ============================================

class ExportFormatEnum(str, Enum):
    """Formatos de exportación disponibles"""
    GEOJSON = "geojson"
    CSV = "csv"


class GroupByPeriodEnum(str, Enum):
    """Períodos de agrupación para KPIs"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


# ============================================
# Request Schemas - Filtros
# ============================================

class ExportIncidentsFilters(BaseModel):
    """
    Filtros para exportación de incidentes (GeoJSON y CSV)
    """
    # Filtros de clasificación
    status: Optional[List[str]] = Field(
        None,
        description="Lista de estados a incluir (open, in_progress, resolved, verified, closed)"
    )
    priority: Optional[List[str]] = Field(
        None,
        description="Lista de prioridades (baja, media, alta, critica)"
    )
    damage_type: Optional[str] = Field(
        None,
        description="Tipo de daño (bache, grieta)"
    )
    severity: Optional[str] = Field(
        None,
        description="Nivel de severidad (baja, media, alta)"
    )
    
    # Filtros geográficos
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="Ciudad (búsqueda parcial, case-insensitive)"
    )
    province: Optional[str] = Field(
        None,
        max_length=100,
        description="Provincia (búsqueda parcial, case-insensitive)"
    )
    
    # Filtros temporales
    date_from: Optional[datetime] = Field(
        None,
        description="Fecha inicio (ISO 8601, filtra por created_at)"
    )
    date_to: Optional[datetime] = Field(
        None,
        description="Fecha fin (ISO 8601, filtra por created_at)"
    )
    
    # Opciones
    include_closed: bool = Field(
        default=False,
        description="Incluir incidentes cerrados (por defecto false)"
    )
    
    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, v, info):
        """Validar que date_to sea posterior a date_from"""
        if v and info.data.get("date_from"):
            if v < info.data["date_from"]:
                raise ValueError("date_to debe ser posterior a date_from")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": ["open", "in_progress"],
                    "priority": ["alta", "critica"],
                    "city": "Santo Domingo",
                    "date_from": "2024-01-01T00:00:00",
                    "date_to": "2024-12-31T23:59:59",
                    "include_closed": False
                }
            ]
        }
    )


class ExportKPIsFilters(BaseModel):
    """
    Filtros para exportación de KPIs agregados
    """
    # Filtros temporales (obligatorios para KPIs)
    date_from: datetime = Field(
        ...,
        description="Fecha inicio (ISO 8601)"
    )
    date_to: datetime = Field(
        ...,
        description="Fecha fin (ISO 8601)"
    )
    
    # Agrupación temporal
    group_by: GroupByPeriodEnum = Field(
        default=GroupByPeriodEnum.DAY,
        description="Nivel de agregación temporal"
    )
    
    # Filtros geográficos (opcionales)
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="Ciudad"
    )
    province: Optional[str] = Field(
        None,
        max_length=100,
        description="Provincia"
    )
    
    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, v, info):
        """Validar que date_to sea posterior a date_from"""
        if v and info.data.get("date_from"):
            if v < info.data["date_from"]:
                raise ValueError("date_to debe ser posterior a date_from")
            
            # Validar que el rango no sea mayor a 2 años
            delta = v - info.data["date_from"]
            if delta.days > 730:  # ~2 años
                raise ValueError("El rango de fechas no puede ser mayor a 2 años")
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "date_from": "2024-01-01T00:00:00",
                    "date_to": "2024-12-31T23:59:59",
                    "group_by": "month",
                    "city": "Santo Domingo"
                }
            ]
        }
    )


# ============================================
# Response Schemas
# ============================================

class ExportMetadata(BaseModel):
    """
    Metadatos de una exportación
    """
    export_type: str = Field(..., description="Tipo de exportación")
    format: ExportFormatEnum = Field(..., description="Formato de exportación")
    generated_at: datetime = Field(..., description="Fecha de generación")
    total_records: int = Field(..., description="Total de registros exportados")
    filters_applied: dict = Field(..., description="Filtros aplicados")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "export_type": "incidents",
                    "format": "geojson",
                    "generated_at": "2024-12-15T10:30:00",
                    "total_records": 150,
                    "filters_applied": {
                        "city": "Santo Domingo",
                        "date_from": "2024-01-01",
                        "date_to": "2024-12-31"
                    }
                }
            ]
        }
    )


class GeoJSONExportResponse(BaseModel):
    """
    Respuesta para exportación GeoJSON
    
    Nota: En la práctica, el endpoint devuelve directamente el dict GeoJSON
    Este schema es solo para documentación
    """
    type: str = Field(default="FeatureCollection", description="Tipo GeoJSON")
    metadata: dict = Field(..., description="Metadatos de la exportación")
    features: List[dict] = Field(..., description="Lista de features GeoJSON")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "FeatureCollection",
                    "metadata": {
                        "generated_at": "2024-12-15T10:30:00",
                        "total_features": 2
                    },
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [-69.9312, 18.4861]
                            },
                            "properties": {
                                "id": 1,
                                "damage_type": "bache",
                                "severity": "alta",
                                "priority": "critica",
                                "status": "open",
                                "city": "Santo Domingo"
                            }
                        }
                    ]
                }
            ]
        }
    )


class CSVExportResponse(BaseModel):
    """
    Respuesta para exportación CSV
    
    Nota: El endpoint devuelve directamente el texto CSV como StreamingResponse
    Este schema es solo para documentación
    """
    content_type: str = Field(
        default="text/csv",
        description="Tipo de contenido"
    )
    filename: str = Field(
        ...,
        description="Nombre del archivo sugerido"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "content_type": "text/csv",
                    "filename": "incidentes_2024-12-15.csv"
                }
            ]
        }
    )


# ============================================
# Status Response
# ============================================

class ExportStatusResponse(BaseModel):
    """
    Respuesta de estado del servicio de exportación
    """
    service: str = Field(default="export", description="Nombre del servicio")
    available_formats: List[str] = Field(..., description="Formatos disponibles")
    endpoints: dict = Field(..., description="Endpoints disponibles")
    limits: dict = Field(..., description="Límites del servicio")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "service": "export",
                    "available_formats": ["geojson", "csv"],
                    "endpoints": {
                        "incidents_geojson": "/api/v1/export/incidents/geojson",
                        "incidents_csv": "/api/v1/export/incidents/csv",
                        "kpis_csv": "/api/v1/export/kpis/csv"
                    },
                    "limits": {
                        "max_date_range_days": 730,
                        "max_records": 10000
                    }
                }
            ]
        }
    )
