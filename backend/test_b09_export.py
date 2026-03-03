"""
Tests Unitarios para B-09 - Exportaciones GeoJSON/CSV

Valida:
1. Estructura GeoJSON (FeatureCollection, Features, Geometry)
2. Propiedades de features (coordenadas, attributes)
3. Headers y formato CSV
4. Agrupación temporal de KPIs (día, semana, mes)
5. Cálculo de métricas agregadas
6. Filtrado por ciudad, fechas, estado, prioridad

Nota: Tests standalone (sin base de datos real ni Redis)
"""

import io
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any


# ============================================
# Simulación de modelos (sin SQLAlchemy)
# ============================================

class MockIncident:
    """Mock de modelo Incident"""
    def __init__(
        self,
        id: int,
        report_id: int,
        status: str,
        priority: str,
        priority_score: float,
        damage_type: str,
        severity: str,
        latitude: float,
        longitude: float,
        address: str,
        city: str,
        province: str,
        created_at: datetime,
        completed_at: datetime = None,
        assigned_brigade_id: int = None,
        is_verified: bool = False
    ):
        self.id = id
        self.report_id = report_id
        self.status = status
        self.priority = priority
        self.priority_score = priority_score
        self.damage_type = damage_type
        self.severity = severity
        self.latitude = latitude
        self.longitude = longitude
        self.address = address
        self.city = city
        self.province = province
        self.created_at = created_at
        self.completed_at = completed_at
        self.assigned_brigade_id = assigned_brigade_id
        self.is_verified = is_verified
        
        # Atributos opcionales
        self.reported_by_user = None
        self.assigned_brigade = None
        self.verified_by = None


# ============================================
# Funciones auxiliares de exportación
# (Réplica simplificada de ExportService)
# ============================================

def mock_export_geojson(incidents: List[MockIncident], filters: Dict = None) -> Dict[str, Any]:
    """
    Simular exportación GeoJSON
    """
    features = []
    
    for incident in incidents:
        # Aplicar filtros
        if filters:
            if "city" in filters and filters["city"]:
                if filters["city"].lower() not in incident.city.lower():
                    continue
            
            if "priority" in filters and filters["priority"]:
                if incident.priority not in filters["priority"]:
                    continue
            
            if "date_from" in filters and filters["date_from"]:
                if incident.created_at < filters["date_from"]:
                    continue
            
            if "date_to" in filters and filters["date_to"]:
                if incident.created_at > filters["date_to"]:
                    continue
        
        # Calcular tiempo de resolución
        resolution_time_hours = None
        if incident.completed_at:
            delta = incident.completed_at - incident.created_at
            resolution_time_hours = round(delta.total_seconds() / 3600, 2)
        
        # Construir feature GeoJSON
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [incident.longitude, incident.latitude]
            },
            "properties": {
                "id": incident.id,
                "report_id": incident.report_id,
                "damage_type": incident.damage_type,
                "severity": incident.severity,
                "priority": incident.priority,
                "priority_score": incident.priority_score,
                "status": incident.status,
                "address": incident.address,
                "city": incident.city,
                "province": incident.province,
                "latitude": incident.latitude,
                "longitude": incident.longitude,
                "created_at": incident.created_at.isoformat(),
                "resolution_time_hours": resolution_time_hours,
                "is_verified": incident.is_verified
            }
        }
        
        features.append(feature)
    
    # Construir FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "total_features": len(features),
            "filters_applied": filters or {}
        },
        "features": features
    }
    
    return geojson


def mock_export_csv(incidents: List[MockIncident]) -> str:
    """
    Simular exportación CSV detallado
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    headers = [
        "id", "report_id", "status", "priority", "priority_score",
        "damage_type", "severity", "latitude", "longitude",
        "address", "city", "province", "created_at", "resolution_time_hours"
    ]
    writer.writerow(headers)
    
    # Datos
    for incident in incidents:
        resolution_time_hours = None
        if incident.completed_at:
            delta = incident.completed_at - incident.created_at
            resolution_time_hours = round(delta.total_seconds() / 3600, 2)
        
        row = [
            incident.id,
            incident.report_id,
            incident.status,
            incident.priority,
            incident.priority_score,
            incident.damage_type,
            incident.severity,
            incident.latitude,
            incident.longitude,
            incident.address,
            incident.city,
            incident.province,
            incident.created_at.isoformat(),
            resolution_time_hours if resolution_time_hours else ""
        ]
        writer.writerow(row)
    
    return output.getvalue()


def mock_export_kpis_csv(incidents: List[MockIncident], group_by: str = "day") -> str:
    """
    Simular exportación CSV de KPIs
    """
    # Agrupar por período
    grouped = {}
    
    for incident in incidents:
        # Determinar período
        if group_by == "day":
            period = incident.created_at.strftime("%Y-%m-%d")
        elif group_by == "week":
            period = incident.created_at.strftime("%Y-W%V")
        elif group_by == "month":
            period = incident.created_at.strftime("%Y-%m")
        else:
            period = incident.created_at.strftime("%Y-%m-%d")
        
        # Inicializar período
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
        
        # Acumular
        stats = grouped[period]
        stats["total"] += 1
        stats["by_status"][incident.status] = stats["by_status"].get(incident.status, 0) + 1
        stats["by_priority"][incident.priority] = stats["by_priority"].get(incident.priority, 0) + 1
        stats["by_damage_type"][incident.damage_type] = stats["by_damage_type"].get(incident.damage_type, 0) + 1
        stats["by_severity"][incident.severity] = stats["by_severity"].get(incident.severity, 0) + 1
        
        if incident.completed_at:
            delta = incident.completed_at - incident.created_at
            hours = delta.total_seconds() / 3600
            stats["resolution_times"].append(hours)
        
        if incident.is_verified:
            stats["verified_count"] += 1
        
        if incident.status in ["resolved", "verified", "closed"]:
            stats["resolved_count"] += 1
    
    # Calcular promedios
    for period, stats in grouped.items():
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
    
    # Generar CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "periodo", "total_incidentes", "nuevos", "asignados", "en_proceso", "resueltos",
        "prioridad_critica", "prioridad_alta", "baches", "grietas",
        "tiempo_resolucion_promedio_horas", "tasa_verificacion_porcentaje"
    ]
    writer.writerow(headers)
    
    for period, stats in sorted(grouped.items()):
        row = [
            period,
            stats["total"],
            stats["by_status"].get("open", 0),
            stats["by_status"].get("assigned", 0),
            stats["by_status"].get("in_progress", 0),
            stats["by_status"].get("resolved", 0),
            stats["by_priority"].get("critica", 0),
            stats["by_priority"].get("alta", 0),
            stats["by_damage_type"].get("bache", 0),
            stats["by_damage_type"].get("grieta", 0),
            round(stats["avg_resolution_time_hours"], 2) if stats["avg_resolution_time_hours"] else "",
            round(stats["verification_rate"] * 100, 2)
        ]
        writer.writerow(row)
    
    return output.getvalue()


# ============================================
# Tests
# ============================================

def test_1_geojson_structure():
    """Test 1: Verificar estructura básica de GeoJSON"""
    print("\n=== Test 1: Estructura GeoJSON válida ===")
    
    # Crear incidentes mock
    incidents = [
        MockIncident(
            id=1, report_id=10, status="open", priority="critica", priority_score=85.5,
            damage_type="bache", severity="alta", latitude=18.4861, longitude=-69.9312,
            address="Av. Winston Churchill", city="Santo Domingo", province="Distrito Nacional",
            created_at=datetime(2024, 12, 10, 8, 30)
        )
    ]
    
    # Exportar GeoJSON
    geojson = mock_export_geojson(incidents)
    
    # Validaciones
    assert geojson["type"] == "FeatureCollection", "Debe ser FeatureCollection"
    assert "metadata" in geojson, "Debe tener metadata"
    assert "features" in geojson, "Debe tener features"
    assert isinstance(geojson["features"], list), "Features debe ser lista"
    assert len(geojson["features"]) == 1, "Debe tener 1 feature"
    
    print("✅ Estructura GeoJSON válida")
    print(f"   - Tipo: {geojson['type']}")
    print(f"   - Features: {len(geojson['features'])}")
    print(f"   - Metadata keys: {list(geojson['metadata'].keys())}")


def test_2_geojson_feature_geometry():
    """Test 2: Verificar geometría de features GeoJSON"""
    print("\n=== Test 2: Geometría de Features ===")
    
    incidents = [
        MockIncident(
            id=1, report_id=10, status="open", priority="alta", priority_score=75.0,
            damage_type="bache", severity="alta", latitude=18.4861, longitude=-69.9312,
            address="Test", city="Santo Domingo", province="DN",
            created_at=datetime.utcnow()
        )
    ]
    
    geojson = mock_export_geojson(incidents)
    feature = geojson["features"][0]
    
    # Validar estructura de feature
    assert feature["type"] == "Feature", "Debe ser tipo Feature"
    assert "geometry" in feature, "Debe tener geometry"
    assert "properties" in feature, "Debe tener properties"
    
    # Validar geometría
    geometry = feature["geometry"]
    assert geometry["type"] == "Point", "Debe ser tipo Point"
    assert "coordinates" in geometry, "Debe tener coordinates"
    assert len(geometry["coordinates"]) == 2, "Debe tener 2 coordenadas [lon, lat]"
    
    lon, lat = geometry["coordinates"]
    assert lon == -69.9312, f"Longitud incorrecta: {lon}"
    assert lat == 18.4861, f"Latitud incorrecta: {lat}"
    
    print("✅ Geometría correcta")
    print(f"   - Tipo: {geometry['type']}")
    print(f"   - Coordenadas: [{lon}, {lat}]")


def test_3_geojson_properties():
    """Test 3: Verificar propiedades de features"""
    print("\n=== Test 3: Propiedades de Features ===")
    
    incidents = [
        MockIncident(
            id=1, report_id=10, status="assigned", priority="critica", priority_score=88.3,
            damage_type="bache", severity="alta", latitude=18.5, longitude=-70.0,
            address="Calle Test #123", city="Santo Domingo", province="DN",
            created_at=datetime(2024, 12, 1),
            completed_at=datetime(2024, 12, 3),
            assigned_brigade_id=5,
            is_verified=True
        )
    ]
    
    geojson = mock_export_geojson(incidents)
    props = geojson["features"][0]["properties"]
    
    # Validar campos obligatorios
    required_fields = [
        "id", "report_id", "damage_type", "severity", "priority", "priority_score",
        "status", "address", "city", "province", "latitude", "longitude", "created_at"
    ]
    
    for field in required_fields:
        assert field in props, f"Falta campo obligatorio: {field}"
    
    # Validar valores
    assert props["id"] == 1
    assert props["priority"] == "critica"
    assert props["priority_score"] == 88.3
    assert props["damage_type"] == "bache"
    assert props["severity"] == "alta"
    assert props["status"] == "assigned"
    assert props["city"] == "Santo Domingo"
    assert props["is_verified"] == True
    
    # Validar tiempo de resolución
    assert props["resolution_time_hours"] is not None
    expected_hours = 48.0  # 2 días
    assert abs(props["resolution_time_hours"] - expected_hours) < 0.1
    
    print("✅ Propiedades correctas")
    print(f"   - Campos obligatorios: {len(required_fields)}")
    print(f"   - Tiempo de resolución: {props['resolution_time_hours']} horas")


def test_4_csv_structure():
    """Test 4: Verificar estructura CSV"""
    print("\n=== Test 4: Estructura CSV ===")
    
    incidents = [
        MockIncident(
            id=1, report_id=10, status="open", priority="alta", priority_score=75.0,
            damage_type="bache", severity="alta", latitude=18.5, longitude=-70.0,
            address="Test", city="Santo Domingo", province="DN",
            created_at=datetime.utcnow()
        ),
        MockIncident(
            id=2, report_id=11, status="resolved", priority="media", priority_score=55.0,
            damage_type="grieta", severity="media", latitude=18.6, longitude=-70.1,
            address="Test 2", city="Santiago", province="Santiago",
            created_at=datetime.utcnow()
        )
    ]
    
    csv_content = mock_export_csv(incidents)
    lines = csv_content.strip().split('\n')
    
    # Validar headers
    headers = [h.strip() for h in lines[0].split(',')]  # Strip whitespace and \r
    expected_headers = [
        "id", "report_id", "status", "priority", "priority_score",
        "damage_type", "severity", "latitude", "longitude",
        "address", "city", "province", "created_at", "resolution_time_hours"
    ]
    
    assert headers == expected_headers, f"Headers incorrectos: {headers}"
    
    # Validar cantidad de filas (header + 2 datos)
    assert len(lines) == 3, f"Debe tener 3 líneas (1 header + 2 datos), tiene {len(lines)}"
    
    print("✅ Estructura CSV correcta")
    print(f"   - Headers: {len(headers)}")
    print(f"   - Filas de datos: {len(lines) - 1}")


def test_5_csv_data_values():
    """Test 5: Verificar valores de datos en CSV"""
    print("\n=== Test 5: Valores de Datos CSV ===")
    
    incidents = [
        MockIncident(
            id=42, report_id=100, status="resolved", priority="critica", priority_score=90.5,
            damage_type="bache", severity="alta", latitude=18.4861, longitude=-69.9312,
            address="Av. Test", city="Santo Domingo", province="DN",
            created_at=datetime(2024, 12, 1, 10, 0),
            completed_at=datetime(2024, 12, 2, 14, 30)
        )
    ]
    
    csv_content = mock_export_csv(incidents)
    lines = csv_content.strip().split('\n')
    
    # Parsear primera fila de datos
    reader = csv.DictReader(io.StringIO(csv_content))
    row = next(reader)
    
    # Validar valores
    assert row["id"] == "42"
    assert row["report_id"] == "100"
    assert row["status"] == "resolved"
    assert row["priority"] == "critica"
    assert row["priority_score"] == "90.5"
    assert row["damage_type"] == "bache"
    assert row["severity"] == "alta"
    assert row["latitude"] == "18.4861"
    assert row["longitude"] == "-69.9312"
    assert row["city"] == "Santo Domingo"
    
    # Validar tiempo de resolución (debe ser ~28.5 horas)
    resolution_time = float(row["resolution_time_hours"])
    expected_time = 28.5
    assert abs(resolution_time - expected_time) < 0.1, f"Tiempo incorrecto: {resolution_time}"
    
    print("✅ Valores CSV correctos")
    print(f"   - ID: {row['id']}, Prioridad: {row['priority']}")
    print(f"   - Tiempo resolución: {resolution_time} horas")


def test_6_kpis_csv_grouping_daily():
    """Test 6: KPIs - Agrupación diaria"""
    print("\n=== Test 6: KPIs Agrupación Diaria ===")
    
    # Crear incidentes en diferentes días
    incidents = [
        MockIncident(1, 10, "open", "alta", 75.0, "bache", "alta", 18.5, -70.0, "A", "SD", "DN",
                     datetime(2024, 12, 1)),
        MockIncident(2, 11, "assigned", "critica", 85.0, "bache", "alta", 18.5, -70.0, "B", "SD", "DN",
                     datetime(2024, 12, 1)),
        MockIncident(3, 12, "open", "media", 50.0, "grieta", "media", 18.5, -70.0, "C", "SD", "DN",
                     datetime(2024, 12, 2)),
    ]
    
    csv_content = mock_export_kpis_csv(incidents, group_by="day")
    lines = csv_content.strip().split('\n')
    
    # Debe haber 3 líneas: header + 2 períodos (2024-12-01, 2024-12-02)
    assert len(lines) == 3, f"Debe tener 3 líneas, tiene {len(lines)}"
    
    # Validar períodos
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    
    assert len(rows) == 2, "Debe agrupar en 2 días"
    assert rows[0]["periodo"] == "2024-12-01"
    assert rows[1]["periodo"] == "2024-12-02"
    
    # Validar totales del primer día (2 incidentes)
    assert rows[0]["total_incidentes"] == "2"
    assert rows[0]["nuevos"] == "1"  # 1 open
    assert rows[0]["asignados"] == "1"  # 1 assigned
    
    # Validar totales del segundo día (1 incidente)
    assert rows[1]["total_incidentes"] == "1"
    assert rows[1]["nuevos"] == "1"  # 1 open
    
    print("✅ Agrupación diaria correcta")
    print(f"   - Períodos: {len(rows)}")
    print(f"   - Día 1: {rows[0]['total_incidentes']} incidentes")
    print(f"   - Día 2: {rows[1]['total_incidentes']} incidentes")


def test_7_kpis_csv_grouping_monthly():
    """Test 7: KPIs - Agrupación mensual"""
    print("\n=== Test 7: KPIs Agrupación Mensual ===")
    
    # Crear incidentes en diferentes meses
    incidents = [
        MockIncident(1, 10, "open", "alta", 75.0, "bache", "alta", 18.5, -70.0, "A", "SD", "DN",
                     datetime(2024, 11, 15)),
        MockIncident(2, 11, "resolved", "media", 55.0, "grieta", "media", 18.5, -70.0, "B", "SD", "DN",
                     datetime(2024, 11, 20)),
        MockIncident(3, 12, "open", "critica", 90.0, "bache", "alta", 18.5, -70.0, "C", "SD", "DN",
                     datetime(2024, 12, 5)),
    ]
    
    csv_content = mock_export_kpis_csv(incidents, group_by="month")
    lines = csv_content.strip().split('\n')
    
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Debe agrupar en 2 meses
    assert len(rows) == 2, f"Debe tener 2 meses, tiene {len(rows)}"
    
    # Validar formato de período (YYYY-MM)
    assert rows[0]["periodo"] == "2024-11"
    assert rows[1]["periodo"] == "2024-12"
    assert len(rows[0]["periodo"]) == 7  # Format: YYYY-MM
    
    # Validar totales de noviembre (2 incidentes)
    assert rows[0]["total_incidentes"] == "2"
    
    # Validar totales de diciembre (1 incidente)
    assert rows[1]["total_incidentes"] == "1"
    assert rows[1]["prioridad_critica"] == "1"
    
    print("✅ Agrupación mensual correcta")
    print(f"   - Mes 1 (2024-11): {rows[0]['total_incidentes']} incidentes")
    print(f"   - Mes 2 (2024-12): {rows[1]['total_incidentes']} incidentes")


def test_8_kpis_metrics_calculation():
    """Test 8: KPIs - Cálculo de métricas"""
    print("\n=== Test 8: Cálculo de Métricas KPIs ===")
    
    # Crear incidentes con diferentes características
    incidents = [
        MockIncident(1, 10, "open", "critica", 90.0, "bache", "alta", 18.5, -70.0, "A", "SD", "DN",
                     datetime(2024, 12, 1), is_verified=False),
        MockIncident(2, 11, "resolved", "alta", 75.0, "bache", "alta", 18.5, -70.0, "B", "SD", "DN",
                     datetime(2024, 12, 1), completed_at=datetime(2024, 12, 2), is_verified=True),
        MockIncident(3, 12, "assigned", "media", 50.0, "grieta", "media", 18.5, -70.0, "C", "SD", "DN",
                     datetime(2024, 12, 1), is_verified=False),
    ]
    
    csv_content = mock_export_kpis_csv(incidents, group_by="day")
    reader = csv.DictReader(io.StringIO(csv_content))
    row = next(reader)
    
    # Validar totales
    assert row["total_incidentes"] == "3"
    
    # Validar distribución por estado
    assert row["nuevos"] == "1"  # 1 open
    assert row["asignados"] == "1"  # 1 assigned
    assert row["resueltos"] == "1"  # 1 resolved
    
    # Validar distribución por prioridad
    assert row["prioridad_critica"] == "1"
    assert row["prioridad_alta"] == "1"
    # prioridad_media sería columna 8, verificar si existe
    
    # Validar distribución por tipo
    assert row["baches"] == "2"
    assert row["grietas"] == "1"
    
    # Validar tasa de verificación (1 de 3 = 33.33%)
    verification_rate = float(row["tasa_verificacion_porcentaje"])
    expected_rate = 33.33
    assert abs(verification_rate - expected_rate) < 0.1, f"Tasa incorrecta: {verification_rate}"
    
    print("✅ Métricas calculadas correctamente")
    print(f"   - Total: {row['total_incidentes']}")
    print(f"   - Tasa verificación: {verification_rate}%")
    print(f"   - Distribución: {row['baches']} baches, {row['grietas']} grietas")


def test_9_filter_by_city():
    """Test 9: Filtrado por ciudad"""
    print("\n=== Test 9: Filtrado por Ciudad ===")
    
    incidents = [
        MockIncident(1, 10, "open", "alta", 75.0, "bache", "alta", 18.5, -70.0, "A",
                     "Santo Domingo", "DN", datetime.utcnow()),
        MockIncident(2, 11, "open", "media", 55.0, "grieta", "media", 19.5, -70.5, "B",
                     "Santiago", "Santiago", datetime.utcnow()),
        MockIncident(3, 12, "open", "baja", 35.0, "bache", "baja", 18.6, -70.1, "C",
                     "Santo Domingo", "DN", datetime.utcnow()),
    ]
    
    # Filtrar solo Santo Domingo
    geojson = mock_export_geojson(incidents, filters={"city": "Santo Domingo"})
    
    # Debe retornar solo 2 features (IDs 1 y 3)
    assert len(geojson["features"]) == 2, f"Debe tener 2 features, tiene {len(geojson['features'])}"
    
    cities = [f["properties"]["city"] for f in geojson["features"]]
    assert all("Santo Domingo" in city for city in cities), "Todas deben ser de Santo Domingo"
    
    print("✅ Filtrado por ciudad correcto")
    print(f"   - Total incidentes: {len(incidents)}")
    print(f"   - Filtrados (Santo Domingo): {len(geojson['features'])}")


def test_10_filter_by_date_range():
    """Test 10: Filtrado por rango de fechas"""
    print("\n=== Test 10: Filtrado por Rango de Fechas ===")
    
    incidents = [
        MockIncident(1, 10, "open", "alta", 75.0, "bache", "alta", 18.5, -70.0, "A", "SD", "DN",
                     datetime(2024, 11, 1)),
        MockIncident(2, 11, "open", "media", 55.0, "grieta", "media", 18.5, -70.0, "B", "SD", "DN",
                     datetime(2024, 11, 15)),
        MockIncident(3, 12, "open", "baja", 35.0, "bache", "baja", 18.5, -70.0, "C", "SD", "DN",
                     datetime(2024, 12, 1)),
    ]
    
    # Filtrar solo noviembre 2024
    date_from = datetime(2024, 11, 1)
    date_to = datetime(2024, 11, 30)
    
    geojson = mock_export_geojson(incidents, filters={
        "date_from": date_from,
        "date_to": date_to
    })
    
    # Debe retornar solo 2 features (IDs 1 y 2)
    assert len(geojson["features"]) == 2, f"Debe tener 2 features, tiene {len(geojson['features'])}"
    
    for feature in geojson["features"]:
        created_at_str = feature["properties"]["created_at"]
        created_at = datetime.fromisoformat(created_at_str)
        assert date_from <= created_at <= date_to, f"Fecha fuera de rango: {created_at}"
    
    print("✅ Filtrado por fechas correcto")
    print(f"   - Rango: {date_from.date()} a {date_to.date()}")
    print(f"   - Incidentes en rango: {len(geojson['features'])}")


# ============================================
# Ejecutar todos los tests
# ============================================

def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n" + "="*60)
    print("TESTS B-09 - EXPORTACIONES CSV/GEOJSON")
    print("="*60)
    
    tests = [
        test_1_geojson_structure,
        test_2_geojson_feature_geometry,
        test_3_geojson_properties,
        test_4_csv_structure,
        test_5_csv_data_values,
        test_6_kpis_csv_grouping_daily,
        test_7_kpis_csv_grouping_monthly,
        test_8_kpis_metrics_calculation,
        test_9_filter_by_city,
        test_10_filter_by_date_range,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"\n❌ FALLO: {e}")
        except Exception as e:
            failed += 1
            print(f"\n❌ ERROR: {e}")
    
    print("\n" + "="*60)
    print(f"RESULTADOS: {passed} tests pasados, {failed} tests fallidos")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 ¡TODOS LOS TESTS PASARON! 🎉")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
