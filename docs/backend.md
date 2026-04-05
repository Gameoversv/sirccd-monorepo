# Modulo Backend

## 1) Proposito del modulo

El backend es el nucleo del sistema SIRCCD. Se encarga de:

1. autenticar usuarios y aplicar permisos por rol,
2. recibir y procesar reportes ciudadanos,
3. gestionar incidentes operativos,
4. ejecutar deduplicacion inteligente,
5. calcular prioridad de atencion,
6. exponer exportaciones y estado de salud del sistema.

## 2) Como se implemento

La implementacion se organizo por capas para separar responsabilidades:

- Capa API (FastAPI): rutas HTTP y validacion de entrada/salida.
- Capa de negocio (services): reglas, calculos y procesos del dominio.
- Capa de datos (models/db): entidades, persistencia y acceso a BD.
- Capa asincrona (tasks + Redis/RQ): procesamiento de trabajos pesados.

Decisiones tecnicas principales:

1. ORM con SQLAlchemy y migraciones con Alembic.
2. datos geoespaciales con PostgreSQL + PostGIS.
3. cola asincrona con Redis + RQ para tareas de inferencia.
4. deduplicacion multimodelo (ResNet/CLIP) con FAISS y score fusionado.
5. contratos API tipados con Pydantic en `schemas/`.

## 3) Donde esta cada cosa (mapa de carpetas y archivos)

### 3.1 API

- `api/deps.py`: dependencias FastAPI (auth, DB, roles).
- `api/openapi.yaml`: especificacion OpenAPI del modulo.
- `api/routes/auth.py`: login, refresh, usuario actual y operaciones auth.
- `api/routes/reports.py`: CRUD/flujo de reportes.
- `api/routes/incidents.py`: gestion de incidentes.
- `api/routes/deduplication.py`: chequeo/similitud/rebuild/stats de dedup.
- `api/routes/export.py`: exportaciones CSV/GeoJSON.
- `api/routes/health.py`: health checks y disponibilidad.
- `api/routes/pois.py`: puntos de interes.
- `api/routes/users.py`: gestion de usuarios.

### 3.2 Core

- `core/config.py`: settings y variables de entorno.
- `core/security.py`: hashing, JWT y utilidades de seguridad.
- `core/database.py`: inicializacion/conexion de DB.
- `core/metrics.py`: metricas de observabilidad.

### 3.3 Datos y modelos

- `db/base.py`: base declarativa.
- `db/session.py`: SessionLocal y ciclo de sesion.
- `models/user.py`: entidad de usuarios.
- `models/report.py`: entidad de reportes.
- `models/incident.py`: entidad de incidentes.
- `models/poi.py`: puntos de interes.
- `models/metric.py`: metricas persistidas.

### 3.4 Schemas

- `schemas/auth.py`: contratos de autenticacion.
- `schemas/report.py`: contratos de reportes.
- `schemas/incident.py`: contratos de incidentes.
- `schemas/deduplication.py`: contratos de deduplicacion.
- `schemas/export.py`: contratos de exportaciones.
- `schemas/poi.py`: contratos de POI.
- `schemas/user.py`: contratos de usuario.

### 3.5 Servicios de negocio

- `services/ml_service.py`: inferencia/capa ML backend.
- `services/anonymizer.py`: anonimizado de imagenes.
- `services/deduplication_service.py`: embeddings + FAISS + fusion.
- `services/priority_service.py`: scoring de prioridad.
- `services/export_service.py`: exportacion de datasets operativos.
- `services/health_service.py`: verificaciones de salud.
- `services/queue_service.py`: cola de trabajos.
- `services/storage.py`: abstraccion de almacenamiento.

### 3.6 Tareas asincronas

- `tasks/ml_tasks.py`: tareas worker para procesamiento de reportes.
- `worker.py` y `worker_windows.py`: entrada de workers.

### 3.7 Scripts operativos

- `scripts/evaluate_dedup_embeddings.py`: evaluacion comparativa de embeddings.
- `scripts/verification/verify_b02.py`: verificacion de migracion/esquema.
- `scripts/verification/verify_b03.py`: verificacion de auth/security.
- `scripts/verification/verify_migration.py`: verificacion general de migraciones.
- `scripts/maintenance/create_incidents_from_reports.py`: mantenimiento de incidentes.

### 3.8 Pruebas

- `tests/`: suite automatica usada por pytest por defecto.
	- `tests/test_auth.py`
	- `tests/test_reports.py`
	- `tests/test_incidents.py`
	- `tests/test_contract.py`
	- `tests/test_health.py`
- `tests/manual/`: pruebas manuales y smoke tests no bloqueantes.
- `tests/manual/fixtures/`: imagenes y recursos de pruebas manuales.

## 4) Flujos funcionales importantes

### 4.1 Flujo de reporte

1. cliente envia reporte a ruta de reportes.
2. backend valida payload y guarda registro.
3. backend encola procesamiento ML.
4. worker procesa y actualiza resultado.
5. backend calcula deduplicacion/prioridad segun contexto.

### 4.2 Flujo de deduplicacion

1. se extraen embeddings visuales.
2. se consultan candidatos con indices FAISS.
3. se incorpora proximidad geografica y similitud textual.
4. se calcula score fusionado y se decide duplicado/no duplicado.

## 5) Endpoints de deduplicacion actuales

- `POST /deduplication/check`
- `POST /deduplication/similar`
- `GET /deduplication/stats`
- `POST /deduplication/index/rebuild`
- `POST /deduplication/index/save`

## 6) Ejecucion local

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Swagger: `http://localhost:8000/docs`

## 7) Pruebas del modulo

### Suite automatica

```powershell
cd backend
pytest
```

### Manuales (ejemplo)

```powershell
cd backend
pytest tests/manual/test_b07_deduplication.py -q
```

En Windows para FAISS/Torch:

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
pytest tests/manual/test_b07_deduplication.py -q
$env:KMP_DUPLICATE_LIB_OK=$null
```

## 8) Integraciones del backend

- backend recibe solicitudes de frontend.
- backend usa PostgreSQL/PostGIS para persistencia.
- backend usa Redis/RQ para cola de tareas.
- backend usa MinIO/storage para archivos.
- backend consume artefactos de ML para inferencia.

## 9) Estado de organizacion

1. `backend/docs` se vacio y quedo fuera del flujo documental.
2. scripts de verificacion/mantenimiento ya no estan sueltos en raiz.
3. pruebas manuales y fixtures se movieron fuera de la raiz del modulo.
4. artefactos generados (coverage/logs/cache) no forman parte del codigo fuente.
