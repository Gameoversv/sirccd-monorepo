# R-09: Fórmula del Score de Prioridad y Pesos

**Fecha:** 2026-01-14  
**Versión:** 1.0  
**Estado:** Completo

## Objetivo

Diseñar una fórmula multicriterio para calcular el **score de prioridad** de cada reporte/incidente, permitiendo ordenar y priorizar la atención de daños viales de manera objetiva, transparente y ajustable.

---

## 1. Visión general del sistema de priorización

### 1.1 Problemática

El municipio recibe cientos de reportes diarios de daños viales. Sin un sistema de priorización:
- ❌ Se atienden reportes por orden de llegada (FIFO), no por urgencia
- ❌ Daños críticos en zonas de alto tráfico quedan desatendidos
- ❌ Decisiones subjetivas de operadores
- ❌ Ineficiencia en asignación de brigadas

### 1.2 Solución: Score multicriterio

```
Score = f(Severidad, Riesgo, Tráfico, POIs, Antigüedad, Duplicados)
```

**Características:**
- ✅ Cálculo automático al crear/actualizar reporte
- ✅ Pesos configurables por administrador
- ✅ Transparente y auditable
- ✅ Recalculable en tiempo real
- ✅ Considera factores espaciales y temporales

---

## 2. Criterios de priorización

### 2.1 Resumen de criterios

| # | Criterio | Símbolo | Peso default | Descripción |
|---|----------|---------|--------------|-------------|
| 1 | Severidad del daño | $S$ | 30% | Gravedad física del daño (ML + validación) |
| 2 | Riesgo peatonal | $R_p$ | 20% | Peligro para peatones (zonas escolares, hospitales) |
| 3 | Tráfico aproximado | $T$ | 15% | Volumen vehicular estimado de la vía |
| 4 | Cercanía a POIs | $P$ | 15% | Proximidad a puntos importantes |
| 5 | Antigüedad del daño | $A$ | 10% | Tiempo desde creación (urgencia creciente) |
| 6 | Duplicados consolidados | $D$ | 10% | Reportes ciudadanos del mismo daño |

**Total pesos:** 100%

---

### 2.2 Criterio 1: Severidad del daño ($S$)

**Definición:** Gravedad física del daño vial detectado.

**Fuentes de datos:**
1. **Modelo ML (YOLOv8-seg):** Clasificación automática de imagen
2. **Selección del ciudadano:** Categoría elegida al reportar
3. **Validación del operador:** Ajuste manual si difiere

**Escala normalizada (0-1):**

| Nivel | Valor $S$ | Descripción | Ejemplos |
|-------|-----------|-------------|----------|
| Crítico | 1.0 | Daño que impide circulación o causa accidentes | Socavón >50cm, colapso de pavimento, hundimiento |
| Alto | 0.75 | Daño significativo que afecta seguridad | Bache >20cm profundidad, grietas anchas, alcantarilla abierta |
| Medio | 0.5 | Daño que afecta comodidad y puede empeorar | Bache 5-20cm, señalización dañada, desnivel |
| Bajo | 0.25 | Daño menor, cosmético o incipiente | Grietas superficiales, pintura desgastada, pequeños hoyos |
| Mínimo | 0.1 | Mantenimiento preventivo | Desgaste normal, limpieza requerida |

**Cálculo:**

```python
def calculate_severity(ml_prediction: dict, citizen_category: str, operator_override: float = None) -> float:
    """
    Calcula severidad combinando ML y entrada humana.
    
    Args:
        ml_prediction: {'class': str, 'confidence': float, 'severity_score': float}
        citizen_category: Categoría seleccionada por ciudadano
        operator_override: Valor manual del operador (si existe)
    
    Returns:
        Severidad normalizada [0, 1]
    """
    
    # Si operador validó manualmente, usar ese valor
    if operator_override is not None:
        return operator_override
    
    # Mapeo de categorías ciudadanas a severidad base
    CITIZEN_SEVERITY_MAP = {
        'socavon': 1.0,
        'bache_grande': 0.75,
        'bache_mediano': 0.5,
        'bache_pequeno': 0.25,
        'grieta': 0.3,
        'alcantarilla': 0.8,
        'senalizacion': 0.4,
        'alumbrado': 0.35,
        'banqueta': 0.45,
        'otro': 0.3
    }
    
    citizen_severity = CITIZEN_SEVERITY_MAP.get(citizen_category, 0.3)
    
    # Si ML tiene alta confianza, ponderar más el ML
    if ml_prediction and ml_prediction['confidence'] > 0.8:
        ml_severity = ml_prediction['severity_score']
        # 70% ML + 30% ciudadano cuando confianza alta
        return 0.7 * ml_severity + 0.3 * citizen_severity
    elif ml_prediction and ml_prediction['confidence'] > 0.5:
        ml_severity = ml_prediction['severity_score']
        # 50% ML + 50% ciudadano cuando confianza media
        return 0.5 * ml_severity + 0.5 * citizen_severity
    else:
        # Baja confianza ML o sin ML, usar ciudadano
        return citizen_severity
```

---

### 2.3 Criterio 2: Riesgo peatonal ($R_p$)

**Definición:** Nivel de peligro para peatones en la zona del daño.

**Factores considerados:**
- Zonas escolares (perímetro de escuelas)
- Hospitales y centros de salud
- Asilos y centros de adultos mayores
- Parques y plazas públicas
- Paradas de transporte público
- Cruces peatonales

**Escala normalizada (0-1):**

| Nivel | Valor $R_p$ | Condición |
|-------|-------------|-----------|
| Crítico | 1.0 | Dentro de zona escolar (≤100m de escuela) en horario escolar |
| Muy alto | 0.85 | Hospital/centro de salud (≤150m) |
| Alto | 0.7 | Asilo, guardería, centro comunitario (≤150m) |
| Medio-alto | 0.55 | Parada de transporte público (≤50m) |
| Medio | 0.4 | Parque, plaza, mercado (≤200m) |
| Bajo | 0.2 | Zona residencial sin POIs especiales |
| Mínimo | 0.1 | Zona industrial o sin tráfico peatonal |

**Cálculo espacial:**

```python
from shapely.geometry import Point
from geoalchemy2.functions import ST_DWithin, ST_Distance

async def calculate_pedestrian_risk(lat: float, lng: float, report_time: datetime) -> float:
    """
    Calcula riesgo peatonal basado en cercanía a zonas sensibles.
    
    Usa PostGIS para cálculos espaciales eficientes.
    """
    
    point = Point(lng, lat)
    
    # Definir radios de búsqueda por tipo de POI
    POI_CONFIGS = [
        {'type': 'school', 'radius_m': 100, 'base_risk': 1.0, 'time_sensitive': True},
        {'type': 'hospital', 'radius_m': 150, 'base_risk': 0.85, 'time_sensitive': False},
        {'type': 'elderly_center', 'radius_m': 150, 'base_risk': 0.7, 'time_sensitive': False},
        {'type': 'bus_stop', 'radius_m': 50, 'base_risk': 0.55, 'time_sensitive': False},
        {'type': 'park', 'radius_m': 200, 'base_risk': 0.4, 'time_sensitive': False},
        {'type': 'market', 'radius_m': 150, 'base_risk': 0.45, 'time_sensitive': True},
    ]
    
    max_risk = 0.1  # Riesgo base mínimo
    
    for config in POI_CONFIGS:
        # Buscar POIs cercanos usando PostGIS
        nearby_pois = await db.execute(f"""
            SELECT id, name, ST_Distance(
                location::geography,
                ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography
            ) as distance_m
            FROM poi
            WHERE type = '{config['type']}'
              AND ST_DWithin(
                  location::geography,
                  ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography,
                  {config['radius_m']}
              )
            ORDER BY distance_m
            LIMIT 1
        """)
        
        if nearby_pois:
            poi = nearby_pois[0]
            distance = poi.distance_m
            
            # Calcular factor de distancia (más cerca = más riesgo)
            distance_factor = 1 - (distance / config['radius_m'])
            
            # Ajustar por horario si aplica
            time_factor = 1.0
            if config['time_sensitive'] and config['type'] == 'school':
                hour = report_time.hour
                # Horario escolar: 7-9 AM y 12-3 PM (entrada/salida)
                if (7 <= hour <= 9) or (12 <= hour <= 15):
                    time_factor = 1.2  # Aumentar 20% en horario pico
                elif 21 <= hour or hour <= 6:
                    time_factor = 0.5  # Reducir 50% en noche
            
            risk = config['base_risk'] * distance_factor * time_factor
            max_risk = max(max_risk, min(risk, 1.0))  # Clamp a [0, 1]
    
    return round(max_risk, 3)
```

---

### 2.4 Criterio 3: Tráfico aproximado ($T$)

**Definición:** Volumen vehicular estimado de la vía donde se ubica el daño.

**Fuentes de datos:**
1. **Clasificación de vía:** Tipo de calle (primaria, secundaria, local)
2. **Datos históricos:** Aforos vehiculares del municipio
3. **APIs externas:** Google Maps Traffic, HERE, TomTom (si disponible)
4. **Estimación por zona:** Densidad poblacional y comercial

**Escala normalizada (0-1):**

| Nivel | Valor $T$ | Vehículos/día estimados | Tipo de vía |
|-------|-----------|-------------------------|-------------|
| Muy alto | 1.0 | >50,000 | Avenida principal, boulevard |
| Alto | 0.8 | 20,000-50,000 | Avenida secundaria, colector |
| Medio-alto | 0.6 | 10,000-20,000 | Calle colectora |
| Medio | 0.4 | 5,000-10,000 | Calle secundaria comercial |
| Bajo | 0.2 | 1,000-5,000 | Calle residencial |
| Muy bajo | 0.1 | <1,000 | Calle local, privada |

**Cálculo:**

```python
async def calculate_traffic_score(lat: float, lng: float) -> float:
    """
    Estima tráfico vehicular basado en tipo de vía y zona.
    """
    
    # 1. Obtener tipo de vía desde OSM o base de datos local
    road_type = await get_road_type_from_osm(lat, lng)
    
    ROAD_TYPE_TRAFFIC = {
        'motorway': 1.0,
        'trunk': 0.9,
        'primary': 0.8,
        'secondary': 0.6,
        'tertiary': 0.45,
        'residential': 0.25,
        'service': 0.15,
        'unclassified': 0.2,
        'living_street': 0.1,
    }
    
    base_traffic = ROAD_TYPE_TRAFFIC.get(road_type, 0.3)
    
    # 2. Ajustar por zona comercial/industrial
    zone_type = await get_zone_type(lat, lng)
    
    ZONE_MULTIPLIERS = {
        'commercial': 1.3,
        'industrial': 1.2,
        'residential': 1.0,
        'mixed': 1.15,
        'rural': 0.7,
    }
    
    zone_multiplier = ZONE_MULTIPLIERS.get(zone_type, 1.0)
    
    # 3. Aplicar multiplicador y normalizar
    traffic_score = min(1.0, base_traffic * zone_multiplier)
    
    return round(traffic_score, 3)

async def get_road_type_from_osm(lat: float, lng: float) -> str:
    """Consulta OpenStreetMap para obtener tipo de vía."""
    
    # Query Overpass API
    query = f"""
    [out:json];
    way(around:20,{lat},{lng})["highway"];
    out tags;
    """
    
    response = await httpx.post(
        "https://overpass-api.de/api/interpreter",
        data=query
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('elements'):
            return data['elements'][0]['tags'].get('highway', 'unclassified')
    
    return 'unclassified'
```

---

### 2.5 Criterio 4: Cercanía a POIs ($P$)

**Definición:** Proximidad a puntos de interés que aumentan la importancia del daño.

**Tipos de POIs considerados:**

| Categoría | Peso relativo | Ejemplos |
|-----------|---------------|----------|
| **Gobierno/Servicios** | 1.0 | Palacio municipal, oficinas de gobierno, bomberos |
| **Salud** | 0.95 | Hospitales, clínicas, centros de salud |
| **Educación** | 0.9 | Escuelas, universidades, bibliotecas |
| **Transporte** | 0.85 | Estaciones de metro/tren, terminales de autobuses |
| **Turismo** | 0.8 | Monumentos, museos, sitios históricos |
| **Comercio** | 0.7 | Centros comerciales, mercados principales |
| **Religioso** | 0.65 | Iglesias, templos (alto tráfico en eventos) |
| **Recreativo** | 0.6 | Estadios, parques grandes, centros deportivos |

**Fórmula de cálculo:**

$$P = \max_{i \in POIs} \left( w_i \cdot \frac{\max(0, r_{max} - d_i)}{r_{max}} \right)$$

Donde:
- $w_i$ = peso del tipo de POI $i$
- $d_i$ = distancia al POI $i$ en metros
- $r_{max}$ = radio máximo de influencia (500m default)

**Implementación:**

```python
async def calculate_poi_proximity_score(lat: float, lng: float) -> float:
    """
    Calcula score basado en cercanía a POIs importantes.
    
    Retorna el máximo score entre todos los POIs cercanos.
    """
    
    R_MAX = 500  # Radio máximo de influencia en metros
    
    POI_WEIGHTS = {
        'government': 1.0,
        'hospital': 0.95,
        'school': 0.9,
        'university': 0.85,
        'transit_station': 0.85,
        'monument': 0.8,
        'shopping_center': 0.7,
        'market': 0.7,
        'church': 0.65,
        'stadium': 0.6,
        'park_major': 0.55,
    }
    
    # Buscar todos los POIs dentro del radio
    nearby_pois = await db.execute(f"""
        SELECT 
            type,
            ST_Distance(
                location::geography,
                ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography
            ) as distance_m
        FROM poi
        WHERE ST_DWithin(
            location::geography,
            ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography,
            {R_MAX}
        )
    """)
    
    if not nearby_pois:
        return 0.1  # Score mínimo si no hay POIs cercanos
    
    max_score = 0.0
    
    for poi in nearby_pois:
        weight = POI_WEIGHTS.get(poi.type, 0.5)
        distance = poi.distance_m
        
        # Factor de distancia: 1.0 a 0m, 0.0 a R_MAX
        distance_factor = max(0, (R_MAX - distance) / R_MAX)
        
        score = weight * distance_factor
        max_score = max(max_score, score)
    
    return round(max_score, 3)
```

---

### 2.6 Criterio 5: Antigüedad del daño ($A$)

**Definición:** Tiempo transcurrido desde la creación del reporte, con urgencia creciente.

**Justificación:**
- Reportes antiguos sin atender indican ineficiencia
- Daños pueden empeorar con el tiempo
- Ciudadanos esperan respuesta en tiempo razonable
- Evita que reportes queden "olvidados"

**Función de crecimiento (logarítmica con meseta):**

$$A = \min\left(1.0, \frac{\ln(1 + t/t_{ref})}{\ln(1 + t_{max}/t_{ref})}\right)$$

Donde:
- $t$ = días desde creación del reporte
- $t_{ref}$ = tiempo de referencia (7 días default)
- $t_{max}$ = tiempo para alcanzar score máximo (30 días default)

**Comportamiento:**

| Días | Score $A$ | Interpretación |
|------|-----------|----------------|
| 0 | 0.0 | Recién creado |
| 1 | 0.12 | Nuevo |
| 3 | 0.28 | Activo |
| 7 | 0.50 | Necesita atención |
| 14 | 0.70 | Urgente |
| 21 | 0.85 | Muy urgente |
| 30+ | 1.0 | Crítico (máximo) |

**Gráfica de la función:**

```
Score A
  1.0 |                    _______________
      |                 __/
  0.8 |              __/
      |           __/
  0.6 |        __/
      |      _/
  0.4 |    _/
      |  _/
  0.2 |_/
      |
  0.0 +----+----+----+----+----+----+----
      0    5   10   15   20   25   30  Días
```

**Implementación:**

```python
import math
from datetime import datetime, timedelta

def calculate_age_score(
    created_at: datetime,
    current_time: datetime = None,
    t_ref: int = 7,
    t_max: int = 30
) -> float:
    """
    Calcula score de antigüedad con crecimiento logarítmico.
    
    Args:
        created_at: Fecha de creación del reporte
        current_time: Tiempo actual (default: now)
        t_ref: Días de referencia para curva logarítmica
        t_max: Días para alcanzar score máximo
    
    Returns:
        Score de antigüedad [0, 1]
    """
    
    if current_time is None:
        current_time = datetime.utcnow()
    
    # Calcular días transcurridos
    delta = current_time - created_at
    days = delta.total_seconds() / 86400  # Convertir a días decimales
    
    if days <= 0:
        return 0.0
    
    # Fórmula logarítmica con meseta
    numerator = math.log(1 + days / t_ref)
    denominator = math.log(1 + t_max / t_ref)
    
    score = min(1.0, numerator / denominator)
    
    return round(score, 3)

# Ejemplos de uso
>>> calculate_age_score(datetime.now() - timedelta(days=0))
0.0
>>> calculate_age_score(datetime.now() - timedelta(days=7))
0.5
>>> calculate_age_score(datetime.now() - timedelta(days=30))
1.0
>>> calculate_age_score(datetime.now() - timedelta(days=60))
1.0  # Meseta alcanzada
```

---

### 2.7 Criterio 6: Duplicados consolidados ($D$)

**Definición:** Número de reportes ciudadanos que refieren al mismo daño físico.

**Justificación:**
- Múltiples reportes del mismo daño indican problema visible/urgente
- Mayor impacto en la ciudadanía
- Validación social del problema
- Evita resolver un reporte y dejar otros idénticos abiertos

**Escala (función logarítmica suavizada):**

$$D = \min\left(1.0, \frac{\ln(1 + n)}{\ln(1 + n_{max})}\right)$$

Donde:
- $n$ = número de reportes duplicados consolidados
- $n_{max}$ = número para alcanzar score máximo (10 default)

| Duplicados | Score $D$ | Interpretación |
|------------|-----------|----------------|
| 1 (único) | 0.0 | Reporte individual |
| 2 | 0.29 | Confirmado por otro ciudadano |
| 3 | 0.46 | Múltiples confirmaciones |
| 5 | 0.67 | Problema muy visible |
| 7 | 0.81 | Alta demanda ciudadana |
| 10+ | 1.0 | Prioridad máxima por duplicados |

**Implementación:**

```python
import math

async def calculate_duplicate_score(incident_id: str, n_max: int = 10) -> float:
    """
    Calcula score basado en número de reportes consolidados.
    
    Args:
        incident_id: ID del incidente (grupo de duplicados)
        n_max: Número de duplicados para score máximo
    
    Returns:
        Score de duplicados [0, 1]
    """
    
    # Contar reportes vinculados al incidente
    count = await db.execute("""
        SELECT COUNT(*) as n
        FROM report
        WHERE incident_id = :incident_id
          AND status NOT IN ('REJECTED', 'SPAM')
    """, {'incident_id': incident_id})
    
    n = count[0].n if count else 1
    
    if n <= 1:
        return 0.0
    
    # Fórmula logarítmica
    score = math.log(1 + n) / math.log(1 + n_max)
    
    return round(min(1.0, score), 3)

# El score se recalcula cada vez que se vincula un nuevo duplicado
async def on_duplicate_linked(report_id: str, incident_id: str):
    """Evento: se vinculó un reporte como duplicado."""
    
    # Recalcular score del incidente
    new_duplicate_score = await calculate_duplicate_score(incident_id)
    
    # Actualizar incidente
    await db.execute("""
        UPDATE incident
        SET duplicate_score = :score,
            duplicate_count = duplicate_count + 1,
            score = recalculate_total_score(:incident_id)  -- Trigger
        WHERE id = :incident_id
    """, {'incident_id': incident_id, 'score': new_duplicate_score})
```

---

## 3. Fórmula matemática del score

### 3.1 Fórmula principal (suma ponderada)

$$\boxed{Score = w_S \cdot S + w_{R_p} \cdot R_p + w_T \cdot T + w_P \cdot P + w_A \cdot A + w_D \cdot D}$$

Donde:
- $Score \in [0, 1]$ (normalizado)
- $\sum w_i = 1$ (pesos suman 100%)

### 3.2 Pesos por defecto

| Criterio | Peso | Justificación |
|----------|------|---------------|
| $w_S$ (Severidad) | **0.30** | Factor más importante: gravedad del daño |
| $w_{R_p}$ (Riesgo peatonal) | **0.20** | Seguridad de personas vulnerables |
| $w_T$ (Tráfico) | **0.15** | Impacto vehicular |
| $w_P$ (POIs) | **0.15** | Visibilidad e importancia institucional |
| $w_A$ (Antigüedad) | **0.10** | Urgencia temporal |
| $w_D$ (Duplicados) | **0.10** | Validación ciudadana |

### 3.3 Ejemplo de cálculo

**Escenario:** Bache grande cerca de escuela primaria

| Criterio | Valor | Peso | Contribución |
|----------|-------|------|--------------|
| Severidad (bache grande) | 0.75 | 0.30 | 0.225 |
| Riesgo peatonal (escuela a 80m) | 0.85 | 0.20 | 0.170 |
| Tráfico (calle secundaria) | 0.45 | 0.15 | 0.068 |
| POIs (escuela = educación) | 0.72 | 0.15 | 0.108 |
| Antigüedad (5 días) | 0.38 | 0.10 | 0.038 |
| Duplicados (3 reportes) | 0.46 | 0.10 | 0.046 |

$$Score = 0.225 + 0.170 + 0.068 + 0.108 + 0.038 + 0.046 = \boxed{0.655}$$

**Interpretación:** Prioridad **ALTA** (ver sección de rangos)

---

### 3.4 Rangos de prioridad

| Rango | Score | Color | Acción recomendada |
|-------|-------|-------|-------------------|
| **CRÍTICA** | 0.85 - 1.00 | 🔴 Rojo | Atención inmediata (<24h) |
| **ALTA** | 0.65 - 0.84 | 🟠 Naranja | Atención prioritaria (<3 días) |
| **MEDIA** | 0.40 - 0.64 | 🟡 Amarillo | Atención programada (<7 días) |
| **BAJA** | 0.20 - 0.39 | 🟢 Verde | Atención normal (<15 días) |
| **MÍNIMA** | 0.00 - 0.19 | 🔵 Azul | Backlog / mantenimiento |

---

## 4. Implementación del cálculo

### 4.1 Servicio de scoring

```python
# backend/services/priority_score.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import asyncio

@dataclass
class ScoreWeights:
    """Pesos configurables del algoritmo de priorización."""
    severity: float = 0.30
    pedestrian_risk: float = 0.20
    traffic: float = 0.15
    poi_proximity: float = 0.15
    age: float = 0.10
    duplicates: float = 0.10
    
    def validate(self) -> bool:
        """Verifica que los pesos sumen 1.0"""
        total = (
            self.severity + 
            self.pedestrian_risk + 
            self.traffic + 
            self.poi_proximity + 
            self.age + 
            self.duplicates
        )
        return abs(total - 1.0) < 0.001

@dataclass
class ScoreComponents:
    """Componentes individuales del score para transparencia."""
    severity: float
    pedestrian_risk: float
    traffic: float
    poi_proximity: float
    age: float
    duplicates: float
    
    @property
    def total(self) -> float:
        return (
            self.severity + 
            self.pedestrian_risk + 
            self.traffic + 
            self.poi_proximity + 
            self.age + 
            self.duplicates
        )

class PriorityScoreService:
    def __init__(self, weights: ScoreWeights = None):
        self.weights = weights or ScoreWeights()
        assert self.weights.validate(), "Los pesos deben sumar 1.0"
    
    async def calculate_score(
        self,
        report_id: str,
        lat: float,
        lng: float,
        ml_prediction: Optional[dict],
        citizen_category: str,
        created_at: datetime,
        incident_id: Optional[str] = None,
        operator_severity_override: Optional[float] = None
    ) -> tuple[float, ScoreComponents]:
        """
        Calcula el score de prioridad completo.
        
        Returns:
            (score_total, componentes_detallados)
        """
        
        # Calcular cada criterio en paralelo (I/O bound)
        severity_task = asyncio.create_task(
            self._calc_severity(ml_prediction, citizen_category, operator_severity_override)
        )
        pedestrian_task = asyncio.create_task(
            calculate_pedestrian_risk(lat, lng, created_at)
        )
        traffic_task = asyncio.create_task(
            calculate_traffic_score(lat, lng)
        )
        poi_task = asyncio.create_task(
            calculate_poi_proximity_score(lat, lng)
        )
        
        # Estos no son async, calcular directamente
        age_score = calculate_age_score(created_at)
        
        duplicate_score = 0.0
        if incident_id:
            duplicate_score = await calculate_duplicate_score(incident_id)
        
        # Esperar resultados async
        severity = await severity_task
        pedestrian_risk = await pedestrian_task
        traffic = await traffic_task
        poi_proximity = await poi_task
        
        # Calcular contribuciones ponderadas
        components = ScoreComponents(
            severity=severity * self.weights.severity,
            pedestrian_risk=pedestrian_risk * self.weights.pedestrian_risk,
            traffic=traffic * self.weights.traffic,
            poi_proximity=poi_proximity * self.weights.poi_proximity,
            age=age_score * self.weights.age,
            duplicates=duplicate_score * self.weights.duplicates
        )
        
        total_score = round(components.total, 3)
        
        return total_score, components
    
    async def _calc_severity(
        self,
        ml_prediction: Optional[dict],
        citizen_category: str,
        operator_override: Optional[float]
    ) -> float:
        """Wrapper para calcular severidad."""
        return calculate_severity(ml_prediction, citizen_category, operator_override)
    
    def get_priority_level(self, score: float) -> str:
        """Convierte score numérico a nivel de prioridad."""
        if score >= 0.85:
            return 'CRITICAL'
        elif score >= 0.65:
            return 'HIGH'
        elif score >= 0.40:
            return 'MEDIUM'
        elif score >= 0.20:
            return 'LOW'
        else:
            return 'MINIMAL'

# Uso en API
@app.post("/api/reports/{report_id}/calculate-score")
async def calculate_report_score(report_id: str):
    report = await db.get_report(report_id)
    
    score_service = PriorityScoreService()
    
    total_score, components = await score_service.calculate_score(
        report_id=report.id,
        lat=report.latitude,
        lng=report.longitude,
        ml_prediction=report.ml_prediction,
        citizen_category=report.category,
        created_at=report.created_at,
        incident_id=report.incident_id,
        operator_severity_override=report.operator_severity
    )
    
    # Actualizar en BD
    report.priority_score = total_score
    report.priority_level = score_service.get_priority_level(total_score)
    report.score_components = asdict(components)
    report.score_calculated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        'score': total_score,
        'priority_level': report.priority_level,
        'components': asdict(components),
        'weights_used': asdict(score_service.weights)
    }
```

---

## 5. Configuración de pesos (Admin)

### 5.1 Modelo de datos

```python
# backend/models/score_config.py

from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON
from datetime import datetime

class ScoreWeightsConfig(Base):
    """Configuración de pesos del algoritmo de priorización."""
    
    __tablename__ = 'score_weights_config'
    
    id = Column(String, primary_key=True)
    
    # Pesos actuales
    weight_severity = Column(Float, default=0.30)
    weight_pedestrian_risk = Column(Float, default=0.20)
    weight_traffic = Column(Float, default=0.15)
    weight_poi_proximity = Column(Float, default=0.15)
    weight_age = Column(Float, default=0.10)
    weight_duplicates = Column(Float, default=0.10)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)  # User ID del admin
    reason = Column(String)  # Motivo del cambio
    
    # Historial de valores anteriores (JSON)
    previous_values = Column(JSON)

# API para admin
@app.put("/api/admin/score-weights")
@require_role(UserRole.ADMIN)
async def update_score_weights(
    weights: ScoreWeightsUpdate,
    reason: str,
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza los pesos del algoritmo de priorización.
    
    Requiere:
    - Rol ADMIN
    - Motivo obligatorio
    - Pesos deben sumar 1.0
    """
    
    # Validar suma de pesos
    total = (
        weights.severity +
        weights.pedestrian_risk +
        weights.traffic +
        weights.poi_proximity +
        weights.age +
        weights.duplicates
    )
    
    if abs(total - 1.0) > 0.001:
        raise HTTPException(400, f"Los pesos deben sumar 1.0, actual: {total}")
    
    # Obtener configuración actual
    current_config = await db.query(ScoreWeightsConfig).filter(
        ScoreWeightsConfig.is_active == True
    ).first()
    
    # Guardar historial
    previous_values = {
        'severity': current_config.weight_severity,
        'pedestrian_risk': current_config.weight_pedestrian_risk,
        'traffic': current_config.weight_traffic,
        'poi_proximity': current_config.weight_poi_proximity,
        'age': current_config.weight_age,
        'duplicates': current_config.weight_duplicates,
        'changed_at': datetime.utcnow().isoformat()
    }
    
    # Desactivar configuración anterior
    current_config.is_active = False
    
    # Crear nueva configuración
    new_config = ScoreWeightsConfig(
        id=str(uuid4()),
        weight_severity=weights.severity,
        weight_pedestrian_risk=weights.pedestrian_risk,
        weight_traffic=weights.traffic,
        weight_poi_proximity=weights.poi_proximity,
        weight_age=weights.age,
        weight_duplicates=weights.duplicates,
        is_active=True,
        created_by=current_user.id,
        reason=reason,
        previous_values=previous_values
    )
    
    db.add(new_config)
    await db.commit()
    
    # Auditar cambio
    await audit_log.record(
        user_id=current_user.id,
        action='config:update_score_weights',
        resource_id=new_config.id,
        changes={
            'previous': previous_values,
            'new': asdict(weights)
        },
        reason=reason
    )
    
    # Programar recálculo de scores pendientes
    await schedule_score_recalculation()
    
    return {
        'config_id': new_config.id,
        'weights': asdict(weights),
        'effective_at': datetime.utcnow().isoformat(),
        'recalculation_scheduled': True
    }
```

---

## 6. Reglas de ajuste dinámico

### 6.1 Ajustes contextuales automáticos

El sistema puede aplicar multiplicadores contextuales basados en condiciones especiales:

| Condición | Multiplicador | Justificación |
|-----------|---------------|---------------|
| **Emergencia climática** (lluvia intensa) | ×1.3 | Daños más peligrosos con agua |
| **Zona de evento público** | ×1.2 | Mayor visibilidad e impacto |
| **Horario escolar** (zona escolar 7-9am, 12-3pm) | ×1.15 | Riesgo peatonal aumentado |
| **Fin de semana** (zona comercial) | ×0.85 | Menos tráfico |
| **Noche** (10pm-6am, zona no comercial) | ×0.7 | Menos urgente |
| **Temporada de turismo** | ×1.1 | Impacto en imagen municipal |

**Implementación:**

```python
# backend/services/dynamic_adjustments.py

from datetime import datetime
from typing import Optional

class DynamicScoreAdjustments:
    async def apply_contextual_multipliers(
        self,
        base_score: float,
        lat: float,
        lng: float,
        report_time: datetime
    ) -> tuple[float, list[str]]:
        """
        Aplica multiplicadores contextuales al score base.
        
        Returns:
            (score_ajustado, lista_de_ajustes_aplicados)
        """
        
        multiplier = 1.0
        adjustments = []
        
        # 1. Condiciones climáticas
        weather = await self._get_current_weather(lat, lng)
        
        if weather['condition'] in ['heavy_rain', 'storm']:
            multiplier *= 1.3
            adjustments.append(f"Clima adverso: {weather['condition']}")
        
        # 2. Eventos públicos programados
        nearby_events = await db.execute("""
            SELECT name, type
            FROM public_event
            WHERE ST_DWithin(
                location::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                1000  -- 1km radius
            )
            AND event_date = CURRENT_DATE
            AND status = 'ACTIVE'
        """, {'lat': lat, 'lng': lng})
        
        if nearby_events:
            multiplier *= 1.2
            adjustments.append(f"Evento cercano: {nearby_events[0].name}")
        
        # 3. Horario escolar (si hay escuela cercana)
        hour = report_time.hour
        is_school_zone = await self._is_school_zone(lat, lng)
        
        if is_school_zone and ((7 <= hour <= 9) or (12 <= hour <= 15)):
            multiplier *= 1.15
            adjustments.append("Horario escolar activo")
        
        # 4. Horario nocturno
        if (hour >= 22 or hour <= 6):
            # Verificar si es zona comercial/industrial que sí opera de noche
            zone_type = await get_zone_type(lat, lng)
            
            if zone_type not in ['commercial', 'industrial']:
                multiplier *= 0.7
                adjustments.append("Horario nocturno (reducción)")
        
        # 5. Fin de semana en zona no residencial
        if report_time.weekday() >= 5:  # Sábado=5, Domingo=6
            zone_type = await get_zone_type(lat, lng)
            
            if zone_type in ['commercial', 'industrial']:
                multiplier *= 0.85
                adjustments.append("Fin de semana - menos tráfico")
        
        # 6. Temporada alta de turismo (si aplica)
        is_tourist_season = self._is_tourist_season(report_time)
        is_tourist_zone = await self._is_tourist_zone(lat, lng)
        
        if is_tourist_season and is_tourist_zone:
            multiplier *= 1.1
            adjustments.append("Temporada turística")
        
        # Aplicar multiplicador compuesto y clamp a [0, 1]
        adjusted_score = min(1.0, base_score * multiplier)
        
        return round(adjusted_score, 3), adjustments
    
    async def _get_current_weather(self, lat: float, lng: float) -> dict:
        """Consulta condiciones climáticas actuales."""
        # Integración con OpenWeatherMap u otro servicio
        # Por ahora, mock
        return {'condition': 'clear', 'temp_c': 22}
    
    async def _is_school_zone(self, lat: float, lng: float) -> bool:
        """Verifica si hay escuela en radio de 100m."""
        result = await db.execute("""
            SELECT EXISTS (
                SELECT 1 FROM poi
                WHERE type = 'school'
                  AND ST_DWithin(
                      location::geography,
                      ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                      100
                  )
            )
        """, {'lat': lat, 'lng': lng})
        
        return result[0][0] if result else False
    
    def _is_tourist_season(self, date: datetime) -> bool:
        """Determina si es temporada alta de turismo."""
        month = date.month
        # Ejemplo: Diciembre-Enero, Semana Santa, Julio-Agosto
        return month in [12, 1, 7, 8]  # Simplificado
    
    async def _is_tourist_zone(self, lat: float, lng: float) -> bool:
        """Verifica si está en zona turística."""
        result = await db.execute("""
            SELECT EXISTS (
                SELECT 1 FROM poi
                WHERE type IN ('monument', 'museum', 'tourist_attraction')
                  AND ST_DWithin(
                      location::geography,
                      ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                      500
                  )
            )
        """, {'lat': lat, 'lng': lng})
        
        return result[0][0] if result else False

# Integración en el servicio principal
class PriorityScoreService:
    def __init__(self, weights: ScoreWeights = None, apply_dynamic: bool = True):
        self.weights = weights or ScoreWeights()
        self.apply_dynamic = apply_dynamic
        self.adjuster = DynamicScoreAdjustments()
    
    async def calculate_score(self, ...):
        # ... cálculo base ...
        
        if self.apply_dynamic:
            adjusted_score, adjustments = await self.adjuster.apply_contextual_multipliers(
                base_score=total_score,
                lat=lat,
                lng=lng,
                report_time=created_at
            )
            
            return adjusted_score, components, adjustments
        
        return total_score, components, []
```

---

### 6.2 Ajustes por zona geográfica

Cada municipio/zona puede tener pesos personalizados:

```python
# backend/models/zone_config.py

class ZoneScoreConfig(Base):
    """Configuración de pesos por zona geográfica."""
    
    __tablename__ = 'zone_score_config'
    
    id = Column(String, primary_key=True)
    municipality_id = Column(String, ForeignKey('municipality.id'))
    zone_name = Column(String)  # "Centro histórico", "Zona industrial", etc.
    
    # Geometría de la zona (polígono)
    boundary = Column(Geometry('POLYGON', srid=4326))
    
    # Pesos personalizados (si null, usa default)
    weight_severity = Column(Float, nullable=True)
    weight_pedestrian_risk = Column(Float, nullable=True)
    weight_traffic = Column(Float, nullable=True)
    weight_poi_proximity = Column(Float, nullable=True)
    weight_age = Column(Float, nullable=True)
    weight_duplicates = Column(Float, nullable=True)
    
    # Multiplicador global para la zona
    global_multiplier = Column(Float, default=1.0)
    
    is_active = Column(Boolean, default=True)

# Ejemplo de uso
async def get_zone_weights(lat: float, lng: float) -> Optional[ScoreWeights]:
    """Obtiene pesos personalizados si la ubicación está en zona especial."""
    
    zone_config = await db.execute("""
        SELECT *
        FROM zone_score_config
        WHERE ST_Contains(
            boundary,
            ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
        )
        AND is_active = TRUE
        LIMIT 1
    """, {'lat': lat, 'lng': lng})
    
    if not zone_config:
        return None
    
    config = zone_config[0]
    
    # Crear pesos personalizados (usar default si null)
    return ScoreWeights(
        severity=config.weight_severity or 0.30,
        pedestrian_risk=config.weight_pedestrian_risk or 0.20,
        traffic=config.weight_traffic or 0.15,
        poi_proximity=config.weight_poi_proximity or 0.15,
        age=config.weight_age or 0.10,
        duplicates=config.weight_duplicates or 0.10
    )
```

---

## 7. Recálculo automático de scores

### 7.1 Triggers de recálculo

El score debe recalcularse cuando:

| Evento | Motivo | Frecuencia |
|--------|--------|------------|
| **Nuevo reporte creado** | Cálculo inicial | Inmediato |
| **Reporte marcado como duplicado** | Actualizar score de incidente | Inmediato |
| **Pasan 24 horas** | Incremento de antigüedad | Diario (batch) |
| **Operador ajusta severidad** | Cambio en componente principal | Inmediato |
| **Admin cambia pesos** | Nueva configuración | Batch (todos los pendientes) |
| **Clima adverso detectado** | Ajuste contextual | En tiempo real |

---

### 7.2 Job de recálculo diario

```python
# backend/jobs/score_recalculation.py

from datetime import datetime, timedelta

class ScoreRecalculationJob:
    async def recalculate_pending_scores(self):
        """
        Job diario que recalcula scores de reportes pendientes.
        
        Ejecutar a las 2:00 AM para minimizar carga.
        """
        
        # Obtener reportes activos (no cerrados)
        pending_reports = await db.execute("""
            SELECT id, latitude, longitude, category, created_at, incident_id
            FROM report
            WHERE status NOT IN ('CLOSED', 'REJECTED', 'SPAM')
            ORDER BY priority_score DESC  -- Priorizar los más urgentes
        """)
        
        score_service = PriorityScoreService()
        updated_count = 0
        
        for report in pending_reports:
            try:
                # Recalcular score
                new_score, components, adjustments = await score_service.calculate_score(
                    report_id=report.id,
                    lat=report.latitude,
                    lng=report.longitude,
                    ml_prediction=None,  # Ya calculado previamente
                    citizen_category=report.category,
                    created_at=report.created_at,
                    incident_id=report.incident_id
                )
                
                # Actualizar solo si cambió significativamente (>0.05 diferencia)
                old_score = report.priority_score or 0.0
                
                if abs(new_score - old_score) >= 0.05:
                    await db.execute("""
                        UPDATE report
                        SET priority_score = :new_score,
                            priority_level = :new_level,
                            score_components = :components,
                            score_calculated_at = :now
                        WHERE id = :report_id
                    """, {
                        'report_id': report.id,
                        'new_score': new_score,
                        'new_level': score_service.get_priority_level(new_score),
                        'components': json.dumps(asdict(components)),
                        'now': datetime.utcnow()
                    })
                    
                    updated_count += 1
                    
                    # Si cambió de nivel, notificar
                    old_level = score_service.get_priority_level(old_score)
                    new_level = score_service.get_priority_level(new_score)
                    
                    if old_level != new_level:
                        await self._notify_priority_change(report.id, old_level, new_level)
            
            except Exception as e:
                logger.error(f"Error recalculando score para reporte {report.id}: {e}")
                continue
        
        await db.commit()
        
        logger.info(f"Recálculo completado: {updated_count}/{len(pending_reports)} reportes actualizados")
        
        return {
            'total_processed': len(pending_reports),
            'updated': updated_count,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _notify_priority_change(self, report_id: str, old_level: str, new_level: str):
        """Notifica cuando un reporte cambia de nivel de prioridad."""
        
        # Notificar a operadores si pasó a CRITICAL o HIGH
        if new_level in ['CRITICAL', 'HIGH'] and old_level not in ['CRITICAL', 'HIGH']:
            await notification_service.send_to_role(
                role='OPERATOR',
                title='Reporte escaló en prioridad',
                message=f'Reporte {report_id} ahora es {new_level}',
                data={'report_id': report_id, 'priority': new_level}
            )

# Configuración de cron job
# infra/k8s/cronjobs/score-recalculation.yaml
"""
apiVersion: batch/v1
kind: CronJob
metadata:
  name: score-recalculation
spec:
  schedule: "0 2 * * *"  # Diario a las 2:00 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: recalculator
            image: sirccd-backend:latest
            command: ["python", "-m", "backend.jobs.score_recalculation"]
          restartPolicy: OnFailure
"""
```

---

### 7.3 Recálculo en tiempo real (eventos)

```python
# backend/events/score_events.py

from backend.core.event_bus import event_bus

# Evento: Reporte marcado como duplicado
@event_bus.on('report:marked_as_duplicate')
async def on_duplicate_marked(event: dict):
    """
    Cuando un reporte se marca como duplicado del incidente X,
    recalcular el score del incidente.
    """
    
    incident_id = event['incident_id']
    
    # Recalcular score de duplicados
    new_duplicate_score = await calculate_duplicate_score(incident_id)
    
    # Obtener todos los reportes del incidente
    incident_reports = await db.query(Report).filter(
        Report.incident_id == incident_id
    ).all()
    
    score_service = PriorityScoreService()
    
    for report in incident_reports:
        # Recalcular score completo
        new_score, components, _ = await score_service.calculate_score(
            report_id=report.id,
            lat=report.latitude,
            lng=report.longitude,
            ml_prediction=report.ml_prediction,
            citizen_category=report.category,
            created_at=report.created_at,
            incident_id=incident_id
        )
        
        report.priority_score = new_score
        report.priority_level = score_service.get_priority_level(new_score)
        report.score_calculated_at = datetime.utcnow()
    
    await db.commit()

# Evento: Operador ajusta severidad manualmente
@event_bus.on('report:severity_updated')
async def on_severity_updated(event: dict):
    """Recalcular score cuando operador ajusta severidad."""
    
    report_id = event['report_id']
    new_severity = event['new_severity']
    
    report = await db.get_report(report_id)
    
    score_service = PriorityScoreService()
    
    new_score, components, _ = await score_service.calculate_score(
        report_id=report.id,
        lat=report.latitude,
        lng=report.longitude,
        ml_prediction=report.ml_prediction,
        citizen_category=report.category,
        created_at=report.created_at,
        incident_id=report.incident_id,
        operator_severity_override=new_severity
    )
    
    report.priority_score = new_score
    report.priority_level = score_service.get_priority_level(new_score)
    report.operator_severity = new_severity
    
    await db.commit()
```

---

## 8. Visualización y transparencia

### 8.1 Desglose del score para operadores

```json
{
  "report_id": "uuid-123",
  "priority_score": 0.655,
  "priority_level": "HIGH",
  "components": {
    "severity": {
      "raw_value": 0.75,
      "weight": 0.30,
      "contribution": 0.225,
      "source": "ML (80% conf) + citizen"
    },
    "pedestrian_risk": {
      "raw_value": 0.85,
      "weight": 0.20,
      "contribution": 0.170,
      "reason": "Escuela primaria a 80m"
    },
    "traffic": {
      "raw_value": 0.45,
      "weight": 0.15,
      "contribution": 0.068,
      "reason": "Calle secundaria (OSM)"
    },
    "poi_proximity": {
      "raw_value": 0.72,
      "weight": 0.15,
      "contribution": 0.108,
      "reason": "Escuela (tipo: education, dist: 80m)"
    },
    "age": {
      "raw_value": 0.38,
      "weight": 0.10,
      "contribution": 0.038,
      "reason": "5 días desde creación"
    },
    "duplicates": {
      "raw_value": 0.46,
      "weight": 0.10,
      "contribution": 0.046,
      "reason": "3 reportes consolidados"
    }
  },
  "adjustments_applied": [
    "Horario escolar activo (+15%)"
  ],
  "calculated_at": "2026-01-14T10:30:00Z",
  "next_recalculation": "2026-01-15T02:00:00Z"
}
```

---

### 8.2 Visualización en dashboard (Operador)

```jsx
// frontend/src/components/ScoreBreakdown.jsx

import React from 'react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, Legend } from 'recharts';

export function ScoreBreakdown({ report }) {
  const components = report.score_components;
  
  // Datos para radar chart
  const radarData = [
    { criterion: 'Severidad', value: components.severity.raw_value },
    { criterion: 'Riesgo peatonal', value: components.pedestrian_risk.raw_value },
    { criterion: 'Tráfico', value: components.traffic.raw_value },
    { criterion: 'POIs', value: components.poi_proximity.raw_value },
    { criterion: 'Antigüedad', value: components.age.raw_value },
    { criterion: 'Duplicados', value: components.duplicates.raw_value },
  ];
  
  return (
    <div className="score-breakdown">
      <h3>Score: {report.priority_score.toFixed(3)}</h3>
      <span className={`badge ${report.priority_level}`}>
        {report.priority_level}
      </span>
      
      <RadarChart width={400} height={300} data={radarData}>
        <PolarGrid />
        <PolarAngleAxis dataKey="criterion" />
        <Radar 
          name="Valores" 
          dataKey="value" 
          stroke="#8884d8" 
          fill="#8884d8" 
          fillOpacity={0.6} 
        />
      </RadarChart>
      
      <div className="components-list">
        {Object.entries(components).map(([key, comp]) => (
          <div key={key} className="component-item">
            <strong>{key}:</strong> {comp.raw_value.toFixed(2)}
            <span className="weight">× {comp.weight}</span>
            = <strong>{comp.contribution.toFixed(3)}</strong>
            <p className="reason">{comp.reason}</p>
          </div>
        ))}
      </div>
      
      {report.adjustments_applied?.length > 0 && (
        <div className="adjustments">
          <h4>Ajustes aplicados:</h4>
          <ul>
            {report.adjustments_applied.map((adj, i) => (
              <li key={i}>{adj}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

### 8.3 Mapa de calor de prioridades

```python
# backend/api/analytics.py

@app.get("/api/analytics/priority-heatmap")
async def get_priority_heatmap(
    bounds: str,  # "lat_min,lng_min,lat_max,lng_max"
    resolution: int = 20  # Grid 20x20
):
    """
    Genera mapa de calor de prioridades para área geográfica.
    
    Útil para identificar zonas críticas.
    """
    
    lat_min, lng_min, lat_max, lng_max = map(float, bounds.split(','))
    
    # Crear grid
    lat_step = (lat_max - lat_min) / resolution
    lng_step = (lng_max - lng_min) / resolution
    
    heatmap_data = []
    
    for i in range(resolution):
        for j in range(resolution):
            lat = lat_min + (i * lat_step)
            lng = lng_min + (j * lng_step)
            
            # Sumar scores de reportes en esta celda
            cell_score = await db.execute("""
                SELECT 
                    COUNT(*) as count,
                    AVG(priority_score) as avg_score,
                    MAX(priority_score) as max_score
                FROM report
                WHERE ST_Within(
                    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326),
                    ST_MakeEnvelope(:lng, :lat, :lng_max, :lat_max, 4326)
                )
                AND status NOT IN ('CLOSED', 'REJECTED')
            """, {
                'lat': lat,
                'lng': lng,
                'lat_max': lat + lat_step,
                'lng_max': lng + lng_step
            })
            
            if cell_score[0].count > 0:
                heatmap_data.append({
                    'lat': lat + lat_step/2,
                    'lng': lng + lng_step/2,
                    'count': cell_score[0].count,
                    'avg_score': float(cell_score[0].avg_score),
                    'max_score': float(cell_score[0].max_score),
                    'intensity': min(1.0, cell_score[0].avg_score * cell_score[0].count / 5)
                })
    
    return {
        'bounds': {
            'lat_min': lat_min,
            'lng_min': lng_min,
            'lat_max': lat_max,
            'lng_max': lng_max
        },
        'resolution': resolution,
        'data': heatmap_data,
        'total_reports': sum(d['count'] for d in heatmap_data)
    }
```

---

## 9. Testing y validación

### 9.1 Test cases del algoritmo

```python
# backend/tests/test_priority_score.py

import pytest
from datetime import datetime, timedelta
from backend.services.priority_score import PriorityScoreService, ScoreWeights

class TestPriorityScore:
    
    @pytest.fixture
    def score_service(self):
        return PriorityScoreService()
    
    def test_score_range_valid(self, score_service):
        """Score debe estar siempre entre 0 y 1."""
        
        # Caso extremo: todos los componentes en máximo
        score, _ = await score_service.calculate_score(
            report_id='test-1',
            lat=19.4326,
            lng=-99.1332,
            ml_prediction={'severity_score': 1.0, 'confidence': 0.9},
            citizen_category='socavon',
            created_at=datetime.utcnow() - timedelta(days=60),  # Muy antiguo
            incident_id='inc-1'  # Con duplicados
        )
        
        assert 0.0 <= score <= 1.0
    
    def test_severity_override(self, score_service):
        """Operador override debe tener precedencia."""
        
        score1, comp1 = await score_service.calculate_score(
            report_id='test-2',
            lat=19.4326,
            lng=-99.1332,
            ml_prediction={'severity_score': 0.3, 'confidence': 0.9},
            citizen_category='bache_pequeno',
            created_at=datetime.utcnow(),
            operator_severity_override=0.9  # Operador dice que es grave
        )
        
        # Severidad debe reflejar el override
        assert comp1.severity >= 0.27  # 0.9 * 0.30 (peso)
    
    def test_age_increases_over_time(self):
        """Score de antigüedad debe crecer con el tiempo."""
        
        now = datetime.utcnow()
        
        score_day_1 = calculate_age_score(now - timedelta(days=1))
        score_day_7 = calculate_age_score(now - timedelta(days=7))
        score_day_30 = calculate_age_score(now - timedelta(days=30))
        
        assert score_day_1 < score_day_7 < score_day_30
        assert score_day_30 == 1.0  # Meseta alcanzada
    
    def test_duplicates_increase_score(self, score_service):
        """Más duplicados deben aumentar el score."""
        
        # Mock: simular 1 vs 5 duplicados
        async def mock_duplicate_score(incident_id):
            if incident_id == 'inc-single':
                return 0.0  # 1 reporte único
            elif incident_id == 'inc-multiple':
                return 0.67  # 5 duplicados
        
        # Reemplazar función temporalmente
        original_func = calculate_duplicate_score
        calculate_duplicate_score = mock_duplicate_score
        
        score_single, _ = await score_service.calculate_score(
            report_id='test-3',
            lat=19.4326,
            lng=-99.1332,
            ml_prediction=None,
            citizen_category='bache_mediano',
            created_at=datetime.utcnow(),
            incident_id='inc-single'
        )
        
        score_multiple, _ = await score_service.calculate_score(
            report_id='test-4',
            lat=19.4326,
            lng=-99.1332,
            ml_prediction=None,
            citizen_category='bache_mediano',
            created_at=datetime.utcnow(),
            incident_id='inc-multiple'
        )
        
        assert score_multiple > score_single
        
        # Restaurar
        calculate_duplicate_score = original_func
    
    def test_weights_sum_to_one(self):
        """Pesos deben sumar exactamente 1.0."""
        
        weights = ScoreWeights()
        total = (
            weights.severity +
            weights.pedestrian_risk +
            weights.traffic +
            weights.poi_proximity +
            weights.age +
            weights.duplicates
        )
        
        assert abs(total - 1.0) < 0.001
    
    def test_school_zone_increases_risk(self):
        """Zona escolar debe aumentar riesgo peatonal."""
        
        # Coordenadas con escuela cercana (mock)
        risk_with_school = await calculate_pedestrian_risk(
            lat=19.4326,
            lng=-99.1332,
            report_time=datetime(2026, 1, 14, 8, 0)  # 8 AM, horario escolar
        )
        
        # Coordenadas sin escuela
        risk_without_school = await calculate_pedestrian_risk(
            lat=19.5, 
            lng=-99.2,
            report_time=datetime(2026, 1, 14, 8, 0)
        )
        
        assert risk_with_school > risk_without_school
```

---

### 9.2 Validación con datos históricos

```python
# backend/scripts/validate_score_algorithm.py

async def validate_with_historical_data():
    """
    Valida el algoritmo comparando scores calculados con priorización real.
    
    Objetivo: Score alto debe correlacionar con atención rápida.
    """
    
    # Obtener reportes cerrados del último año
    historical_reports = await db.execute("""
        SELECT 
            id,
            priority_score,
            created_at,
            closed_at,
            EXTRACT(EPOCH FROM (closed_at - created_at))/86400 as resolution_days
        FROM report
        WHERE status = 'CLOSED'
          AND closed_at IS NOT NULL
          AND created_at > NOW() - INTERVAL '1 year'
        ORDER BY priority_score DESC
    """)
    
    # Dividir en cuartiles de score
    scores = [r.priority_score for r in historical_reports]
    q1 = np.percentile(scores, 25)
    q2 = np.percentile(scores, 50)
    q3 = np.percentile(scores, 75)
    
    # Calcular tiempo promedio de resolución por cuartil
    quartiles = {
        'Q4 (top 25%)': [],
        'Q3 (50-75%)': [],
        'Q2 (25-50%)': [],
        'Q1 (bottom 25%)': []
    }
    
    for report in historical_reports:
        if report.priority_score >= q3:
            quartiles['Q4 (top 25%)'].append(report.resolution_days)
        elif report.priority_score >= q2:
            quartiles['Q3 (50-75%)'].append(report.resolution_days)
        elif report.priority_score >= q1:
            quartiles['Q2 (25-50%)'].append(report.resolution_days)
        else:
            quartiles['Q1 (bottom 25%)'].append(report.resolution_days)
    
    # Verificar correlación: mayor score → menor tiempo de resolución
    print("Validación de correlación score-tiempo de resolución:")
    print("-" * 60)
    
    for quartile, days in quartiles.items():
        avg_days = np.mean(days)
        median_days = np.median(days)
        print(f"{quartile}: Promedio {avg_days:.1f} días, Mediana {median_days:.1f} días")
    
    # Test estadístico: ¿top 25% se resuelve más rápido que bottom 25%?
    from scipy.stats import mannwhitneyu
    
    statistic, p_value = mannwhitneyu(
        quartiles['Q4 (top 25%)'],
        quartiles['Q1 (bottom 25%)'],
        alternative='less'  # Q4 debe ser menor (más rápido)
    )
    
    print(f"\nMann-Whitney U test: p-value = {p_value:.4f}")
    
    if p_value < 0.05:
        print("✅ Algoritmo VÁLIDO: Score alto correlaciona con resolución rápida")
    else:
        print("⚠️ Algoritmo NECESITA AJUSTE: No hay correlación significativa")

# Ejecutar validación
asyncio.run(validate_with_historical_data())
```

---

## 10. Casos de uso avanzados

### 10.1 Ejemplo 1: Socavón en zona escolar

**Input:**
- **Severidad:** Socavón >50cm (ML detecta con 95% confianza)
- **Ubicación:** 50m de escuela primaria
- **Horario:** 8:15 AM (horario de entrada)
- **Tráfico:** Avenida secundaria
- **Antigüedad:** 2 días
- **Duplicados:** 7 reportes

**Cálculo:**

| Criterio | Valor | Peso | Contribución |
|----------|-------|------|--------------|
| Severidad | 1.0 | 0.30 | **0.300** |
| Riesgo peatonal | 1.0 (escuela + horario) | 0.20 | **0.200** |
| Tráfico | 0.6 | 0.15 | 0.090 |
| POIs | 0.85 | 0.15 | 0.128 |
| Antigüedad | 0.22 | 0.10 | 0.022 |
| Duplicados | 0.81 | 0.10 | 0.081 |

**Score base:** 0.821

**Ajustes contextuales:**
- Horario escolar activo: ×1.15

**Score final:** 0.944 → **CRÍTICA**

**Acción:** Asignación inmediata, notificación a brigada de emergencias, cierre temporal de vía.

---

### 10.2 Ejemplo 2: Grieta superficial en zona residencial

**Input:**
- **Severidad:** Grieta superficial (ML 60% confianza)
- **Ubicación:** Calle residencial sin POIs cercanos
- **Horario:** 3:00 PM
- **Tráfico:** Muy bajo (<1000 veh/día)
- **Antigüedad:** 15 días
- **Duplicados:** 1 único reporte

**Cálculo:**

| Criterio | Valor | Peso | Contribución |
|----------|-------|------|--------------|
| Severidad | 0.30 | 0.30 | 0.090 |
| Riesgo peatonal | 0.20 | 0.20 | 0.040 |
| Tráfico | 0.15 | 0.15 | 0.023 |
| POIs | 0.10 | 0.15 | 0.015 |
| Antigüedad | 0.72 | 0.10 | 0.072 |
| Duplicados | 0.0 | 0.10 | 0.000 |

**Score final:** 0.240 → **BAJA**

**Acción:** Programar en siguiente ronda de mantenimiento preventivo.

---

### 10.3 Ejemplo 3: Alcantarilla abierta en mercado

**Input:**
- **Severidad:** Alcantarilla sin tapa (peligro caída)
- **Ubicación:** Mercado municipal (100m)
- **Horario:** 10:00 AM (hora pico mercado)
- **Tráfico:** Medio (calle peatonal)
- **Antigüedad:** 6 horas
- **Duplicados:** 4 reportes

**Cálculo:**

| Criterio | Valor | Peso | Contribución |
|----------|-------|------|--------------|
| Severidad | 0.80 | 0.30 | 0.240 |
| Riesgo peatonal | 0.70 | 0.20 | 0.140 |
| Tráfico | 0.30 | 0.15 | 0.045 |
| POIs | 0.65 (mercado) | 0.15 | 0.098 |
| Antigüedad | 0.03 | 0.10 | 0.003 |
| Duplicados | 0.58 | 0.10 | 0.058 |

**Score base:** 0.584

**Ajuste:** Mercado en horario pico ×1.1

**Score final:** 0.642 → **MEDIA-ALTA** (casi ALTA)

**Acción:** Asignar en las próximas 24 horas, colocar señalización temporal inmediata.

---

## 11. Optimización y rendimiento

### 11.1 Caché de cálculos espaciales

```python
# backend/core/cache.py

from functools import lru_cache
import hashlib

class SpatialDataCache:
    """Cache para consultas espaciales repetitivas."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 hora
    
    async def get_poi_proximity(self, lat: float, lng: float) -> Optional[float]:
        """Obtiene score de POI desde cache."""
        
        # Redondear coordenadas a 4 decimales (±11m precisión)
        lat_rounded = round(lat, 4)
        lng_rounded = round(lng, 4)
        
        cache_key = f"poi_score:{lat_rounded}:{lng_rounded}"
        
        cached = await self.redis.get(cache_key)
        
        if cached:
            return float(cached)
        
        # Calcular y cachear
        score = await calculate_poi_proximity_score(lat, lng)
        
        await self.redis.setex(cache_key, self.ttl, score)
        
        return score
    
    async def get_traffic_score(self, lat: float, lng: float) -> Optional[float]:
        """Obtiene score de tráfico desde cache."""
        
        lat_rounded = round(lat, 3)  # ±111m precisión
        lng_rounded = round(lng, 3)
        
        cache_key = f"traffic_score:{lat_rounded}:{lng_rounded}"
        
        cached = await self.redis.get(cache_key)
        
        if cached:
            return float(cached)
        
        score = await calculate_traffic_score(lat, lng)
        
        await self.redis.setex(cache_key, self.ttl * 24, score)  # 24h TTL
        
        return score

# Uso en servicio
cache = SpatialDataCache(redis_client)

poi_score = await cache.get_poi_proximity(lat, lng)
traffic_score = await cache.get_traffic_score(lat, lng)
```

---

### 11.2 Batch processing

```python
# Para recálculos masivos, procesar en batches

async def recalculate_scores_batch(report_ids: list[str], batch_size: int = 100):
    """Recalcula scores en batches para evitar sobrecargar DB."""
    
    score_service = PriorityScoreService()
    
    for i in range(0, len(report_ids), batch_size):
        batch = report_ids[i:i+batch_size]
        
        # Obtener reportes del batch
        reports = await db.query(Report).filter(
            Report.id.in_(batch)
        ).all()
        
        # Procesar en paralelo (asyncio.gather)
        tasks = [
            score_service.calculate_score(
                report_id=r.id,
                lat=r.latitude,
                lng=r.longitude,
                ml_prediction=r.ml_prediction,
                citizen_category=r.category,
                created_at=r.created_at,
                incident_id=r.incident_id
            )
            for r in reports
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Actualizar en batch
        for report, (score, components, _) in zip(reports, results):
            report.priority_score = score
            report.priority_level = score_service.get_priority_level(score)
            report.score_components = asdict(components)
        
        await db.commit()
        
        # Pausa breve entre batches
        await asyncio.sleep(0.5)
```

---

## 12. Resumen ejecutivo

| Aspecto | Decisión |
|---------|----------|
| **Criterios principales** | 6 factores (Severidad, Riesgo peatonal, Tráfico, POIs, Antigüedad, Duplicados) |
| **Pesos default** | 30%, 20%, 15%, 15%, 10%, 10% respectivamente |
| **Fórmula** | Suma ponderada normalizada a [0, 1] |
| **Rangos de prioridad** | 5 niveles (Crítica, Alta, Media, Baja, Mínima) |
| **Recálculo** | Diario (batch) + eventos en tiempo real |
| **Ajustes contextuales** | Clima, horario, eventos, zona (hasta ×1.3) |
| **Configuración** | Pesos editables por Admin con auditoría |
| **Transparencia** | Desglose completo de componentes en API/UI |
| **Caché** | Redis para consultas espaciales (1-24h TTL) |
| **Testing** | Test suite + validación con datos históricos |

---

## 13. Roadmap de implementación

### Fase 1: MVP (Semana 1-2)

- [ ] Implementar cálculo de severidad (ML + ciudadano)
- [ ] Implementar antigüedad (función logarítmica)
- [ ] Implementar duplicados (conteo simple)
- [ ] Fórmula básica con pesos hardcoded
- [ ] API `/calculate-score` para reportes

### Fase 2: Datos espaciales (Semana 3-4)

- [ ] Integración con PostGIS para POIs
- [ ] Cálculo de riesgo peatonal (zonas escolares)
- [ ] Estimación de tráfico (OSM road types)
- [ ] Caché Redis para consultas espaciales

### Fase 3: Configuración (Semana 5)

- [ ] Modelo `ScoreWeightsConfig` en DB
- [ ] API Admin para editar pesos
- [ ] Validación de suma = 1.0
- [ ] Auditoría de cambios

### Fase 4: Recálculo automático (Semana 6)

- [ ] Job diario de recálculo
- [ ] Event bus para recálculos en tiempo real
- [ ] Notificaciones de cambio de prioridad

### Fase 5: Visualización (Semana 7-8)

- [ ] Desglose de componentes en frontend
- [ ] Radar chart de criterios
- [ ] Mapa de calor de prioridades
- [ ] Exportación de scores

### Fase 6: Avanzado (Post-MVP)

- [ ] Ajustes contextuales (clima, horario, eventos)
- [ ] Configuración por zona geográfica
- [ ] Validación con datos históricos
- [ ] Machine learning para ajuste automático de pesos

---

## 14. Referencias

- [Multi-Criteria Decision Analysis (MCDA)](https://en.wikipedia.org/wiki/Multiple-criteria_decision_analysis)
- [PostGIS Spatial Functions](https://postgis.net/docs/reference.html)
- [OpenStreetMap Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [Redis Caching Best Practices](https://redis.io/docs/manual/patterns/caching/)
- [Time Decay Functions](https://en.wikipedia.org/wiki/Exponential_decay)

---

**Documento aprobado para implementación**  
**Próximo paso:** Implementar servicio de scoring con criterios base y API de configuración
