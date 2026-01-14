# Backend - Modelos de Datos

## 📖 Descripción

Esta carpeta contiene la definición del modelo de datos (schemas, modelos ORM) del backend de SIRCCD.

---

## 📁 Estructura

```
backend/models/
├── README.md                    # Este archivo
├── __init__.py                  # Exportaciones de modelos
├── base.py                      # Clase base SQLAlchemy
├── user.py                      # Modelo USER_ACCOUNT
├── municipality.py              # Modelo MUNICIPALITY
├── brigade.py                   # Modelos BRIGADE, BRIGADE_MEMBER
├── report.py                    # Modelos REPORT, REPORT_IMAGE
├── deduplication.py             # Modelo REPORT_DEDUP
├── incident.py                  # Modelo INCIDENT
├── work_order.py                # Modelos WORK_ORDER, WORK_ORDER_IMAGE
├── metrics.py                   # Modelos METRIC_EVENT, DAILY_METRICS
├── enums.py                     # Enums compartidos
└── migrations/                  # Migraciones Alembic
    ├── versions/
    │   ├── 001_initial_schema.py
    │   └── 002_add_deduplication.py
    └── alembic.ini
```

---

## 🗺️ Modelo Completo

**Documentación exhaustiva:**  
👉 [docs/arquitectura/modelo_datos.md](../../docs/arquitectura/modelo_datos.md)

Incluye:
- Diagrama ERD completo en Mermaid
- Descripción de cada tabla
- Índices espaciales (PostGIS)
- Constraints de integridad
- Consultas SQL de ejemplo
- Vistas materializadas

---

## 🔧 Tecnologías

- **PostgreSQL 15+** - Base de datos relacional
- **PostGIS 3.x** - Extensión espacial (GEOGRAPHY, POINT)
- **SQLAlchemy 2.x** - ORM de Python
- **Alembic** - Migraciones de schema
- **GeoAlchemy2** - Soporte PostGIS en SQLAlchemy

---

## 🚀 Uso

### Configurar Conexión

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DATABASE_URL = "postgresql://user:pass@localhost:5432/sirccd"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Crear todas las tablas
Base.metadata.create_all(engine)
```

---

### Crear Reporte con Geolocalización

```python
from models.report import Report
from geoalchemy2.elements import WKTElement

session = SessionLocal()

nuevo_reporte = Report(
    reporter_user_id=user_id,
    description="Bache grande en calle principal",
    category="bache",
    location=WKTElement(f'POINT({longitud} {latitud})', srid=4326),
    address_text="Calle Principal, Col. Escalón",
    status="pendiente"
)

session.add(nuevo_reporte)
session.commit()
```

---

### Buscar Reportes Cercanos (500m)

```python
from sqlalchemy import func
from models.report import Report

punto_busqueda = f'POINT(-89.218191 13.692940)'

reportes_cercanos = session.query(
    Report,
    func.ST_Distance(
        Report.location,
        func.ST_GeographyFromText(punto_busqueda)
    ).label('distancia_m')
).filter(
    func.ST_DWithin(
        Report.location,
        func.ST_GeographyFromText(punto_busqueda),
        500  # metros
    )
).order_by('distancia_m').all()
```

---

### Asignar Incidente a Brigada

```python
from models.work_order import WorkOrder
from datetime import datetime

orden = WorkOrder(
    incident_id=incident_id,
    brigade_id=brigade_id,
    assigned_by_user_id=admin_id,
    status='asignada',
    assigned_at=datetime.utcnow()
)

session.add(orden)
session.commit()
```

---

## 📊 Enums

### UserRole
```python
class UserRole(str, Enum):
    CIUDADANO = "ciudadano"
    BRIGADA = "brigada"
    ADMINISTRADOR = "administrador"
    SUPERVISOR = "supervisor"
```

### ReportStatus
```python
class ReportStatus(str, Enum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    VALIDADO = "validado"
    RECHAZADO = "rechazado"
    DUPLICADO = "duplicado"
```

### IncidentStatus
```python
class IncidentStatus(str, Enum):
    PENDIENTE = "pendiente"
    ASIGNADO = "asignado"
    EN_PROCESO = "en_proceso"
    RESUELTO = "resuelto"
    CERRADO = "cerrado"
```

### DamageCategory
```python
class DamageCategory(str, Enum):
    BACHE = "bache"
    GRIETA = "grieta"
    HUNDIMIENTO = "hundimiento"
```

---

## 🗄️ Migraciones

### Crear Nueva Migración

```bash
cd backend
alembic revision -m "agregar campo prioridad a incident"
```

### Aplicar Migraciones

```bash
# Aplicar todas pendientes
alembic upgrade head

# Aplicar hasta versión específica
alembic upgrade abc123

# Revertir última migración
alembic downgrade -1
```

### Ver Historial

```bash
alembic history
alembic current
```

---

## 🌍 PostGIS - Tipos Espaciales

### GEOGRAPHY vs GEOMETRY

**Usar `GEOGRAPHY`:**
- Coordenadas GPS (lat/lng)
- Cálculos de distancia en metros
- Proyección esférica (tierra redonda)

**Sintaxis:**
```python
from geoalchemy2 import Geography
from sqlalchemy import Column

location = Column(Geography('POINT', srid=4326))
```

### Funciones Espaciales Comunes

| Función | Descripción | Ejemplo |
|---------|-------------|---------|
| `ST_Distance` | Distancia en metros | `ST_Distance(a, b)` |
| `ST_DWithin` | Dentro de radio | `ST_DWithin(a, b, 500)` |
| `ST_MakePoint` | Crear punto | `ST_MakePoint(lng, lat)` |
| `ST_GeographyFromText` | Parse WKT | `ST_GeographyFromText('POINT(...)')` |
| `ST_AsGeoJSON` | Exportar GeoJSON | `ST_AsGeoJSON(location)` |

---

## 🔍 Validaciones y Constraints

### A Nivel de Modelo (SQLAlchemy)

```python
from sqlalchemy.orm import validates

class Report(Base):
    # ...
    
    @validates('category')
    def validate_category(self, key, value):
        if value not in ['bache', 'grieta', 'hundimiento']:
            raise ValueError("Categoría inválida")
        return value
    
    @validates('severity_pred')
    def validate_severity(self, key, value):
        if value is not None and not (0 <= value <= 1):
            raise ValueError("Severidad debe estar entre 0 y 1")
        return value
```

### A Nivel de Base de Datos

```sql
-- Ver backend/models/migrations/versions/001_initial_schema.py
ALTER TABLE report ADD CONSTRAINT chk_severity_range 
CHECK (severity_pred IS NULL OR (severity_pred >= 0 AND severity_pred <= 1));

ALTER TABLE report ADD CONSTRAINT chk_duplicate_status 
CHECK (
  (status = 'duplicado' AND duplicate_of_report_id IS NOT NULL) OR
  (status != 'duplicado' AND duplicate_of_report_id IS NULL)
);
```

---

## 🧪 Testing

### Fixtures de Prueba

```python
import pytest
from sqlalchemy import create_engine
from models import Base

@pytest.fixture
def db_session():
    engine = create_engine("postgresql://test:test@localhost/sirccd_test")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.rollback()
    Base.metadata.drop_all(engine)
```

### Test de Deduplicación

```python
def test_reporte_duplicado(db_session):
    reporte_original = Report(
        reporter_user_id=user_id,
        description="Bache",
        location=WKTElement('POINT(-89.218 13.692)', srid=4326),
        status="validado"
    )
    db_session.add(reporte_original)
    db_session.commit()
    
    reporte_duplicado = Report(
        reporter_user_id=user_id,
        description="Mismo bache",
        location=WKTElement('POINT(-89.218 13.692)', srid=4326),
        status="duplicado",
        duplicate_of_report_id=reporte_original.id
    )
    db_session.add(reporte_duplicado)
    db_session.commit()
    
    assert reporte_duplicado.duplicate_of_report_id == reporte_original.id
```

---

## 📚 Referencias

- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **GeoAlchemy2 Docs:** https://geoalchemy-2.readthedocs.io/
- **PostGIS Manual:** https://postgis.net/documentation/
- **Alembic Tutorial:** https://alembic.sqlalchemy.org/en/latest/tutorial.html

---

## 🤝 Contribución

Al agregar nuevos modelos:

1. Crear archivo `.py` en `backend/models/`
2. Definir clase heredando de `Base`
3. Agregar a `__init__.py`
4. Crear migración con Alembic
5. Actualizar documentación en `docs/arquitectura/modelo_datos.md`
6. Agregar tests

**Convención de commits:**
```
feat: agregar modelo de notificaciones
fix: corregir constraint en work_order
refactor: optimizar índices espaciales
```

---

## 📄 Licencia

MIT License
