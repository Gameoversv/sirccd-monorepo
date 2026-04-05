# Modulo Backend

## 1. Proposito del modulo

El backend es el nucleo del sistema SIRCCD. Es responsable de:

1. **Autenticacion y autorizacion**: login, registro, JWT, refresh tokens y control de acceso por roles (citizen, operator, admin).
2. **Gestion de reportes**: recepcion, validacion, almacenamiento y ciclo de vida de reportes ciudadanos.
3. **Gestion de incidentes**: consolidacion de reportes en incidentes operativos, actualizacion de estados y seguimiento.
4. **Deduplicacion inteligente**: deteccion multimodal de reportes duplicados usando embeddings visuales, proximidad geografica y similitud textual.
5. **Priorizacion automatica**: calculo de prioridad de incidentes basado en severidad, frecuencia, ubicacion y contexto urbano (POIs).
6. **Inferencia ML**: clasificacion automatica de tipo de dano y severidad mediante modelos YOLO.
7. **Anonimizacion**: difuminado automatico de rostros y placas en imagenes.
8. **Exportacion de datos**: generacion de datasets en CSV y GeoJSON.
9. **Observabilidad**: health checks, metricas Prometheus y monitoreo de servicios.

## 2. Stack tecnologico

| Componente | Tecnologia | Version | Proposito |
|-----------|------------|---------|-----------|
| Framework web | FastAPI | 0.115.0 | API REST asincrona con documentacion automatica |
| ORM | SQLAlchemy | 2.0+ | Mapeo objeto-relacional con soporte async |
| Migraciones | Alembic | - | Evolucion de esquema de base de datos |
| Base de datos | PostgreSQL + PostGIS | 16+ | Persistencia relacional + queries geoespaciales |
| Cola de tareas | Redis + RQ | Redis 7, RQ 5 | Procesamiento asincrono de tareas pesadas |
| Almacenamiento | MinIO | 7.2+ | Object storage compatible con S3 para imagenes |
| ML Inference | PyTorch + torchvision | 2.1+ | Ejecucion de modelos de clasificacion |
| Busqueda vectorial | FAISS | 1.7.4+ | Indexacion y busqueda de embeddings por similitud |
| Embeddings | ResNet50 / CLIP | - | Extraccion de vectores visuales para deduplicacion |
| Auth | python-jose + passlib | - | JWT tokens y hashing de passwords |
| Validacion | Pydantic | 2.0+ | Contratos tipados de request/response |
| Testing | pytest + httpx | - | Suite de pruebas automatizadas |

## 3. Arquitectura en capas

```
┌──────────────────────────────────────────────────────────────┐
│                        API Layer                              │
│  FastAPI routes + OpenAPI spec + dependency injection          │
│  Responsabilidad: HTTP, validacion, serializacion, auth       │
├──────────────────────────────────────────────────────────────┤
│                      Service Layer                            │
│  Logica de negocio, ML, deduplicacion, prioridad, export      │
│  Responsabilidad: reglas de dominio, calculos, orquestacion   │
├──────────────────────────────────────────────────────────────┤
│                    Models / DB Layer                           │
│  SQLAlchemy ORM + Alembic migrations + session management     │
│  Responsabilidad: persistencia, esquema, queries              │
├──────────────────────────────────────────────────────────────┤
│                      Tasks Layer                              │
│  Redis RQ workers para procesamiento asincrono                │
│  Responsabilidad: inferencia ML, embeddings, deduplicacion    │
└──────────────────────────────────────────────────────────────┘
```

### 3.1 Principios de diseno

- **Separacion de responsabilidades**: cada capa tiene un rol claro y no conoce detalles de implementacion de las otras.
- **Dependency injection**: FastAPI `Depends()` para inyectar sesiones de BD, usuario autenticado y verificacion de roles.
- **Procesamiento asincrono**: tareas pesadas (ML, embeddings) se ejecutan en workers RQ fuera del ciclo request-response.
- **Contratos tipados**: Pydantic schemas definen la forma exacta de entrada y salida de cada endpoint.

## 4. Mapa de archivos y directorios

### 4.1 API (`api/`)

| Archivo | Descripcion |
|---------|-------------|
| `api/deps.py` | Dependencias compartidas de FastAPI: `get_db` (sesion), `get_current_user` (auth JWT), `require_role` (autorizacion por rol) |
| `api/openapi.yaml` | Especificacion OpenAPI/Swagger del modulo |
| `api/routes/auth.py` | Endpoints de autenticacion: login, refresh token, registro, perfil actual |
| `api/routes/reports.py` | CRUD de reportes: crear (multipart con imagen), listar con filtros, detalle, actualizar estado, eliminar |
| `api/routes/incidents.py` | Gestion de incidentes: listar, detalle con reportes asociados, actualizar estado/prioridad, merge de reportes |
| `api/routes/deduplication.py` | Operaciones de deduplicacion: verificar duplicado, buscar similares, estadisticas, rebuild/save de indice FAISS |
| `api/routes/export.py` | Exportacion de datos: descarga CSV y GeoJSON con filtros |
| `api/routes/health.py` | Health checks: estado general, BD, Redis, MinIO |
| `api/routes/pois.py` | Puntos de interes: consulta de POIs cercanos a coordenada |
| `api/routes/users.py` | Administracion de usuarios: listar, detalle, actualizar, desactivar |

### 4.2 Core (`core/`)

| Archivo | Descripcion |
|---------|-------------|
| `core/config.py` | Clase `Settings` con todas las variables de entorno del sistema. Usa Pydantic `BaseSettings` para validacion y defaults |
| `core/security.py` | Utilidades de seguridad: generacion/verificacion de JWT, hashing de passwords con bcrypt, extraccion de claims |
| `core/database.py` | Inicializacion de la conexion a BD: engine, session factory, funcion de init con creacion de tablas |
| `core/metrics.py` | Definicion de metricas Prometheus: contadores de requests, histogramas de latencia, gauges de estado |

### 4.3 Base de datos (`db/`)

| Archivo | Descripcion |
|---------|-------------|
| `db/base.py` | Base declarativa de SQLAlchemy (`DeclarativeBase`) usada por todos los modelos |
| `db/session.py` | `SessionLocal` factory y funcion generadora `get_session()` para dependency injection |

### 4.4 Modelos ORM (`models/`)

| Archivo | Entidad | Campos principales |
|---------|---------|-------------------|
| `models/user.py` | User | id (UUID), email, hashed_password, full_name, role (citizen/operator/admin), is_active, created_at, updated_at |
| `models/report.py` | Report | id (UUID), user_id (FK), incident_id (FK nullable), image_url, description, lat/lng, status, damage_type, severity, embedding (binary), created_at, updated_at |
| `models/incident.py` | Incident | id (UUID), title, description, lat/lng, status, priority, damage_type, report_count, created_at, updated_at, resolved_at |
| `models/poi.py` | POI | id (UUID), name, category (school/hospital/government/etc.), lat/lng, source |
| `models/metric.py` | Metric | Metricas persistidas del sistema |

### 4.5 Diagrama entidad-relacion

```
┌──────────┐       ┌──────────────┐       ┌─────────────┐
│   User   │1     *│    Report    │*     1│  Incident   │
│──────────│───────│──────────────│───────│─────────────│
│ id (PK)  │       │ id (PK)      │       │ id (PK)     │
│ email    │       │ user_id (FK) │       │ title       │
│ password │       │ incident_id  │       │ description │
│ name     │       │ image_url    │       │ lat/lng     │
│ role     │       │ description  │       │ status      │
│ is_active│       │ lat/lng      │       │ priority    │
└──────────┘       │ status       │       │ damage_type │
                   │ damage_type  │       │ report_count│
                   │ severity     │       └─────────────┘
                   │ embedding    │
                   └──────────────┘
                          |
                     (proximidad)
                          |
                   ┌──────────────┐
                   │     POI      │
                   │──────────────│
                   │ id, name     │
                   │ category     │
                   │ lat/lng      │
                   └──────────────┘
```

**Relaciones**:
- **User → Report**: 1:N. Un usuario puede crear muchos reportes.
- **Incident → Report**: 1:N. Un incidente agrupa multiples reportes (deduplicacion).
- **Report ↔ POI**: relacion implicita por proximidad geografica (usada en priorizacion).

### 4.6 Schemas Pydantic (`schemas/`)

| Archivo | Schemas principales |
|---------|-------------------|
| `schemas/auth.py` | `LoginRequest`, `TokenResponse`, `RegisterRequest`, `UserProfile` |
| `schemas/report.py` | `ReportCreate`, `ReportResponse`, `ReportUpdate`, `ReportListResponse` (paginado) |
| `schemas/incident.py` | `IncidentResponse`, `IncidentUpdate`, `IncidentListResponse`, `IncidentMerge` |
| `schemas/deduplication.py` | `DedupCheckRequest`, `DedupCheckResponse`, `SimilarReportsResponse`, `DedupStats` |
| `schemas/export.py` | `ExportRequest`, `ExportParams` |
| `schemas/poi.py` | `POIResponse`, `POIListResponse` |
| `schemas/user.py` | `UserResponse`, `UserUpdate`, `UserListResponse` |

### 4.7 Servicios de negocio (`services/`)

| Archivo | Servicio | Descripcion detallada |
|---------|----------|----------------------|
| `services/ml_service.py` | ML Service | Carga modelos YOLO pre-entrenados, ejecuta inferencia sobre imagenes de reportes. Retorna tipo de dano (pothole, crack, subsidence, etc.) y score de severidad (0-1). Maneja cache de modelos en memoria |
| `services/anonymizer.py` | Anonymizer | Detecta y difumina rostros y placas vehiculares en imagenes de reportes. Usa modelo de deteccion dedicado |
| `services/deduplication_service.py` | Dedup Service | Pipeline completo de deduplicacion multimodal. Extrae embeddings (ResNet50/CLIP), consulta FAISS, calcula scores geo y texto, fusiona con pesos configurables. Gestiona indice FAISS (build, save, load) |
| `services/priority_service.py` | Priority Service | Calcula prioridad de incidentes con formula ponderada: severidad ML, numero de reportes, proximidad a POIs criticos, antiguedad del primer reporte |
| `services/export_service.py` | Export Service | Genera datasets exportables en CSV y GeoJSON con filtros por fecha, estado, tipo, area geografica |
| `services/health_service.py` | Health Service | Verifica conectividad y estado de BD, Redis y MinIO. Retorna status global del sistema |
| `services/queue_service.py` | Queue Service | Encola tareas en Redis RQ, monitorea estado de jobs, maneja reintentos |
| `services/storage.py` | Storage Service | Abstraccion sobre MinIO SDK: upload/download de archivos, generacion de URLs presignadas, gestion de buckets |

### 4.8 Tareas asincronas (`tasks/`)

| Archivo | Descripcion |
|---------|-------------|
| `tasks/ml_tasks.py` | Tarea principal del worker: recibe reporte, ejecuta clasificacion ML, extrae embeddings, ejecuta deduplicacion, calcula prioridad. Todo en un solo job |
| `tasks/worker.py` | Entry point del worker RQ para Linux/Mac |
| `tasks/worker_windows.py` | Entry point del worker RQ para Windows (RQ tiene limitaciones con fork() en Windows) |

### 4.9 Scripts operativos (`scripts/`)

| Archivo | Descripcion |
|---------|-------------|
| `scripts/evaluate_dedup_embeddings.py` | Evaluacion comparativa de diferentes modelos de embeddings para deduplicacion (precision, recall, F1) |
| `scripts/verification/verify_b02.py` | Verificacion de migraciones y esquema de BD (batch B02) |
| `scripts/verification/verify_b03.py` | Verificacion de auth y seguridad (batch B03) |
| `scripts/verification/verify_migration.py` | Verificacion general de migraciones Alembic |
| `scripts/maintenance/create_incidents_from_reports.py` | Script de mantenimiento: crea incidentes a partir de reportes huerfanos |

### 4.10 Pruebas (`tests/`)

| Archivo | Cobertura |
|---------|-----------|
| `tests/test_auth.py` | Autenticacion: login valido/invalido, JWT generation, refresh token, proteccion de rutas, roles |
| `tests/test_reports.py` | Reportes: creacion, listado con filtros, detalle, actualizacion de estado, validaciones |
| `tests/test_incidents.py` | Incidentes: listado, detalle con reportes asociados, actualizacion, merge |
| `tests/test_contract.py` | Contratos API: validacion de schemas request/response contra spec |
| `tests/test_health.py` | Health checks: respuesta correcta, deteccion de servicios caidos |
| `tests/manual/` | Pruebas manuales y smoke tests (ej: deduplicacion end-to-end) |
| `tests/manual/fixtures/` | Imagenes y recursos para pruebas manuales |

## 5. Endpoints de la API

### 5.1 Autenticacion (`/api/auth`)

| Metodo | Ruta | Auth | Descripcion |
|--------|------|------|-------------|
| POST | `/api/auth/login` | No | Login con email/password, retorna access_token + refresh_token |
| POST | `/api/auth/refresh` | refresh_token | Renueva access_token usando refresh_token |
| POST | `/api/auth/register` | No | Registro de nuevo usuario ciudadano |
| GET | `/api/auth/me` | JWT | Retorna perfil del usuario autenticado |

### 5.2 Reportes (`/api/reports`)

| Metodo | Ruta | Auth | Rol minimo | Descripcion |
|--------|------|------|-----------|-------------|
| GET | `/api/reports` | JWT | operator | Lista reportes con filtros (status, damage_type, severity, fecha, area) y paginacion |
| POST | `/api/reports` | JWT | citizen | Crea reporte con imagen (multipart/form-data), ubicacion y descripcion |
| GET | `/api/reports/{id}` | JWT | citizen | Detalle de un reporte (ciudadano ve solo los suyos, operador ve todos) |
| PATCH | `/api/reports/{id}` | JWT | operator | Actualiza estado o metadata del reporte |
| DELETE | `/api/reports/{id}` | JWT | admin | Elimina reporte |

### 5.3 Incidentes (`/api/incidents`)

| Metodo | Ruta | Auth | Rol minimo | Descripcion |
|--------|------|------|-----------|-------------|
| GET | `/api/incidents` | JWT | operator | Lista incidentes con filtros (status, priority, damage_type, area) |
| GET | `/api/incidents/{id}` | JWT | operator | Detalle de incidente con lista de reportes asociados |
| PATCH | `/api/incidents/{id}` | JWT | operator | Actualiza estado, prioridad o asignacion |
| POST | `/api/incidents/{id}/merge` | JWT | operator | Fusiona reportes en un incidente existente |

### 5.4 Deduplicacion (`/api/deduplication`)

| Metodo | Ruta | Auth | Descripcion |
|--------|------|------|-------------|
| POST | `/api/deduplication/check` | JWT | Verifica si un reporte es duplicado de alguno existente |
| POST | `/api/deduplication/similar` | JWT | Busca reportes similares a uno dado (top-K) |
| GET | `/api/deduplication/stats` | JWT | Estadisticas del indice: total vectores, dimension, ultimo rebuild |
| POST | `/api/deduplication/index/rebuild` | JWT (admin) | Reconstruye indice FAISS desde cero con todos los embeddings |
| POST | `/api/deduplication/index/save` | JWT (admin) | Persiste indice FAISS actual a disco |

### 5.5 Exportacion (`/api/export`)

| Metodo | Ruta | Auth | Descripcion |
|--------|------|------|-------------|
| GET | `/api/export/csv` | JWT (operator) | Exporta reportes/incidentes filtrados en formato CSV |
| GET | `/api/export/geojson` | JWT (operator) | Exporta reportes/incidentes filtrados en formato GeoJSON |

### 5.6 Health (`/api/health`)

| Metodo | Ruta | Auth | Descripcion |
|--------|------|------|-------------|
| GET | `/api/health` | No | Estado general del sistema (healthy/degraded/unhealthy) |
| GET | `/api/health/db` | No | Conectividad con PostgreSQL |
| GET | `/api/health/redis` | No | Conectividad con Redis |
| GET | `/api/health/minio` | No | Conectividad con MinIO |

### 5.7 Usuarios (`/api/users`)

| Metodo | Ruta | Auth | Rol minimo | Descripcion |
|--------|------|------|-----------|-------------|
| GET | `/api/users` | JWT | admin | Lista todos los usuarios con filtros |
| GET | `/api/users/{id}` | JWT | admin | Detalle de un usuario |
| PATCH | `/api/users/{id}` | JWT | admin | Actualiza rol, nombre o estado de un usuario |
| DELETE | `/api/users/{id}` | JWT | admin | Desactiva usuario (soft delete) |

### 5.8 POIs (`/api/pois`)

| Metodo | Ruta | Auth | Descripcion |
|--------|------|------|-------------|
| GET | `/api/pois` | JWT | Lista POIs cercanos a una coordenada (lat, lng, radio) |

## 6. Pipeline de deduplicacion (detalle)

### 6.1 Arquitectura multimodal

La deduplicacion combina tres senales independientes para determinar si dos reportes refieren al mismo dano:

```
                    Imagen del reporte
                           |
                    ┌──────v──────┐
                    │  Extractor  │
                    │  Embeddings │
                    │(ResNet/CLIP)│
                    └──────┬──────┘
                           |
                    ┌──────v──────┐
                    │ Indice FAISS│──→ Top-K candidatos
                    └──────┬──────┘
                           |
              ┌────────────┼────────────┐
              v            v            v
        Score Visual  Score Geo   Score Texto
        (coseno)      (Haversine) (TF-IDF)
              |            |            |
              └────────────┼────────────┘
                           v
                    Score Fusionado
                    (pesos: 0.5/0.35/0.15)
                           |
                    ┌──────v──────┐
                    │  Umbral     │
                    │  >= 0.85    │
                    └──────┬──────┘
                     |           |
                 Duplicado   No duplicado
```

### 6.2 Componentes

1. **Embeddings visuales**: ResNet50 (2048-dim) o CLIP (512-dim). Se extraen en el worker y se almacenan como binary en el campo `embedding` del reporte.
2. **Indice FAISS**: IndexFlatIP (inner product) para busqueda exacta de vecinos. Se persiste en disco como archivo binario.
3. **Score geografico**: distancia Haversine entre coordenadas GPS, normalizada a 0-1 dentro de un radio configurable.
4. **Score textual**: similitud TF-IDF entre descripciones (cuando disponibles).
5. **Fusion**: promedio ponderado con pesos configurables (default: visual=0.5, geo=0.35, texto=0.15).

### 6.3 Parametros configurables

```env
FAISS_INDEX_PATH=data/faiss_index.bin
DEDUP_SIMILARITY_THRESHOLD=0.85
DEDUP_VISUAL_WEIGHT=0.5
DEDUP_GEO_WEIGHT=0.35
DEDUP_TEXT_WEIGHT=0.15
DEDUP_GEO_RADIUS_METERS=100
DEDUP_TOP_K=10
```

## 7. Sistema de autorizacion

### 7.1 Roles

| Rol | Descripcion | Permisos |
|-----|-------------|----------|
| `citizen` | Ciudadano que reporta danos | Crear reportes, ver reportes propios |
| `operator` | Operador municipal | Todo de citizen + ver todos los reportes, gestionar incidentes, exportar datos |
| `admin` | Administrador del sistema | Todo de operator + gestionar usuarios, rebuild indice FAISS, eliminar reportes |

### 7.2 Flujo de autenticacion

```
1. POST /api/auth/login {email, password}
2. Backend verifica credenciales (bcrypt hash)
3. Genera access_token (JWT, 30min) + refresh_token (JWT, 7 dias)
4. Cliente almacena tokens
5. Cada request incluye: Authorization: Bearer <access_token>
6. deps.py extrae y valida JWT, inyecta current_user
7. require_role() verifica que el rol del usuario sea suficiente
8. Antes de expiracion: POST /api/auth/refresh con refresh_token
```

## 8. Configuracion (variables de entorno)

```env
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/sirccd
DATABASE_URL_SYNC=postgresql://user:pass@localhost:5432/sirccd

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sirccd-reports
MINIO_SECURE=false

# Auth
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# ML
ML_MODEL_PATH=models/best.pt
ML_CONFIDENCE_THRESHOLD=0.5

# FAISS / Deduplicacion
FAISS_INDEX_PATH=data/faiss_index.bin
DEDUP_SIMILARITY_THRESHOLD=0.85
```

Archivo de referencia: `.env.example`

## 9. Ejecucion local

### 9.1 Servidor API

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

### 9.2 Worker de procesamiento

```powershell
# Linux/Mac
cd backend
python -m tasks.worker

# Windows
cd backend
..\.venv\Scripts\Activate.ps1
python tasks/worker_windows.py
```

### 9.3 Migraciones de BD

```powershell
cd backend
alembic upgrade head          # Aplicar todas las migraciones
alembic revision --autogenerate -m "descripcion"  # Nueva migracion
alembic downgrade -1          # Revertir ultima migracion
```

## 10. Pruebas

### 10.1 Suite automatica

```powershell
cd backend
pytest                                    # Ejecutar todos los tests
pytest -v                                 # Verbose
pytest --cov=. --cov-report=html          # Con cobertura
pytest tests/test_auth.py                 # Solo auth
pytest tests/test_reports.py -k "test_create"  # Test especifico
```

### 10.2 Pruebas manuales

```powershell
cd backend
pytest tests/manual/test_b07_deduplication.py -q
```

### 10.3 Windows: FAISS/PyTorch

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
pytest tests/manual/test_b07_deduplication.py -q
$env:KMP_DUPLICATE_LIB_OK=$null
```

## 11. Integraciones

| Servicio externo | Mecanismo | Uso |
|-----------------|-----------|-----|
| Frontend | REST API + JWT | Consume todos los endpoints para dashboard operativo |
| Mobile (futuro) | REST API + JWT | Envio de reportes ciudadanos |
| PostgreSQL + PostGIS | SQLAlchemy ORM | Persistencia de entidades + queries geoespaciales |
| Redis + RQ | Cola de tareas | Workers procesan reportes de forma asincrona |
| MinIO | SDK MinIO (S3-compatible) | Almacenamiento de imagenes de reportes |
| ML (artefactos) | Archivos de pesos/config | Modelos entrenados para inferencia |

## 12. Puertos por defecto

| Servicio | Puerto |
|----------|--------|
| FastAPI (backend) | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| MinIO API | 9000 |
| MinIO Console | 9001 |
