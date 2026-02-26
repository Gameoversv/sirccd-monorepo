# B-02: Esquema PostgreSQL + PostGIS

## ✅ Completado

Se ha implementado el esquema completo de base de datos PostgreSQL con PostGIS, modelos SQLAlchemy y migraciones con Alembic.

## 📊 Tablas Implementadas

### 1. **users** - Usuarios del sistema

```sql
- id: SERIAL PRIMARY KEY
- email: VARCHAR(255) UNIQUE NOT NULL
- username: VARCHAR(100) UNIQUE NOT NULL
- full_name: VARCHAR(255)
- phone: VARCHAR(20)
- hashed_password: VARCHAR(255) NOT NULL
- is_active: BOOLEAN DEFAULT true
- is_verified: BOOLEAN DEFAULT false
- role: ENUM('ADMIN', 'CIUDADANO', 'BRIGADA', 'SUPERVISOR') DEFAULT 'CIUDADANO'
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
- last_login: TIMESTAMP
```

**Relaciones**:
- `reports`: Un usuario puede crear múltiples reportes
- `incidents`: Un usuario puede reportar múltiples incidentes
- `brigade_assignments`: Usuarios pueden ser miembros de brigadas (many-to-many)

### 2. **brigades** - Equipos de trabajo

```sql
- id: SERIAL PRIMARY KEY
- name: VARCHAR(255) UNIQUE NOT NULL
- code: VARCHAR(50) UNIQUE NOT NULL  -- Ej: BRG-001
- contact_phone: VARCHAR(20)
- contact_email: VARCHAR(255)
- is_active: BOOLEAN DEFAULT true
- is_available: BOOLEAN DEFAULT true
- current_location: GEOGRAPHY(POINT, 4326)  -- PostGIS
- last_location_update: TIMESTAMP
- max_concurrent_incidents: INTEGER DEFAULT 5
- total_incidents_resolved: INTEGER DEFAULT 0
- avg_resolution_hours: FLOAT
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

**Campos geoespaciales**:
- `current_location`: Ubicación actual de la brigada (tracking en tiempo real)

**Relaciones**:
- `members`: Miembros de la brigada (many-to-many con users)
- `incidents`: Incidentes asignados a la brigada

### 3. **brigade_members** - Asociación brigadas-usuarios

```sql
- brigade_id: INTEGER FK(brigades.id) ON DELETE CASCADE
- user_id: INTEGER FK(users.id) ON DELETE CASCADE
- joined_at: TIMESTAMP DEFAULT NOW()
- PRIMARY KEY(brigade_id, user_id)
```

### 4. **reports** - Reportes ciudadanos

```sql
- id: SERIAL PRIMARY KEY
- user_id: INTEGER FK(users.id) NOT NULL
- location: GEOGRAPHY(POINT, 4326) NOT NULL  -- PostGIS
- address: VARCHAR(500)
- city: VARCHAR(100)
- province: VARCHAR(100)
- damage_type: ENUM('BACHE', 'GRIETA') NOT NULL
- severity: ENUM('BAJA', 'MEDIA', 'ALTA') NOT NULL
- confidence: FLOAT NOT NULL  -- 0.0 - 1.0 (confianza ML)
- image_url: VARCHAR(500) NOT NULL  -- URL en MinIO
- image_width: INTEGER
- image_height: INTEGER
- detections_json: TEXT  -- Bounding boxes JSON
- status: ENUM('PENDING', 'APPROVED', 'REJECTED', 'PROCESSING') DEFAULT 'PENDING'
- description: TEXT
- rejection_reason: TEXT
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
- reviewed_at: TIMESTAMP
```

**Campos geoespaciales**:
- `location`: Ubicación exacta del daño reportado

**Relaciones**:
- `user`: Usuario que reportó
- `incident`: Incidente generado (one-to-one)

### 5. **incidents** - Incidentes confirmados

```sql
- id: SERIAL PRIMARY KEY
- report_id: INTEGER FK(reports.id) UNIQUE NOT NULL
- reported_by: INTEGER FK(users.id) NOT NULL
- location: GEOGRAPHY(POINT, 4326) NOT NULL  -- PostGIS
- address: VARCHAR(500)
- city: VARCHAR(100)
- province: VARCHAR(100)
- damage_type: ENUM('BACHE', 'GRIETA') NOT NULL
- severity: ENUM('BAJA', 'MEDIA', 'ALTA') NOT NULL
- priority: ENUM('BAJA', 'MEDIA', 'ALTA', 'CRITICA') NOT NULL
- priority_score: FLOAT  -- Score calculado por algoritmo
- status: ENUM('OPEN', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'VERIFIED', 'CLOSED') DEFAULT 'OPEN'
- assigned_brigade_id: INTEGER FK(brigades.id)
- assigned_at: TIMESTAMP
- estimated_repair_hours: FLOAT
- started_at: TIMESTAMP
- completed_at: TIMESTAMP
- verified_at: TIMESTAMP
- is_verified: BOOLEAN DEFAULT false
- verified_by: INTEGER FK(users.id)
- verification_notes: TEXT
- before_image_url: VARCHAR(500)
- after_image_url: VARCHAR(500)
- notes: TEXT
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

**Campos geoespaciales**:
- `location`: Ubicación del incidente (heredada del reporte)

**Relaciones**:
- `original_report`: Reporte que generó el incidente
- `reported_by_user`: Usuario que reportó
- `assigned_brigade`: Brigada asignada
- `metrics`: Métricas asociadas

### 6. **pois** - Puntos de Interés

```sql
- id: SERIAL PRIMARY KEY
- name: VARCHAR(500) NOT NULL
- category: ENUM('SCHOOL', 'UNIVERSITY', 'HOSPITAL', 'CLINIC', 
                 'FIRE_STATION', 'POLICE_STATION', 'BRIDGE', 
                 'BUS_STATION', 'COMMERCIAL', 'OTHER') NOT NULL
- location: GEOGRAPHY(POINT, 4326) NOT NULL  -- PostGIS
- address: VARCHAR(500)
- city: VARCHAR(100)
- province: VARCHAR(100)
- source: VARCHAR(100)  -- 'google_places', 'osm', 'manual'
- external_id: VARCHAR(255)  -- ID externo
- priority_weight: INTEGER DEFAULT 1  -- 1-10
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

**Campos geoespaciales**:
- `location`: Ubicación del POI

**Uso**: Priorización de incidentes basada en proximidad a POIs críticos.

### 7. **metrics** - Métricas y estadísticas

```sql
- id: SERIAL PRIMARY KEY
- incident_id: INTEGER FK(incidents.id)
- metric_type: VARCHAR(100) NOT NULL  -- 'response_time', 'resolution_time', etc.
- value: FLOAT NOT NULL
- unit: VARCHAR(50)  -- 'hours', 'minutes', 'percent', 'dollars'
- category: VARCHAR(100)  -- 'performance', 'quality', 'cost'
- subcategory: VARCHAR(100)
- metadata_json: TEXT  -- Información adicional en JSON
- notes: TEXT
- recorded_at: TIMESTAMP DEFAULT NOW()
- created_at: TIMESTAMP DEFAULT NOW()
```

**Relaciones**:
- `incident`: Incidente relacionado (opcional)

## 🗺️ Campos Geoespaciales (PostGIS)

Todas las ubicaciones usan `Geography(POINT, 4326)`:

- **SRID 4326**: Sistema de coordenadas WGS84 (GPS estándar)
- **Geography**: Cálculos en superficie esférica (más preciso para distancias)
- **Spatial Index**: Índice automático para consultas geoespaciales rápidas

### Queries Geoespaciales Comunes

```python
from geoalchemy2.functions import ST_DWithin, ST_Distance
from sqlalchemy import func

# Encontrar incidentes dentro de 200m de un POI
incidents_near_poi = session.query(Incident).filter(
    ST_DWithin(
        Incident.location,
        poi.location,
        200  # metros
    )
).all()

# Calcular distancia entre dos puntos
distance = session.query(
    func.ST_Distance(incident.location, brigade.current_location)
).scalar()

# Ordenar por proximidad
incidents_sorted = session.query(Incident).order_by(
    func.ST_Distance(Incident.location, brigade.current_location)
).all()
```

## 🚀 Configuración de Base de Datos

### 1. Iniciar PostgreSQL con PostGIS (Docker)

```bash
# Iniciar contenedores
docker-compose -f backend/docker-compose.db.yml up -d

# Verificar que estén corriendo
docker ps

# Ver logs
docker logs sirccd-postgres
docker logs sirccd-redis
```

### 2. Verificar Conexión

```bash
# Conectar a PostgreSQL
docker exec -it sirccd-postgres psql -U sirccd_user -d sirccd_db

# Verificar PostGIS
SELECT PostGIS_version();

# Salir
\q
```

### 3. Aplicar Migraciones

```bash
cd backend

# Aplicar migración inicial
alembic upgrade head

# Verificar tablas creadas
docker exec -it sirccd-postgres psql -U sirccd_user -d sirccd_db -c "\dt"
```

### 4. Verificar Extensión PostGIS

```sql
-- En psql
SELECT postgis_full_version();

-- Verificar índices espaciales
SELECT tablename, indexname 
FROM pg_indexes 
WHERE indexdef LIKE '%USING gist%';
```

## 📝 Uso de Modelos en Código

### Crear Usuario

```python
from db import SessionLocal
from models import User, UserRole

db = SessionLocal()

user = User(
    email="juan@example.com",
    username="juan123",
    full_name="Juan Pérez",
    hashed_password=hash_password("secret"),
    role=UserRole.CIUDADANO
)

db.add(user)
db.commit()
db.refresh(user)
```

### Crear Reporte con Ubicación

```python
from geoalchemy2.elements import WKTElement

report = Report(
    user_id=user.id,
    location=WKTElement('POINT(-70.6623 19.4517)', srid=4326),  # Santiago, RD
    damage_type=DamageType.BACHE,
    severity=SeverityLevel.ALTA,
    confidence=0.92,
    image_url="s3://bucket/image.jpg",
    status=ReportStatus.PENDING
)

db.add(report)
db.commit()
```

### Query con Filtro Geoespacial

```python
from geoalchemy2.functions import ST_DWithin

# Encontrar reportes dentro de 500m de una ubicación
location_point = WKTElement('POINT(-70.6623 19.4517)', srid=4326)

nearby_reports = db.query(Report).filter(
    ST_DWithin(Report.location, location_point, 500)
).all()
```

## 🔧 Herramientas de Alembic

### Crear Nueva Migración

```bash
# Auto-generar migración basada en cambios de modelos
alembic revision --autogenerate -m "descripcion_del_cambio"

# Crear migración vacía (manual)
alembic revision -m "descripcion"
```

### Gestionar Migraciones

```bash
# Ver historial
alembic history

# Ver estado actual
alembic current

# Aplicar migración específica
alembic upgrade <revision>

# Revertir última migración
alembic downgrade -1

# Revertir todas
alembic downgrade base
```

### Ver SQL sin Aplicar

```bash
# Ver SQL que se ejecutaría
alembic upgrade head --sql
```

## 📚 Estructura de Archivos

```
backend/
├── db/
│   ├── __init__.py           # Exports (Base, engine, SessionLocal, get_db)
│   ├── base.py               # Base declarativa
│   └── session.py            # Configuración de sesión
│
├── models/
│   ├── __init__.py           # Imports de todos los modelos
│   ├── user.py               # Modelo User
│   ├── report.py             # Modelo Report
│   ├── incident.py           # Modelo Incident
│   ├── brigade.py            # Modelo Brigade
│   ├── poi.py                # Modelo POI
│   └── metric.py             # Modelo Metric
│
├── alembic/
│   ├── env.py                # Configuración de Alembic (modificado)
│   └── versions/
│       └── 001_initial_schema_with_postgis.py  # Migración inicial
│
├── alembic.ini               # Configuración Alembic (modificado)
├── docker-compose.db.yml     # PostgreSQL + Redis
└── docs/
    └── B-02_DATABASE_SCHEMA.md  # Esta documentación
```

## 🎯 Enumeraciones (Enums)

### UserRole
- `ADMIN`: Administrador del sistema
- `CIUDADANO`: Usuario ciudadano que reporta
- `BRIGADA`: Miembro de equipo de reparación
- `SUPERVISOR`: Supervisor de brigadas

### DamageType
- `BACHE`: Bache/hueco en el pavimento
- `GRIETA`: Grieta/fisura en el pavimento

### SeverityLevel
- `BAJA`: Daño menor
- `MEDIA`: Daño moderado
- `ALTA`: Daño severo

### ReportStatus
- `PENDING`: Pendiente de revisión
- `APPROVED`: Aprobado (se crea incidente)
- `REJECTED`: Rechazado (falso positivo, duplicado)
- `PROCESSING`: En proceso de análisis

### IncidentStatus
- `OPEN`: Abierto, sin asignar
- `ASSIGNED`: Asignado a brigada
- `IN_PROGRESS`: En reparación
- `RESOLVED`: Reparado
- `VERIFIED`: Verificado por supervisor
- `CLOSED`: Cerrado

### PriorityLevel
- `BAJA`: Prioridad baja
- `MEDIA`: Prioridad media
- `ALTA`: Prioridad alta
- `CRITICA`: Prioridad crítica

### POICategory
- `SCHOOL`: Escuela
- `UNIVERSITY`: Universidad
- `HOSPITAL`: Hospital
- `CLINIC`: Clínica
- `FIRE_STATION`: Estación de bomberos
- `POLICE_STATION`: Estación de policía
- `BRIDGE`: Puente
- `BUS_STATION`: Estación de autobuses
- `COMMERCIAL`: Zona comercial
- `OTHER`: Otro

## 🔐 Índices Creados

- **users**: email, username, id
- **brigades**: code, name, id, current_location (spatial)
- **reports**: user_id, status, created_at, location (spatial)
- **incidents**: report_id, reported_by, assigned_brigade_id, status, priority, severity, damage_type, created_at, location (spatial)
- **pois**: category, id, location (spatial)
- **metrics**: incident_id, metric_type, category, recorded_at

## 🚧 Próximos Pasos

- [x] Esquema de base de datos definido
- [x] Modelos SQLAlchemy creados
- [x] Migraciones con Alembic configuradas
- [x] PostGIS habilitado
- [x] Docker Compose para desarrollo
- [ ] Schemas Pydantic para validación (B-03)
- [ ] Endpoints CRUD para cada modelo (B-04)
- [ ] Tests de modelos y queries

## ✅ Verificación

```bash
# 1. Iniciar base de datos
docker-compose -f backend/docker-compose.db.yml up -d

# 2. Aplicar migraciones
cd backend
alembic upgrade head

# 3. Verificar tablas
docker exec -it sirccd-postgres psql -U sirccd_user -d sirccd_db -c "\dt"

# Deberías ver:
#  Schema |      Name       | Type  |    Owner     
# --------+-----------------+-------+--------------
#  public | alembic_version | table | sirccd_user
#  public | brigade_members | table | sirccd_user
#  public | brigades        | table | sirccd_user
#  public | incidents       | table | sirccd_user
#  public | metrics         | table | sirccd_user
#  public | pois            | table | sirccd_user
#  public | reports         | table | sirccd_user
#  public | users           | table | sirccd_user
#  public | spatial_ref_sys | table | sirccd_user
```

## 📊 Diagrama ER (Simplificado)

```
users (1) ----> (N) reports
users (1) ----> (N) incidents
users (N) <----> (N) brigades (via brigade_members)

reports (1) ----> (1) incidents

incidents (N) ----> (1) brigades
incidents (1) ----> (N) metrics

pois (standalone, usado para priorización)
```

## 🏆 Estado

**✅ B-02 COMPLETADO**

- 7 tablas creadas
- 3 tipos geoespaciales (Geography POINT)
- 7 enumeraciones
- Múltiples índices (incluyendo espaciales)
- Migración inicial funcional
- Docker Compose configurado
