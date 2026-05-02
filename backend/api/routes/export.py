# -*- coding: utf-8 -*-
"""
Rutas de API para Exportaciones (B-09)

Endpoints para exportar:
- Incidentes con ubicación en formato GeoJSON
- Incidentes detallados en formato CSV
- Métricas agregadas (KPIs) en formato CSV
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status as http_status
from fastapi.responses import StreamingResponse, JSONResponse
import io

from api.deps import SupervisorUser, CurrentUser
from services.export_service import ExportService, get_export_service
from schemas.export import (
    ExportStatusResponse,
    ExportFormatEnum,
    GroupByPeriodEnum
)


router = APIRouter()


# ============================================
# Exportación GeoJSON
# ============================================

@router.get(
    "/incidents/geojson",
    response_model=None,
    summary="Exportar incidentes en formato GeoJSON",
    description="""
    Exporta incidentes con ubicación geográfica en formato GeoJSON FeatureCollection.
    
    **Casos de uso:**
    - Visualización en mapas (Leaflet, Mapbox, Google Maps)
    - Análisis GIS (QGIS, ArcGIS)
    - Aplicaciones móviles con mapas
    
    **Filtros disponibles:**
    - Estado (status): open, in_progress, resolved, verified, closed
    - Prioridad (priority): baja, media, alta, critica
    - Tipo de daño (damage_type): bache, grieta
    - Severidad (severity): baja, media, alta
    - Ubicación (city, province)
    - Rango de fechas (date_from, date_to)
    - Incluir cerrados (include_closed)
    
    **Estructura GeoJSON:**
    ```json
    {
      "type": "FeatureCollection",
      "metadata": { ... },
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
          },
          "properties": { ... }
        }
      ]
    }
    ```
    
    **Límites:**
    - Máximo 10,000 incidentes por exportación
    - Sin paginación (usar filtros para reducir resultados)
    """,
    tags=["Exportaciones"]
)
async def export_incidents_geojson(
    # Dependencias
    current_user: SupervisorUser,
    
    # Filtros de clasificación
    filter_status: Optional[List[str]] = Query(
        None,
        alias="status",
        description="Estados a incluir (puede especificar múltiples)",
        examples=["open", "in_progress"]
    ),
    priority: Optional[List[str]] = Query(
        None,
        description="Prioridades a incluir",
        examples=["alta", "critica"]
    ),
    damage_type: Optional[str] = Query(
        None,
        description="Tipo de daño",
        examples=["bache"]
    ),
    severity: Optional[str] = Query(
        None,
        description="Nivel de severidad",
        examples=["alta"]
    ),
    
    # Filtros geográficos
    city: Optional[str] = Query(
        None,
        max_length=100,
        description="Ciudad (búsqueda parcial)",
        examples=["Santo Domingo"]
    ),
    province: Optional[str] = Query(
        None,
        max_length=100,
        description="Provincia",
        examples=["Distrito Nacional"]
    ),
    
    # Filtros temporales
    date_from: Optional[datetime] = Query(
        None,
        description="Fecha inicio (ISO 8601)",
        examples=["2024-01-01T00:00:00"]
    ),
    date_to: Optional[datetime] = Query(
        None,
        description="Fecha fin (ISO 8601)",
        examples=["2024-12-31T23:59:59"]
    ),
    
    # Opciones
    include_closed: bool = Query(
        False,
        description="Incluir incidentes cerrados"
    ),
    
    export_service: ExportService = Depends(get_export_service)
):
    """
    Exportar incidentes en formato GeoJSON
    """
    try:
        # Validar rango de fechas
        if date_from and date_to and date_to < date_from:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="date_to debe ser posterior a date_from"
            )
        
        # Generar GeoJSON
        geojson = export_service.export_incidents_geojson(
            status=filter_status,
            priority=priority,
            damage_type=damage_type,
            severity=severity,
            city=city,
            province=province,
            date_from=date_from,
            date_to=date_to,
            include_closed=include_closed
        )
        
        # Validar límite de registros
        if len(geojson["features"]) > 10000:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Demasiados registros ({len(geojson['features'])}). Máximo 10,000. Use filtros más específicos."
            )
        
        # Retornar GeoJSON directamente
        return JSONResponse(
            content=geojson,
            headers={
                "Content-Disposition": f"attachment; filename=incidentes_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.geojson"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar exportación GeoJSON: {str(e)}"
        )


# ============================================
# Exportación CSV - Incidentes Detallados
# ============================================

@router.get(
    "/incidents/csv",
    response_model=None,
    summary="Exportar listado detallado de incidentes en CSV",
    description="""
    Exporta listado detallado de incidentes en formato CSV (tabla).
    
    **Casos de uso:**
    - Análisis en Excel/Google Sheets
    - Reportes para gestión
    - Importación a otros sistemas
    
    **Columnas incluidas:**
    - Identificación: id, report_id
    - Clasificación: status, priority, priority_score, damage_type, severity
    - Ubicación: latitude, longitude, address, city, province
    - Personas: reported_by_name, verified_by_name
    - Fechas: created_at, started_at, completed_at, verified_at
    - Tiempos: resolution_time_hours, estimated_repair_hours
    - Verificación: is_verified
    
    **Filtros:** Mismos que GeoJSON (ver endpoint anterior)
    
    **Límites:** Máximo 10,000 registros
    """,
    tags=["Exportaciones"]
)
async def export_incidents_csv(
    # Dependencias
    current_user: SupervisorUser,
    
    # Filtros (mismos que GeoJSON)
    filter_status: Optional[List[str]] = Query(None, alias="status"),
    priority: Optional[List[str]] = Query(None),
    damage_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    city: Optional[str] = Query(None, max_length=100),
    province: Optional[str] = Query(None, max_length=100),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    include_closed: bool = Query(False),
    
    export_service: ExportService = Depends(get_export_service)
):
    """
    Exportar listado detallado de incidentes en CSV
    """
    try:
        # Validar rango de fechas
        if date_from and date_to and date_to < date_from:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="date_to debe ser posterior a date_from"
            )
        
        # Generar CSV
        csv_content = export_service.export_incidents_detailed_csv(
            status=filter_status,
            priority=priority,
            damage_type=damage_type,
            severity=severity,
            city=city,
            province=province,
            date_from=date_from,
            date_to=date_to,
            include_closed=include_closed
        )
        
        # Validar límite (contar líneas - 1 para el header)
        line_count = len(csv_content.split('\n')) - 1
        if line_count > 10000:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Demasiados registros ({line_count}). Máximo 10,000. Use filtros más específicos."
            )
        
        # Generar nombre de archivo
        filename = f"incidentes_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Retornar como streaming response
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar exportación CSV: {str(e)}"
        )


# ============================================
# Exportación CSV - KPIs Agregados
# ============================================

@router.get(
    "/kpis/csv",
    response_model=None,
    summary="Exportar métricas agregadas (KPIs) en CSV",
    description="""
    Exporta métricas agregadas por período temporal en formato CSV.
    
    **Casos de uso:**
    - Reportes ejecutivos
    - Análisis de tendencias
    - Dashboards de gestión
    - Auditoría de desempeño
    
    **Métricas incluidas por período:**
    - Total de incidentes
    - Distribución por estado (nuevos, en proceso, resueltos, verificados, cerrados)
    - Distribución por prioridad (baja, media, alta, crítica)
    - Distribución por tipo de daño (baches, grietas)
    - Distribución por severidad (baja, media, alta)
    - Tiempo promedio de resolución (horas)
    - Tasa de verificación (%)
    - Porcentaje de resueltos (%)
    
    **Períodos de agrupación:**
    - `day`: Diario (fecha YYYY-MM-DD)
    - `week`: Semanal (YYYY-W## formato ISO)
    - `month`: Mensual (YYYY-MM)
    
    **Filtros obligatorios:**
    - date_from, date_to (máximo 2 años de rango)
    
    **Filtros opcionales:**
    - city, province
    
    **Incluye fila de totales al final**
    """,
    tags=["Exportaciones"]
)
async def export_kpis_csv(
    # Dependencias
    current_user: SupervisorUser,
    
    # Filtros temporales (obligatorios)
    date_from: datetime = Query(
        ...,
        description="Fecha inicio (ISO 8601)",
        examples=["2024-01-01T00:00:00"]
    ),
    date_to: datetime = Query(
        ...,
        description="Fecha fin (ISO 8601)",
        examples=["2024-12-31T23:59:59"]
    ),
    
    # Agrupación
    group_by: GroupByPeriodEnum = Query(
        GroupByPeriodEnum.DAY,
        description="Nivel de agregación temporal"
    ),
    
    # Filtros geográficos (opcionales)
    city: Optional[str] = Query(
        None,
        max_length=100,
        description="Ciudad",
        examples=["Santo Domingo"]
    ),
    province: Optional[str] = Query(
        None,
        max_length=100,
        description="Provincia",
        examples=["Distrito Nacional"]
    ),
    
    export_service: ExportService = Depends(get_export_service)
):
    """
    Exportar KPIs agregados en CSV
    """
    try:
        # Validar rango de fechas
        if date_to < date_from:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="date_to debe ser posterior a date_from"
            )
        
        # Validar que el rango no sea mayor a 2 años
        delta = date_to - date_from
        if delta.days > 730:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="El rango de fechas no puede ser mayor a 2 años (730 días)"
            )
        
        # Generar CSV de KPIs
        csv_content = export_service.export_kpis_csv(
            date_from=date_from,
            date_to=date_to,
            group_by=group_by.value,
            city=city,
            province=province
        )
        
        # Generar nombre de archivo
        period_suffix = {
            "day": "diario",
            "week": "semanal",
            "month": "mensual"
        }.get(group_by.value, "agregado")
        
        filename = f"kpis_{period_suffix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Retornar como streaming response
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar exportación de KPIs: {str(e)}"
        )


# ============================================
# Exportación PDF — Reporte Mensual
# ============================================

@router.get(
    "/report/pdf",
    response_model=None,
    summary="Exportar reporte mensual en PDF",
    description="""
    Genera un reporte mensual en formato PDF con:
    - Resumen ejecutivo: incidentes creados, resueltos, tasa de resolución, tiempo promedio de cierre
    - Distribución por prioridad (crítica, alta, media, baja)
    - Zonas críticas: top 5 ciudades por cantidad de incidentes
    """,
    tags=["Exportaciones"]
)
async def export_monthly_report_pdf(
    current_user: SupervisorUser,
    year: int = Query(..., ge=2020, le=2100, description="Año del reporte"),
    month: int = Query(..., ge=1, le=12, description="Mes del reporte (1-12)"),
    city: Optional[str] = Query(None, max_length=100),
    province: Optional[str] = Query(None, max_length=100),
    export_service: ExportService = Depends(get_export_service)
):
    try:
        pdf_bytes = export_service.export_monthly_report_pdf(
            year=year,
            month=month,
            city=city,
            province=province
        )
        filename = f"reporte_mensual_{year}_{month:02d}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar reporte PDF: {str(e)}"
        )


# ============================================
# Endpoint de Estado
# ============================================

@router.get(
    "/status",
    response_model=ExportStatusResponse,
    summary="Estado del servicio de exportación",
    description="Retorna información sobre el servicio de exportación, formatos disponibles y límites",
    tags=["Exportaciones"]
)
async def get_export_status(
    current_user: CurrentUser
):
    """
    Obtener estado del servicio de exportación
    """
    return ExportStatusResponse(
        service="export",
        available_formats=["geojson", "csv", "pdf"],
        endpoints={
            "incidents_geojson": "/api/v1/export/incidents/geojson",
            "incidents_csv": "/api/v1/export/incidents/csv",
            "kpis_csv": "/api/v1/export/kpis/csv",
            "report_pdf": "/api/v1/export/report/pdf",
            "status": "/api/v1/export/status"
        },
        limits={
            "max_date_range_days": 730,
            "max_records_per_export": 10000,
            "supported_grouping": ["day", "week", "month"],
            "geojson_max_features": 10000,
            "csv_max_rows": 10000
        }
    )
