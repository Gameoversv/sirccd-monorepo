"""
Servicio de Exportación de Incidentes y KPIs (B-09)

Este servicio proporciona funcionalidad para exportar:
- Incidentes con ubicación geográfica en formato GeoJSON
- Métricas agregadas (KPIs) en formato CSV

Soporta filtros por:
- Rango de fechas (created_at, updated_at, completed_at)
- Estado del incidente
- Nivel de prioridad
- Ciudad/provincia
- Brigada asignada
- Tipo de daño
- Severidad
"""

import csv
import io
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from geoalchemy2.functions import ST_X, ST_Y, ST_AsGeoJSON

from db.session import get_db
from models.incident import Incident, IncidentStatus, PriorityLevel
from models.report import DamageType, SeverityLevel
from models.user import User
from models.brigade import Brigade


class ExportService:
    """
    Servicio para generar exportaciones de incidentes y KPIs
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================
    # Exportación GeoJSON
    # ============================================
    
    def export_incidents_geojson(
        self,
        status: Optional[List[str]] = None,
        priority: Optional[List[str]] = None,
        damage_type: Optional[str] = None,
        severity: Optional[str] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        brigade_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_closed: bool = False
    ) -> Dict[str, Any]:
        """
        Exportar incidentes en formato GeoJSON con filtros aplicados
        
        Args:
            status: Lista de estados a incluir
            priority: Lista de prioridades a incluir
            damage_type: Tipo de daño
            severity: Nivel de severidad
            city: Ciudad
            province: Provincia
            brigade_id: ID de brigada asignada
            date_from: Fecha inicio (por created_at)
            date_to: Fecha fin (por created_at)
            include_closed: Incluir incidentes cerrados (por defecto no)
        
        Returns:
            Dict con estructura GeoJSON FeatureCollection
        """
        # Base query
        query = self.db.query(Incident)
        
        # Aplicar filtros
        filters = []
        
        # Filtro de estado
        if status:
            filters.append(Incident.status.in_(status))
        
        # Por defecto, excluir cerrados a menos que se especifique
        if not include_closed and not status:
            filters.append(Incident.status != IncidentStatus.CLOSED)
        
        # Filtro de prioridad
        if priority:
            filters.append(Incident.priority.in_(priority))
        
        # Filtro de tipo de daño
        if damage_type:
            filters.append(Incident.damage_type == damage_type)
        
        # Filtro de severidad
        if severity:
            filters.append(Incident.severity == severity)
        
        # Filtro geográfico
        if city:
            filters.append(Incident.city.ilike(f"%{city}%"))
        
        if province:
            filters.append(Incident.province.ilike(f"%{province}%"))
        
        # Filtro de brigada
        if brigade_id:
            filters.append(Incident.assigned_brigade_id == brigade_id)
        
        # Filtro de fechas
        if date_from:
            filters.append(Incident.created_at >= date_from)
        
        if date_to:
            # Incluir todo el día final
            date_to_end = date_to.replace(hour=23, minute=59, second=59)
            filters.append(Incident.created_at <= date_to_end)
        
        # Aplicar todos los filtros
        if filters:
            query = query.filter(and_(*filters))
        
        # Ordenar por fecha de creación descendente
        query = query.order_by(Incident.created_at.desc())
        
        # Obtener incidentes
        incidents = query.all()
        
        # Construir GeoJSON FeatureCollection
        features = []
        
        for incident in incidents:
            # Extraer coordenadas usando PostGIS
            lon = self.db.scalar(ST_X(incident.location))
            lat = self.db.scalar(ST_Y(incident.location))
            
            # Obtener datos relacionados
            reporter_name = None
            if incident.reported_by_user:
                reporter_name = incident.reported_by_user.username
            
            brigade_name = None
            if incident.assigned_brigade:
                brigade_name = incident.assigned_brigade.name
            
            verifier_name = None
            if incident.verified_by:
                verifier = self.db.query(User).filter(User.id == incident.verified_by).first()
                if verifier:
                    verifier_name = verifier.username
            
            # Calcular tiempos
            resolution_time_hours = None
            if incident.completed_at and incident.created_at:
                delta = incident.completed_at - incident.created_at
                resolution_time_hours = round(delta.total_seconds() / 3600, 2)
            
            # Construir feature GeoJSON
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    # Identificación
                    "id": incident.id,
                    "report_id": incident.report_id,
                    
                    # Clasificación
                    "damage_type": incident.damage_type.value,
                    "severity": incident.severity.value,
                    "priority": incident.priority.value,
                    "priority_score": incident.priority_score,
                    
                    # Estado
                    "status": incident.status.value,
                    
                    # Ubicación
                    "address": incident.address,
                    "city": incident.city,
                    "province": incident.province,
                    "latitude": lat,
                    "longitude": lon,
                    
                    # Asignación
                    "assigned_brigade_id": incident.assigned_brigade_id,
                    "assigned_brigade_name": brigade_name,
                    "estimated_repair_hours": incident.estimated_repair_hours,
                    
                    # Reportante
                    "reported_by_id": incident.reported_by,
                    "reported_by_name": reporter_name,
                    
                    # Verificación
                    "is_verified": incident.is_verified,
                    "verified_by_id": incident.verified_by,
                    "verified_by_name": verifier_name,
                    
                    # Fechas (formato ISO 8601)
                    "created_at": incident.created_at.isoformat() if incident.created_at else None,
                    "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
                    "assigned_at": incident.assigned_at.isoformat() if incident.assigned_at else None,
                    "started_at": incident.started_at.isoformat() if incident.started_at else None,
                    "completed_at": incident.completed_at.isoformat() if incident.completed_at else None,
                    "verified_at": incident.verified_at.isoformat() if incident.verified_at else None,
                    
                    # Métricas
                    "resolution_time_hours": resolution_time_hours,
                    
                    # URLs de imágenes
                    "before_image_url": incident.before_image_url,
                    "after_image_url": incident.after_image_url,
                    
                    # Notas (limitadas a 500 caracteres para GeoJSON)
                    "notes": incident.notes[:500] if incident.notes else None
                }
            }
            
            features.append(feature)
        
        # Construir FeatureCollection
        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_features": len(features),
                "filters_applied": {
                    "status": status,
                    "priority": priority,
                    "damage_type": damage_type,
                    "severity": severity,
                    "city": city,
                    "province": province,
                    "brigade_id": brigade_id,
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                    "include_closed": include_closed
                }
            },
            "features": features
        }
        
        return geojson
    
    # ============================================
    # Exportación CSV de KPIs
    # ============================================
    
    def export_kpis_csv(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        group_by: str = "day",  # "day", "week", "month"
        city: Optional[str] = None,
        province: Optional[str] = None
    ) -> str:
        """
        Exportar métricas agregadas en formato CSV
        
        Args:
            date_from: Fecha inicio
            date_to: Fecha fin
            group_by: Nivel de agregación temporal ("day", "week", "month")
            city: Filtrar por ciudad
            province: Filtrar por provincia
        
        Returns:
            String con contenido CSV
        """
        # Base query
        query = self.db.query(Incident)
        
        # Filtros
        filters = []
        
        if date_from:
            filters.append(Incident.created_at >= date_from)
        
        if date_to:
            date_to_end = date_to.replace(hour=23, minute=59, second=59)
            filters.append(Incident.created_at <= date_to_end)
        
        if city:
            filters.append(Incident.city.ilike(f"%{city}%"))
        
        if province:
            filters.append(Incident.province.ilike(f"%{province}%"))
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Obtener todos los incidentes en el rango
        incidents = query.all()
        
        # Agrupar por período temporal
        grouped_data = self._group_incidents_by_period(incidents, group_by)
        
        # Generar CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        headers = [
            "periodo",
            "total_incidentes",
            "nuevos",
            "asignados",
            "en_proceso",
            "resueltos",
            "verificados",
            "cerrados",
            "prioridad_critica",
            "prioridad_alta",
            "prioridad_media",
            "prioridad_baja",
            "baches",
            "grietas",
            "severidad_alta",
            "severidad_media",
            "severidad_baja",
            "tiempo_resolucion_promedio_horas",
            "tasa_verificacion_porcentaje",
            "porcentaje_resueltos"
        ]
        writer.writerow(headers)
        
        # Escribir datos agrupados
        for period, stats in sorted(grouped_data.items()):
            row = [
                period,
                stats["total"],
                stats["by_status"].get("open", 0),
                stats["by_status"].get("assigned", 0),
                stats["by_status"].get("in_progress", 0),
                stats["by_status"].get("resolved", 0),
                stats["by_status"].get("verified", 0),
                stats["by_status"].get("closed", 0),
                stats["by_priority"].get("critica", 0),
                stats["by_priority"].get("alta", 0),
                stats["by_priority"].get("media", 0),
                stats["by_priority"].get("baja", 0),
                stats["by_damage_type"].get("bache", 0),
                stats["by_damage_type"].get("grieta", 0),
                stats["by_severity"].get("alta", 0),
                stats["by_severity"].get("media", 0),
                stats["by_severity"].get("baja", 0),
                round(stats["avg_resolution_time_hours"], 2) if stats["avg_resolution_time_hours"] else "",
                round(stats["verification_rate"] * 100, 2) if stats["verification_rate"] else "",
                round(stats["resolution_rate"] * 100, 2) if stats["resolution_rate"] else ""
            ]
            writer.writerow(row)
        
        # Agregar fila de totales al final
        total_stats = self._calculate_total_stats(incidents)
        writer.writerow([])  # Línea en blanco
        writer.writerow(["TOTALES"])
        total_row = [
            "TOTAL",
            total_stats["total"],
            total_stats["by_status"].get("open", 0),
            total_stats["by_status"].get("assigned", 0),
            total_stats["by_status"].get("in_progress", 0),
            total_stats["by_status"].get("resolved", 0),
            total_stats["by_status"].get("verified", 0),
            total_stats["by_status"].get("closed", 0),
            total_stats["by_priority"].get("critica", 0),
            total_stats["by_priority"].get("alta", 0),
            total_stats["by_priority"].get("media", 0),
            total_stats["by_priority"].get("baja", 0),
            total_stats["by_damage_type"].get("bache", 0),
            total_stats["by_damage_type"].get("grieta", 0),
            total_stats["by_severity"].get("alta", 0),
            total_stats["by_severity"].get("media", 0),
            total_stats["by_severity"].get("baja", 0),
            round(total_stats["avg_resolution_time_hours"], 2) if total_stats["avg_resolution_time_hours"] else "",
            round(total_stats["verification_rate"] * 100, 2) if total_stats["verification_rate"] else "",
            round(total_stats["resolution_rate"] * 100, 2) if total_stats["resolution_rate"] else ""
        ]
        writer.writerow(total_row)
        
        return output.getvalue()
    
    def export_incidents_detailed_csv(
        self,
        status: Optional[List[str]] = None,
        priority: Optional[List[str]] = None,
        damage_type: Optional[str] = None,
        severity: Optional[str] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        brigade_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_closed: bool = False
    ) -> str:
        """
        Exportar listado detallado de incidentes en CSV
        Similar al GeoJSON pero en formato tabular
        """
        # Reutilizar lógica de filtros del GeoJSON
        query = self.db.query(Incident)
        
        filters = []
        
        if status:
            filters.append(Incident.status.in_(status))
        
        if not include_closed and not status:
            filters.append(Incident.status != IncidentStatus.CLOSED)
        
        if priority:
            filters.append(Incident.priority.in_(priority))
        
        if damage_type:
            filters.append(Incident.damage_type == damage_type)
        
        if severity:
            filters.append(Incident.severity == severity)
        
        if city:
            filters.append(Incident.city.ilike(f"%{city}%"))
        
        if province:
            filters.append(Incident.province.ilike(f"%{province}%"))
        
        if brigade_id:
            filters.append(Incident.assigned_brigade_id == brigade_id)
        
        if date_from:
            filters.append(Incident.created_at >= date_from)
        
        if date_to:
            date_to_end = date_to.replace(hour=23, minute=59, second=59)
            filters.append(Incident.created_at <= date_to_end)
        
        if filters:
            query = query.filter(and_(*filters))
        
        query = query.order_by(Incident.created_at.desc())
        incidents = query.all()
        
        # Generar CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        headers = [
            "id", "report_id", "status", "priority", "priority_score",
            "damage_type", "severity", "latitude", "longitude",
            "address", "city", "province",
            "assigned_brigade_id", "assigned_brigade_name",
            "reported_by_name", "is_verified", "verified_by_name",
            "created_at", "assigned_at", "started_at", "completed_at", "verified_at",
            "resolution_time_hours", "estimated_repair_hours"
        ]
        writer.writerow(headers)
        
        # Datos
        for incident in incidents:
            lon = self.db.scalar(ST_X(incident.location))
            lat = self.db.scalar(ST_Y(incident.location))
            
            reporter_name = incident.reported_by_user.username if incident.reported_by_user else None
            brigade_name = incident.assigned_brigade.name if incident.assigned_brigade else None
            verifier_name = None
            if incident.verified_by:
                verifier = self.db.query(User).filter(User.id == incident.verified_by).first()
                if verifier:
                    verifier_name = verifier.username
            
            resolution_time_hours = None
            if incident.completed_at and incident.created_at:
                delta = incident.completed_at - incident.created_at
                resolution_time_hours = round(delta.total_seconds() / 3600, 2)
            
            row = [
                incident.id,
                incident.report_id,
                incident.status.value,
                incident.priority.value,
                incident.priority_score,
                incident.damage_type.value,
                incident.severity.value,
                lat,
                lon,
                incident.address,
                incident.city,
                incident.province,
                incident.assigned_brigade_id,
                brigade_name,
                reporter_name,
                incident.is_verified,
                verifier_name,
                incident.created_at.isoformat() if incident.created_at else "",
                incident.assigned_at.isoformat() if incident.assigned_at else "",
                incident.started_at.isoformat() if incident.started_at else "",
                incident.completed_at.isoformat() if incident.completed_at else "",
                incident.verified_at.isoformat() if incident.verified_at else "",
                resolution_time_hours if resolution_time_hours else "",
                incident.estimated_repair_hours if incident.estimated_repair_hours else ""
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    # ============================================
    # Métodos auxiliares
    # ============================================
    
    def _group_incidents_by_period(
        self,
        incidents: List[Incident],
        group_by: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Agrupar incidentes por período temporal y calcular estadísticas
        """
        grouped = {}
        
        for incident in incidents:
            # Determinar período
            if group_by == "day":
                period = incident.created_at.strftime("%Y-%m-%d")
            elif group_by == "week":
                # ISO week: año-semana
                period = incident.created_at.strftime("%Y-W%V")
            elif group_by == "month":
                period = incident.created_at.strftime("%Y-%m")
            else:
                period = incident.created_at.strftime("%Y-%m-%d")
            
            # Inicializar período si no existe
            if period not in grouped:
                grouped[period] = {
                    "total": 0,
                    "by_status": {},
                    "by_priority": {},
                    "by_damage_type": {},
                    "by_severity": {},
                    "resolution_times": [],
                    "verified_count": 0,
                    "resolved_count": 0
                }
            
            # Incrementar contadores
            stats = grouped[period]
            stats["total"] += 1
            
            # Por estado
            status = incident.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Por prioridad
            priority = incident.priority.value
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
            # Por tipo de daño
            damage = incident.damage_type.value
            stats["by_damage_type"][damage] = stats["by_damage_type"].get(damage, 0) + 1
            
            # Por severidad
            severity = incident.severity.value
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
            
            # Tiempo de resolución
            if incident.completed_at and incident.created_at:
                delta = incident.completed_at - incident.created_at
                hours = delta.total_seconds() / 3600
                stats["resolution_times"].append(hours)
            
            # Contadores para tasas
            if incident.is_verified:
                stats["verified_count"] += 1
            
            if incident.status in [IncidentStatus.RESOLVED, IncidentStatus.VERIFIED, IncidentStatus.CLOSED]:
                stats["resolved_count"] += 1
        
        # Calcular promedios y tasas
        for period, stats in grouped.items():
            # Tiempo promedio de resolución
            if stats["resolution_times"]:
                stats["avg_resolution_time_hours"] = sum(stats["resolution_times"]) / len(stats["resolution_times"])
            else:
                stats["avg_resolution_time_hours"] = None
            
            # Tasa de verificación
            if stats["total"] > 0:
                stats["verification_rate"] = stats["verified_count"] / stats["total"]
                stats["resolution_rate"] = stats["resolved_count"] / stats["total"]
            else:
                stats["verification_rate"] = 0
                stats["resolution_rate"] = 0
        
        return grouped
    
    def _calculate_total_stats(self, incidents: List[Incident]) -> Dict[str, Any]:
        """
        Calcular estadísticas totales para todos los incidentes
        """
        stats = {
            "total": len(incidents),
            "by_status": {},
            "by_priority": {},
            "by_damage_type": {},
            "by_severity": {},
            "resolution_times": [],
            "verified_count": 0,
            "resolved_count": 0
        }
        
        for incident in incidents:
            # Por estado
            status = incident.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Por prioridad
            priority = incident.priority.value
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
            # Por tipo de daño
            damage = incident.damage_type.value
            stats["by_damage_type"][damage] = stats["by_damage_type"].get(damage, 0) + 1
            
            # Por severidad
            severity = incident.severity.value
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
            
            # Tiempo de resolución
            if incident.completed_at and incident.created_at:
                delta = incident.completed_at - incident.created_at
                hours = delta.total_seconds() / 3600
                stats["resolution_times"].append(hours)
            
            # Contadores
            if incident.is_verified:
                stats["verified_count"] += 1
            
            if incident.status in [IncidentStatus.RESOLVED, IncidentStatus.VERIFIED, IncidentStatus.CLOSED]:
                stats["resolved_count"] += 1
        
        # Promedios y tasas
        if stats["resolution_times"]:
            stats["avg_resolution_time_hours"] = sum(stats["resolution_times"]) / len(stats["resolution_times"])
        else:
            stats["avg_resolution_time_hours"] = None
        
        if stats["total"] > 0:
            stats["verification_rate"] = stats["verified_count"] / stats["total"]
            stats["resolution_rate"] = stats["resolved_count"] / stats["total"]
        else:
            stats["verification_rate"] = 0
            stats["resolution_rate"] = 0
        
        return stats


def get_export_service(db: Session = Depends(get_db)) -> ExportService:
    """
    Dependencia para obtener instancia del servicio de exportación
    """
    return ExportService(db)
