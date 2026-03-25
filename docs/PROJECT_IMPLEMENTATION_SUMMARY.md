# Resumen de Implementación del Proyecto SIRCCD

**Fecha de actualización**: 5 de marzo de 2026  
**Estado del proyecto**: En desarrollo activo  
**Progreso general**: ~65% completado

---

## 📋 Tabla de Contenidos

1. [Visión General](#-visión-general)
2. [Épicas Completadas](#-épicas-completadas)
3. [Infraestructura](#-infraestructura)
4. [Datasets y Machine Learning](#-datasets-y-machine-learning)
5. [Backend y API](#-backend-y-api)
6. [Frontend Web](#-frontend-web)
7. [Documentación Técnica](#-documentación-técnica)
8. [Próximos Pasos](#-próximos-pasos)

---

## 🎯 Visión General

El **SIRCCD** (Sistema Inteligente Urbano para Reporte y Priorización de Daños Viales) es un sistema completo que integra:

- **Detección automática** de daños viales mediante IA (YOLOv8)
- **Reportes ciudadanos** con geolocalización GPS
- **Deduplicación inteligente** visual y geográfica
- **Priorización multicriterio** basada en severidad, riesgo y antigüedad
- **Panel municipal GIS interactivo** con mapas y KPIs en tiempo real
- **Protección de privacidad** mediante anonimización automática

### Arquitectura del Monorepo

```
sirccd-monorepo/
├── backend/        ✅ FastAPI + PostgreSQL/PostGIS + autenticación JWT
├── frontend/       ✅ Next.js 14 + Tailwind CSS + react-leaflet
├── mobile/         ⏳ Flutter (pendiente)
├── ml/            ✅ YOLOv8 + pipeline de datos + MinIO
├── infra/         ✅ Docker Compose + configuraciones
└── docs/          ✅ Arquitectura + guías + actas
```

---

## ✅ Épicas Completadas

### D - Dataset Preparation (100% completado)

| Tarea | Estado | Descripción |
|-------|--------|-------------|
| **D-01** | ✅ | Organización y unificación de datasets (RDD2022, RDD2020, N-RDD2024, Pothole-600) |
| **D-02** | ✅ | Limpieza, validación y balanceo de clases |
| **D-03** | ✅ | División estratificada 70/20/10 (train/val/test) con seed 42 |
| **D-04** | ✅ | Etiquetado automático en formato YOLO |
| **D-05** | ✅ | Clasificación de severidad (baja/media/alta) |
| **D-06** | ✅ | Descarga de 328 POIs de Santiago (escuelas, hospitales, puentes) |
| **D-07** | ✅ | Ingesta a MinIO (115,952 archivos: 57,976 imágenes + labels) |
| **D-08** | ✅ | Anonimización de metadatos EXIF y protección de privacidad |

**Resultado**: Dataset de **57,976 imágenes** procesado, limpio, estratificado, versionado (v1.0.0) y anonimizado.

---

### B - Backend (85% completado)

| Tarea | Estado | Descripción |
|-------|--------|-------------|
| **B-01** | ✅ | Inicialización de proyecto FastAPI con estructura modular |
| **B-02** | ✅ | Esquema de base de datos PostgreSQL + PostGIS con Alembic |
| **B-03** | ✅ | Sistema de autenticación JWT con roles (ciudadano/supervisor/admin) |
| **B-04** | ✅ | Endpoints CRUD para reportes, incidentes y usuarios |
| **B-05** | ✅ | Middleware de anonimización (blur de rostros/placas con OpenCV) |
| **B-06** | ✅ | Inferencia ML con YOLOv8 + queue asíncrono (Redis) |
| **B-07** | ✅ | Deduplicación visual con embeddings y clustering DBSCAN |
| **B-08** | ✅ | Priorización multicriterio y gestión de ciclo de vida |
| **B-09** | ✅ | Exportaciones GeoJSON/CSV para análisis GIS |
| **B-10** | ✅ | Observabilidad con health checks y métricas Prometheus |
| **B-11** | ✅ | Testing unitario, integración y contratos (Schemathesis) |

**Resultado**: API REST completa con ML, deduplicación, priorización, exportaciones y observabilidad. Cobertura de tests ~75%.

---

### W - Frontend Web (Dashboard Municipal) (80% completado)

| Tarea | Estado | Descripción |
|-------|--------|-------------|
| **W-01** | ✅ | Setup Next.js 14 + TypeScript + Tailwind + Zustand + routing |
| **W-02** | ✅ | Formulario de reporte ciudadano con foto, validaciones y geolocalización GPS |
| **W-03** | ✅ | Página de login con JWT, redirección y persistencia de sesión |
| **W-04** | ✅ | Mapa interactivo Leaflet con marcadores dinámicos por prioridad |
| **W-05** | ✅ | Listado de incidentes con filtros, panel dividido (lista + mapa), exportación CSV |
| **W-06** | ✅ | Detalle de incidente: foto antes/después, análisis ML, ubicación, prioridad, historial |
| **W-07** | ✅ | Dashboard KPIs con métricas TTR, SLA, gráficos Recharts (barras, donut, prioridades) |
| **W-08** | ✅ | Gestión de usuarios y roles — CRUD completo (admin), activar/desactivar, filtros |
| **W-09** | ✅ | Página de reportes ciudadanos — lista paginada, revisión (aprobar/rechazar) por supervisores |
| **W-10** | ✅ | Internacionalización ES/EN con react-i18next, LanguageSwitcher, html[lang], mejoras de accesibilidad |
| **W-11** | ⏳ | Panel de deduplicación visual — comparar imágenes, fusionar/marcar único (pendiente) |
| **W-12** | ⏳ | Exportación desde UI — botones CSV/GeoJSON en dashboard de incidentes (pendiente) |
| **W-13** | ⏳ | Notificaciones en tiempo real — WebSocket/SSE para alertas de nuevos incidentes (pendiente) |
| **W-14** | ⏳ | Mapa de calor y zonas de riesgo — heatmap + capa GeoJSON de POIs (pendiente) |

**Resultado**: Dashboard municipal completamente funcional con autenticación por roles, gestión de incidentes y reportes, KPIs, mapa interactivo, CRUD de usuarios, i18n ES/EN y accesibilidad.

---

### M - Machine Learning (50% completado)

| Tarea | Estado | Descripción |
|-------|--------|-------------|
| **M-01** | ✅ | Configuración de entorno Python 3.12 con Ultralytics |
| **M-02** | ⏳ | Entrenamiento de modelo YOLOv8n baseline (en progreso) |
| **M-03** | ⏳ | Fine-tuning y optimización de hiperparámetros (pendiente) |
| **M-04** | ⏳ | Implementación de embeddings para deduplicación (pendiente) |
| **M-05** | ⏳ | API de inferencia en tiempo real (pendiente) |

**Resultado**: Entorno preparado, dataset listo, entrenamiento en progreso.

---

## 🏗️ Infraestructura

### Docker y Contenedores

| Servicio | Estado | Configuración |
|----------|--------|---------------|
| **MinIO** | ✅ | Almacenamiento S3-compatible en localhost:9000 |
| **PostgreSQL** | ✅ | Base de datos con PostGIS en localhost:5432 |
| **Backend API** | ✅ | FastAPI en localhost:8000 |
| **Frontend** | ✅ | Next.js en localhost:3000 |

**Archivos clave**:
- `docker-compose.minio.yml` - MinIO con volumen persistente
- `backend/alembic/` - Migraciones de base de datos
- `dev.ps1` / `dev-stop.ps1` - Scripts de inicio/parada de servicios

### MinIO (Object Storage)

- **Bucket**: `sirccd-datasets`
- **Versión actual**: v1.0.0
- **Contenido**: 57,976 imágenes + 57,976 labels = 115,952 archivos
- **Metadata**: SHA256 hashing para integridad
- **Estructura**:
  ```
  v1.0.0/
  ├── train/
  │   ├── images/
  │   └── labels/
  ├── val/
  │   ├── images/
  │   └── labels/
  └── test/
      ├── images/
      └── labels/
  ```

---

## 🤖 Datasets y Machine Learning

### Dataset Final (v1.0.0)

**Estadísticas**:
- **Total de imágenes**: 57,976
- **Clases**: 2 (bache, grieta)
- **Formato**: YOLO con bounding boxes
- **División**:
  - Train: 40,543 imágenes (70%)
  - Val: 11,614 imágenes (20%)
  - Test: 5,819 imágenes (10%)
- **Seed de reproducibilidad**: 42

**Distribución de clases** (train):
- Bache: 16,111 muestras (39.5%)
- Grieta: 21,347 muestras (52.4%)
- Señal: 3,287 muestras (8.1%)

**Severidad**:
- Baja: Área <1% (baches) o longitud <20% (grietas)
- Media: Área 1-3% (baches) o longitud 20-40% (grietas)
- Alta: Área ≥3% (baches) o longitud ≥40% (grietas)

### Fuentes de Datos

1. **RDD2022** (Road Damage Dataset 2022) - Multi-país
2. **RDD2020** (Road Damage Dataset 2020) - India, Japón, República Checa
3. **N-RDD2024** (Norwegian Road Damage) - Noruega
4. **Pothole-600** - Dataset especializado en baches

### Puntos de Interés Catalogados

Se descargaron **328 POIs** de Santiago de los Caballeros, RD mediante Google Places API:

| Categoría | Cantidad |
|-----------|----------|
| Escuelas | 60 |
| Universidades | 60 |
| Hospitales | 60 |
| Clínicas | 60 |
| Estaciones de bomberos | 19 |
| Estaciones de policía | 49 |
| Puentes | 20 |

**Archivos**: 7 GeoJSON en `ml/datasets/pois_google/`

### Scripts de Procesamiento

Ubicados en `ml/datasets/scripts/`:

1. **organize_datasets.py** - Unifica datasets de diferentes fuentes a formato YOLO
2. **process_pothole600.py** - Convierte máscaras de Pothole-600 a bounding boxes
3. **clean_and_balance.py** - Valida imágenes, elimina duplicados, balancea clases
4. **split_dataset.py** - División estratificada reproducible
5. **validate_split.py** - Verifica proporciones y estratificación
6. **label_severity.py** - Etiqueta severidad automáticamente
7. **catalog_pois.py** - Descarga POIs desde OpenStreetMap (obsoleto)
8. **google_places_pois.py** - Descarga POIs desde Google Places API
9. **generate_theoretical_risk_zones.py** - Genera buffers de 200m alrededor de POIs
10. **upload_to_minio.py** - Ingesta dataset a MinIO con versionado
11. **anonymize_dataset.py** - Elimina EXIF sensible y difumina rostros/placas

### Privacidad y Anonimización

✅ **Implementado en D-08**:
- Eliminación de metadatos EXIF (GPS, usuario, dispositivo)
- Detección de rostros con Haar Cascade (OpenCV)
- Detección de placas vehiculares (YOLOv8 - preparado)
- Difuminado automático con Gaussian Blur (51x51, sigma=30)
- Reporte de anonimización en JSON

**Resultado del análisis**:
- 57,976 imágenes procesadas
- 0 imágenes con EXIF sensible detectado (0.0%)
- Dataset completamente anonimizado en `ml/datasets/processed/anonymized/`

---

## 🖥️ Backend y API

### Tecnologías

- **Framework**: FastAPI 0.110+
- **Base de datos**: PostgreSQL 15 + PostGIS 3.4
- **ORM**: SQLAlchemy 2.0
- **Migraciones**: Alembic
- **Autenticación**: JWT (pyjwt)
- **Password hashing**: bcrypt
- **Testing**: pytest + pytest-cov

### Estructura del Código

```
backend/
├── alembic/                    # Migraciones de BD
├── api/routes/                 # Endpoints API REST
│   ├── auth.py                # Login, registro, refresh token
│   ├── reports.py             # CRUD de reportes + upload imágenes
│   ├── incidents.py           # CRUD de incidentes + estados
│   ├── deduplication.py       # Agrupación y fusión de duplicados
│   ├── export.py              # Exportaciones GeoJSON/CSV
│   └── health.py              # Health checks y métricas
├── services/                   # Lógica de negocio
│   ├── anonymizer.py          # Blur de rostros/placas (OpenCV)
│   ├── ml_service.py          # Inferencia YOLOv8
│   ├── queue_service.py       # Cola asíncrona (Redis)
│   ├── deduplication_service.py # Embeddings + DBSCAN
│   ├── priority_service.py    # Scoring multicriterio
│   ├── export_service.py      # Generación GeoJSON/CSV
│   ├── health_service.py      # Checks de PostgreSQL, Redis, MinIO
│   └── storage.py             # Almacenamiento local (MinIO pendiente)
├── core/
│   ├── config.py              # Configuración central
│   ├── security.py            # JWT, bcrypt, RBAC
│   ├── database.py            # Sesión de SQLAlchemy
│   └── metrics.py             # Métricas Prometheus
├── models/                     # Modelos SQLAlchemy (User, Report, Incident, etc.)
├── schemas/                    # Esquemas Pydantic para validación
├── tasks/                      # Worker tasks para procesamiento asíncrono
├── tests/                      # Tests unitarios, integración y contratos
│   ├── test_auth.py           # 20+ tests de autenticación
│   ├── test_reports.py        # 15+ tests de reportes
│   ├── test_incidents.py      # 18+ tests de incidentes
│   ├── test_contract.py       # Tests de contrato con Schemathesis
│   └── conftest.py            # Fixtures compartidas
├── main.py                     # Entry point de FastAPI
├── worker.py                   # Worker para procesamiento asíncrono
└── requirements.txt           # 30+ dependencias (FastAPI, SQLAlchemy, etc.)
```

### Modelos de Datos Principales

1. **User** - Usuarios con roles (ciudadano/supervisor/admin)
2. **Report** - Reportes ciudadanos con foto + GPS
3. **Incident** - Incidentes validados con clasificación IA
4. **DuplicateGroup** - Grupos de reportes duplicados
5. **WorkOrder** - Órdenes de trabajo operativas
6. **RepairHistory** - Historial de reparaciones

### Endpoints Implementados

**Autenticación** (`/api/auth/`):
- `POST /login` - Login con email/password, retorna JWT
- `POST /register` - Registro de nuevos usuarios con validación
- `POST /refresh` - Renovación de access token con refresh token
- `GET /me` - Información del usuario autenticado

**Reportes** (`/api/reports/`):
- `GET /` - Lista paginada con filtros (estado, tipo, fechas, usuario)
- `POST /` - Crear reporte + upload imagen + anonimización automática
- `GET /{id}` - Detalle de reporte con foto e incidente asociado
- `PATCH /{id}` - Actualizar reporte (solo propietario o admin)
- `DELETE /{id}` - Soft delete de reporte
- `POST /{id}/process` - Forzar procesamiento ML del reporte

**Incidentes** (`/api/incidents/`):
- `GET /` - Lista con filtros (estado, prioridad, tipo, rango de fechas)
- `GET /{id}` - Detalle completo con reportes asociados
- `PATCH /{id}` - Actualizar estado o prioridad
- `POST /{id}/transition` - Cambiar estado con validación de transiciones
- `GET /{id}/priority` - Calcular y retornar score de prioridad actualizado
- `POST /recalculate-priorities` - Recalcular todas las prioridades (admin)

**Deduplicación** (`/api/deduplication/`):
- `POST /find-duplicates` - Detectar reportes similares con embeddings
- `GET /groups` - Listar grupos de duplicados
- `GET /groups/{id}` - Detalle de grupo con reportes
- `POST /groups/{id}/merge` - Fusionar reportes duplicados en un incidente
- `POST /groups/{id}/mark-unique` - Marcar reporte como único (no duplicado)

**Exportaciones** (`/api/export/`):
- `GET /incidents/geojson` - Exportar incidentes en formato GeoJSON para GIS
- `GET /incidents/csv` - Exportar incidentes en CSV para análisis
- `GET /kpis/csv` - Exportar KPIs agregados en CSV
- Soporte para filtros: fechas, ubicación, estado, prioridad

**Observabilidad** (`/api/health/`):
- `GET /` - Health check completo (PostgreSQL, Redis, MinIO)
- `GET /metrics` - Métricas en formato Prometheus
- `GET /ready` - Readiness probe para Kubernetes
- `GET /live` - Liveness probe para Kubernetes

### Sistema de Priorización Multicriterio

**Fórmula implementada**:

```
score_prioridad = (
    severidad_peso * severidad_normalizada +
    riesgo_peso * riesgo_normalizado +
    antiguedad_peso * antiguedad_normalizada +
    densidad_peso * densidad_normalizada
)
```Servicios Implementados

**AnonymizerService** (`services/anonymizer.py`):
- Detección de rostros con Haar Cascade (OpenCV)
- Detección de placas vehiculares (doble método: Haar + color/forma)
- Blur gaussiano de alta intensidad (kernel 51x51, sigma 30)
- Expansión de regiones (+20%) para cobertura completa
- Estadísticas detalladas por imagen procesada

**MLInferenceService** (`services/ml_service.py`):
- Carga de modelo YOLOv8 (weights autodetectables)
- Inferencia con confidence threshold configurable
- Extracción de bounding boxes y clasificación
- Cálculo de severidad por área/longitud
- Cache de resultados para evitar reprocesamiento

**QueueService** (`services/queue_service.py`):
- Cola asíncrona con Redis
- Enqueue de tareas de ML
- Worker para procesamiento en background
- Retry automático en caso de fallo
- Monitoreo de tamaño de cola

**DeduplicationService** (`services/deduplication_service.py`):
- Extracción de embeddings visuales (CLIP/ResNet)
- Cálculo de similitud coseno entre imágenes
- Clustering con DBSCAN (eps=0.3, min_samples=2)
- Filtrado geográfico (radio de 50m)
- Creación de grupos de duplicados

**PriorityService** (`services/priority_service.py`):
- Cálculo de score multicriterio (severidad, riesgo, antigüedad, densidad)
- Pesos configurables por factor
- Normalización de valores [0-100]
- Asignación automática de nivel (crítica/alta/media/baja)
- Gestión del ciclo de vida con 6 estados

**ExportService** (`services/export_service.py`):
- Generación de GeoJSON compatible con QGIS, Leaflet, Mapbox
- Exportación CSV para Excel/Sheets
- Filtros avanzados por múltiples criterios
- Límite de 10,000 registros por exportación
- Compresión opcional para archivos grandes

**HealthCheckService** (`services/health_service.py`):
- Verificación de conexión a PostgreSQL + PostGIS
- Verificación de Redis (queue)
- Verificación de MinIO (opcional)
- Tiempo de respuesta de cada componente
- Métricas en formato Prometheus

### Testing y Coverage

**Suite de Tests Implementada**:
- **Tests de autenticación** (`test_auth.py`): 20+ tests
  - Login, registro, refresh tokens
  - Validación de roles y permisos
  - Expiración de tokens
  
- **Tests de reportes** (`test_reports.py`): 15+ tests
  - CRUD completo
  - Upload de imágenes
  - Anonimización automática
  - Procesamiento ML
  
- **Tests de incidentes** (`test_incidents.py`): 18+ tests
  - CRUD con filtros
  - Transiciones de estado
  - Cálculo de prioridad
  - Asignación de incidentes
  
- **Tests de contrato** (`test_contract.py`): Schemathesis
  - Validación automática de OpenAPI schema
  - Tests de todas las rutas
  - Fuzzing de inputs

**Cobertura**:
- **Coverage total**: ~75%
- **Servicios core**: >85%
- **Endpoints API**: >70%
- **Archivo de reporte**: `backend/coverage.xml`
- **HTML report**: `backend/htmlcov/index.html`

**Ejecución de Tests**:
```bash
# Todos los tests
pytest backend/tests/ -v

# Con coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Solo tests rápidos
pytest -m "not slow"

# Tests de contrato
pytest backend/tests/test_contract.py --hypothesis-profile=ci
``
- Densidad: 0.15 (15%)

**Niveles de prioridad**:
- Crítica: score ≥ 80
- Alta: score 60-79
- Media: score 40-59
- Baja: score < 40

### Testing y Coverage

- **Tests unitarios**: `pytest backend/tests/unit/`
- **Tests de integración**: `pytest backend/tests/integration/`
- **Coverage**: ~75% de cobertura
- **Archivo de reporte**: `backend/coverage.xml`

---

## 🌐 Frontend Web

### Tecnologías

- **Framework**: Next.js 14 (App Router)
- **Lenguaje**: TypeScript 5+
- **Estilos**: Tailwind CSS 3.4
- **UI Components**: shadcn/ui + Radix UI
- **Iconos**: Lucide React
- **Mapas**: Leaflet + react-leaflet
- **Gráficos**: Recharts
- **HTTP Client**: Axios

### Estructura del Proyecto

```
frontend/
├── src/
│   ├── app/
│   │   ├── dashboard/
│   │   │   ├── page.tsx                  # Dashboard principal (KPIs + gráficos + mapa)
│   │   │   ├── layout.tsx                # Layout del dashboard con LanguageSwitcher
│   │   │   ├── incidents/
│   │   │   │   ├── page.tsx              # Listado de incidentes (split/tabla/mapa)
│   │   │   │   └── [id]/page.tsx         # Detalle de incidente
│   │   │   ├── reports/
│   │   │   │   ├── page.tsx              # Listado de reportes ciudadanos
│   │   │   │   └── new/page.tsx          # Formulario crear reporte
│   │   │   └── users/page.tsx            # Gestión de usuarios (admin)
│   │   ├── login/page.tsx                # Página de login
│   │   └── layout.tsx                    # Layout raíz con I18nProvider
│   ├── components/
│   │   ├── I18nProvider.tsx              # Proveedor react-i18next + html[lang]
│   │   ├── LanguageSwitcher.tsx          # Toggle ES/EN
│   │   ├── MapView.tsx                   # Mapa Leaflet con marcadores
│   │   ├── MiniMap.tsx                   # Mapa pequeño para formularios
│   │   ├── ImageUpload.tsx               # Upload de imagen con preview
│   │   ├── LocationPicker.tsx            # Selector de coordenadas GPS
│   │   └── ui/                           # Componentes base
│   ├── hooks/
│   │   └── useToast.ts                   # Hook de notificaciones
│   ├── i18n/
│   │   ├── config.ts                     # Configuración i18next + localStorage
│   │   └── locales/
│   │       ├── es.json                   # Traducciones español
│   │       └── en.json                   # Traducciones inglés
│   ├── services/
│   │   ├── api.ts                        # Cliente Axios con interceptores JWT
│   │   ├── authService.ts                # Login, logout, refresh token
│   │   ├── incidentsService.ts           # CRUD incidentes + stats
│   │   ├── reportsService.ts             # CRUD reportes + revisión
│   │   └── usersService.ts               # CRUD usuarios + getMe
│   ├── store/
│   │   └── index.ts                      # Zustand store (auth + user)
│   └── types/
│       └── index.ts                      # Tipos TypeScript (UserRole, Incident, etc.)
└── package.json
```

### Páginas Implementadas

#### 1. Login (`/login`)
- Formulario email/password con validación
- Autenticación JWT contra backend
- Persistencia de sesión en Zustand + localStorage
- Redirección automática si ya autenticado
- `aria-required`, `autoComplete`, LanguageSwitcher

#### 2. Dashboard (`/dashboard`)
- KPIs en tiempo real: total, activos, resueltos, sin asignar, TTR promedio, score promedio
- Barra SLA (cumplimiento ≤48h) con indicador de color
- Gráficos Recharts: barras por estado, donut activos vs resueltos, barras horizontales por prioridad
- Botones de navegación rápida a incidentes, reportes, usuarios y crear reporte
- LanguageSwitcher fijo en esquina superior derecha

#### 3. Incidentes (`/dashboard/incidents`)
- Vista split (lista + mapa), solo tabla o solo mapa
- Filtros: estado, prioridad, tipo de daño, búsqueda de texto
- Paginación, conteo de resultados, exportar CSV
- Mapa de incidentes con marcadores por prioridad

#### 4. Detalle de incidente (`/dashboard/incidents/[id]`)
- Foto antes/después procesada con análisis ML
- Información de ubicación con coordenadas y dirección
- Barra de prioridad multicriterio con color y score
- Cambio de estado (transiciones válidas según rol)
- Historial de cambios y notas internas
- Recalcular prioridad

#### 5. Reportes (`/dashboard/reports`)
- Tabla paginada con imagen, tipo de daño, severidad, estado, ciudad
- Filtros por estado y severidad, búsqueda de texto
- Modal de detalle con acción de aprobar o rechazar (supervisor/admin)

#### 6. Nuevo Reporte (`/dashboard/reports/new`)
- Upload de foto con preview
- LocationPicker (GPS automático o manual) con MiniMap
- Autocompletado de dirección, ciudad, provincia
- Descripción con contador de caracteres

#### 7. Usuarios (`/dashboard/users`)
- Tabla completa con ID, username, email, rol, estado, verificado, fechas
- Filtros por rol, estado activo/inactivo, búsqueda
- Modal crear/editar usuario con todos los campos
- Activar/desactivar y eliminar permanentemente (solo admin)
- Vista de solo lectura para supervisor

#### 8. Internacionalización (i18n)
- `react-i18next` con archivos `es.json` / `en.json`
- Persistencia en `localStorage` (clave `sirccd-lang`)
- `html[lang]` actualizado dinámicamente
- LanguageSwitcher con `aria-label` en login y dashboard
3. **B-03_AUTHENTICATION.md** - Sistema de autenticación JWT con roles
4. **B-03_SUMMARY.md** - Resumen de sistema de autenticación
5. **B-04_IMPLEMENTATION.md** - Implementación de endpoints CRUD
6. **B-05_IMPLEMENTATION.md** - Middleware de anonimización con OpenCV
7. **B-06_IMPLEMENTATION.md** - Inferencia ML con YOLOv8 + queue
8. **B-07_IMPLEMENTATION.md** - Deduplicación con embeddings y DBSCAN
7. **B-07_SUMMARY.md** - Resumen de deduplicación
9. **B-08_IMPLEMENTATION.md** - Priorización multicriterio y ciclo de vida
10. **B-09_IMPLEMENTATION.md** - Exportaciones GeoJSON/CSV
11. **B-10_OBSERVABILITY.md** - Health checks y métricas Prometheus
12. **B-11_TESTING_SUMMARY.md** - Suite de tests y coverage
13. **B-07_QUICKSTART.md** - Guía de inicio rápido del backend
  - Marcadores dinámicos por prioridad
  - Popups con información de incidente
  - Leyenda de colores
  - Carga de hasta 100 incidentes desde API

### Componente MapView (W-04)

**Características**:
- Mapa base de OpenStreetMap (sin API key requerida)
- Centro por defecto: Santo Domingo, RD (18.4861, -69.9312)
- Zoom inicial: 13
- Marcadores SVG personalizados con colores:
  - 🔴 Rojo: Prioridad crítica (#dc2626)
  - 🟠 Naranja: Prioridad alta (#ea580c)
  - 🟡 Amarillo: Prioridad media (#f59e0b)
  - 🔵 Azul: Prioridad baja (#3b82f6)
  - ⚫ Gris: Desconocida (#6b7280)
- **Popups con información**:
  - ID de incidente y reporte
  - ⏳ Pendiente de Implementar en Backend

#### 1. **Integración Completa con MinIO** (Parcialmente implementado)
- ✅ StorageService básico existe
- ❌ Upload de imágenes a MinIO (actualmente local)
- ❌ Generación de URLs presignadas
- ❌ Limpieza automática de imágenes antiguas
- ❌ Sincronización de metadatos imagen-BD

#### 2. **Sistema de Work Orders** (No implementado)
- ❌ CRUD de órdenes de trabajo
- ❌ Asignación automática de órdenes de trabajo
- ❌ Tracking de progreso de reparación
- ❌ Historial de trabajo completado

#### 3. **Optimización de Rutas** (No implementado)
- ❌ Algoritmo TSP (Traveling Salesman Problem)
- ❌ Agrupamiento geográfico de incidentes
- ❌ Generación de rutas óptimas para operadores
- ❌ Exportación a GPS/navegación

#### 4. **Sistema de Notificaciones** (No implementado)
- ❌ Email notifications (reporte creado, incidente resuelto)
- ❌ Push notifications para app móvil
- ❌ Webhooks para integraciones externas
- ❌ Template engine para emails (Jinja2)

#### 5. **Rate Limiting y Seguridad** (No implementado)
- ❌ Límite de requests por usuario/IP
- ❌ Protección contra spam y abuso
- ❌ Cuotas por rol
- ❌ IP blocking automático

#### 6. **Auditoría Completa** (Parcialmente implementado)
- ✅ Logs básicos con Python logging
- ❌ Audit trail de cambios críticos
- ❌ Firma digital de operaciones sensibles
- ❌ Retention policies configurables
- ❌ Log rotation automático

#### 7. **Backup Automatizado** (No implementado)
- ❌ Backup automático de PostgreSQL
- ❌ Backup de imágenes en MinIO
- ❌ Programación de backups (cron)
- ❌ Procedimientos de restore documentados

#### 8. **Permisos Granulares** (Básico implementado)
- ✅ RBAC con 4 roles (ciudadano/operador/supervisor/admin)
- ❌ Permisos específicos por recurso
- ❌ Delegación de permisos temporales
- ❌ Grupos de usuarios

#### 9. **Analytics Avanzado** (No implementado)
- ❌ Predicción de zonas de riesgo con ML
- ❌ Análisis de tendencias temporales
- ❌ Heatmaps de densidad
- ❌ Forecast de próximos incidentes

#### 10. **API Pública** (Parcialmente implementado)
- ✅ OpenAPI/Swagger en `/docs`
- ❌ API keys para terceros
- ❌ Webhooks bidireccionales
- ❌ SDK para clientes (Python, JavaScript)

---

### 🎯 Prioridades de Desarrollo

#### Prioridad Alta (Sprint Actual)

1. **M-02: Completar entrenamiento de YOLOv8n**
   - Entrenar por 100-200 épocas en Colab
   - Evaluar métricas (mAP@0.5, precision, recall)
   - Guardar `best.pt` y publicar en MinIO

2. **W-11: Panel de deduplicación**
   - Lista de grupos de duplicados desde `/api/deduplication/groups`
   - Comparación lado a lado de imágenes
   - Acciones: fusionar grupo → incidente, marcar como único
   - Score de similitud visual y geográfica

3. **W-12: Exportaciones desde la UI**
   - Botón «Exportar CSV» en `/dashboard/incidents`
   - Botón «Exportar GeoJSON» para integración QGIS
   - Respeta los filtros activos en el panel

4. **Integrar MinIO con Backend**
   - Implementar upload a MinIO en `POST /reports`
   - Generar URLs presignadas con expiración (actualmente almacenamiento local)
   - Cleanup automático de imágenes antiguas

#### Prioridad Media (Próximo Sprint)

5. **W-13: Notificaciones en tiempo real**
   - SSE o WebSocket para push de nuevos incidentes
   - Indicador de «nuevos» en el nav del dashboard
   - Toast automático al llegar incidente de alta prioridad

6. **W-14: Mapa de calor y zonas de riesgo**
   - Capa heatmap de densidad de incidentes en MapView
   - Capa GeoJSON de buffers 200m alrededor de POIs
   - Toggle capas en la UI

7. **Sistema de Work Orders**
   - CRUD de órdenes de trabajo (modelo ya existe en BD)
   - Asignación con tracking de progreso
   - Estados: pendiente, en progreso, completada

8. **Mobile App MVP (Flutter)**
   - Configuración del proyecto Flutter
   - Captura de fotos con cámara + GPS automático
   - Envío de reportes a la API
   - Login y autenticación JWT

#### Prioridad Baja (Backlog)

9. **Rate Limiting con Redis**
   - Límites por endpoint y por usuario/IP
   - Protección en `/api/auth/login` y `/api/reports`
   - Headers `X-RateLimit-*` y respuesta `429`

10. **Sistema de Notificaciones por Email**
    - Email al ciudadano cuando su reporte cambia de estado
    - Email al operador cuando se le asigna una orden
    - Templates HTML con Jinja2

11. **Analytics Avanzado**
    - Gráficos de tendencias temporales
    - Predicción de zonas de riesgo con ML
    - Exportación a PDF de reportes ejecutivos

12. **App Móvil Completa**
    - Historial de reportes del usuario
    - Notificaciones push (FCM)
    - Mapa de incidentes cercanos
    - Modo offline con sincronización
1. **B-01_INITIALIZATION.md** - Inicialización de proyecto FastAPI
2. **B-02_DATABASE_SCHEMA.md** - Esquema de base de datos
3. **B-03_AUTHENTICATION.md** - Sistema de autenticación JWT
4. **B-04_IMPLEMENTATION.md** - Implementación de endpoints CRUD
5. **B-06_IMPLEMENTATION.md** - Endpoints de priorización
6. **B-07_IMPLEMENTATION.md** - Endpoints de análisis
7. **B-07_QUICKSTART.md** - Guía de inicio rápido

### Wireframes y Diseño

`docs/diseno/wireframes.md`:
- Mockups de 12,000 | 65+ |
| Frontend | ~3,500 | 30 |
| ML Scripts | ~2,800 | 12 |
| Documentación | ~15,000 | 50+ |
| Tests | ~3,000 | 15 |
| **Total** | **~36,300** | **172+

`docs/matriz_riesgos.md`:
- Identificación de riesgos técnicos
- Estrategias de mitigación
- Planes de contingencia

---

## 🚀 Próximos Pasos
**Backend** (30+ paquetes Python):
- FastAPI, Uvicorn, SQLAlchemy, Alembic (core)
- PyJWT, bcrypt, python-jose (autenticación)
- Pillow, opencv-python (procesamiento de imágenes)
- redis, rq (queue asíncrono)
- ultralytics (YOLOv8)
- sklearn, numpy (ML/embeddings)
- pytest, pytest-cov, schemathesis (testing)
- prometheus-client (métricas)

**Frontend** (40+ paquetes npm):
- Next.js 14, React 18, TypeScript
- Tailwind CSS, Radix UI
- Leaflet, react-leaflet (mapas)
- Recharts (gráficos)
- Axios (HTTP client)
- Zustand (estado global)
- react-i18next, i18next (internacionalización)
- Lucide React (iconos)

**ML** (10+ paquetes Python):
- Ultralytics (YOLOv8)
- OpenCV, Pillow (imágenes)
- NumPy, Pandas (datos)
- tqdm (progress bars)
- piexif (metadatos EXIF
1. **M-02: Completar entrenamiento de YOLOv8n**
   - Entrenar por 100-200 épocas
   - Evaluar métricas (mAP@0.5, precision, recall)
   - Generar reportes de validación

2. **Integrar MinIO con backend**
   - Subir imágenes de reportes a MinIO
   - Generar URLs presignadas para acceso
   - Implementar eliminación de imágenes

3. **W-11: Panel de deduplicación**
   - Lista de grupos de duplicados
   - Comparación lado a lado
   - Fusionar / marcar único

4. **W-12: Exportaciones desde UI**
   - Botones CSV/GeoJSON en listado de incidentes
   - Respetan filtros activos

### Prioridad Media (Próximo Sprint)

5. **M-04: Implementar embeddings para deduplicación**
   - Extraer embeddings con CLIP o ResNet
   - Calcular similitud coseno
   - Clustering con DBSCAN

6. **W-13: Notificaciones en tiempo real**
   - SSE o WebSocket
   - Indicador de nuevos incidentes

7. **W-14: Mapa de calor y capas GeoJSON**
   - Heatmap de densidad
   - Capa de zonas de riesgo (POIs + buffers)

8. **Mobile App MVP**
   - Configuración de Flutter
   - Captura de fotos con GPS
   - Envío de reportes

### Prioridad Baja (Backlog)

9. **Sistema de Work Orders**
   - CRUD de órdenes (modelo ya en BD)
   - Asignación operativa
   - Tracking de progreso

10. **Notificaciones push / email**
    - FCM para móvil
    - SMTP para email
    - Templates Jinja2

11. **Reportes descargables**
    - Exportación a PDF/Excel
    - Gráficos de tendencias
    - Reportes ejecutivos

12. **Dark mode**
    - Tema oscuro para frontend
    - Persistencia de preferencia
    - Animaciones de transición

---

## 📊 Métricas del Proyecto

### Líneas de Código (aproximado)

| Componente | Líneas | Archivos |
|------------|--------|----------|
| Backend | ~8,000 | 45 |
| Frontend | ~6,500 | 50 |
| ML Scripts | ~2,500 | 11 |
| Documentación | ~10,000 | 35 |
| **Total** | **~27,000** | **141** |

### Commits y Versionado

- **Commits totales**: ~55
- **Branches**: main (estable), desarrollo (activo)
- **Estrategia**: Conventional Commits
- **Formato**: `feat(scope): descripción` / `fix(scope): descripción`
- **Último commit**: `545585a` — W-10: i18n ES/EN + accesibilidad

### Dependencias

- **Backend**: 25 paquetes Python
- **Frontend**: 35 paquetes npm
- **ML**: 10 paquetes Python (Ultralytics, OpenCV, PIL)

---

## 🔒 Seguridad y Privacidad

### Medidas Implementadas

✅ **Autenticación**:
- JWT con expiración de 30 minutos
- Refresh tokens de 7 días
- Password hashing con bcrypt (10 rounds)

✅ **Control de acceso**:
- RBAC con 4 roles (ciudadano/operador/supervisor/admin)
- Decoradores de permisos en endpoints
- Validación de ownership en operaciones

✅ **Privacidad de datos**:
- Eliminación de EXIF GPS
- Difuminado de rostros/placas (preparado)
- Dataset anonimizado para training

✅ **Infraestructura**:
- Variables de entorno para secrets
- CORS configurado
- PostgreSQL con SSL (producción)

### Pendientes de Seguridad

⏳ **Por implementar**:
- Rate limiting en API
- Logging de auditoría
- Encriptación de datos sensibles en BD
- Análisis de vulnerabilidades (Dependabot)

---

## 🛠️ Herramientas de Desarrollo

### Backend
- **IDE**: VS Code / PyCharm
- **Linter**: Ruff / Flake8
- **Formatter**: Black
- **Testing**: pytest + pytest-cov
- **DB Client**: pgAdmin / DBeaver

### Frontend
- **IDE**: VS Code
- **Linter**: ESLint
- **Formatter**: Prettier
- **Dev Server**: Next.js Fast Refresh

### ML
- **Notebooks**: Jupyter Lab / Google Colab
- **Tensorboard**: Visualización de entrenamiento
- **Weights & Biases**: Tracking de experimentos (opcional)

### DevOps
- **Contenedores**: Docker Desktop
- **Orquestación**: Docker Compose
- **CI/CD**: GitHub Actions (preparado)

---

## 🎓 Aprendizajes y Mejores Prácticas

### Decisiones Técnicas Importantes

1. **Monorepo vs Multirepo**: Se eligió monorepo para facilitar desarrollo local y compartir tipos
2. **YOLO vs R-CNN**: YOLOv8 por velocidad de inferencia necesaria en tiempo real
3. **PostgreSQL vs MongoDB**: PostgreSQL + PostGIS por capacidades geoespaciales nativas
4. **Next.js vs React SPA**: Next.js por SSR, routing y optimización out-of-the-box
5. **MinIO vs S3**: MinIO para desarrollo local, compatible con S3 en producción

### Patrones de Código█████░░░ 85% (11/11 épicas core + faltan features avanzadas)
Frontend:    ████████░░░░░░░░░░░░ 40% (4/8 páginas principales)
ML/Data:     ████████████████░░░░ 80% (dataset completo, modelo en entrenamiento)
Mobile:      ░░░░░░░░░░░░░░░░░░░░  0% (no iniciado)
DevOps:      ████████████░░░░░░░░ 60% (Docker, compose, falta CI/CD)
Docs:        ████████████████████ 100% (documentación exhaustiva)
```

### Desglose de Backend

**✅ Completado (85%)**:
- Core API (auth, CRUD, filtros)
- Machine Learning (inferencia YOLOv8 + queue)
- Deduplicación (embeddings + clustering)
- Priorización (scoring multicriterio)
- Anonimización (blur de rostros/placas)
- Exportaciones (GeoJSON/CSV)
- Observabilidad (health checks + Prometheus)
- Testing (75% coverage)

**⏳ Parcial**:
- Storage (local, falta MinIO completo) (100-200 épocas en Colab)
2. **Integración MinIO-Backend pendiente** - Necesaria para producción (almacenamiento escalable)
3. **App móvil no iniciada** - Crítica para adopción ciudadana (captura de reportes in-situ)
4. **Work Orders sin implementar** - Necesario para tracking operativo
5. **Frontend incompleto** - Faltan páginas de listado, detalle y deduplicación

**❌ Pendiente (15%)**:
- Work Orders completo
- Optimización de rutas
- Notificaciones
- Rate limiting
- Backups automatizados
- Analytics avanzado
- API pública completa
### Lecciones Aprendidas

✅ **Funcionó bien**:
- División estratificada con seed fijo (reproducibilidad)
- Anonimización temprana en el pipeline
- Documentación exhaustiva desde el inicio
- Docker Compose para desarrollo local

⚠️ **Mejorar**:
- Implementar CI/CD desde el inicio
- Definir contratos de API antes de implementar
- Automatizar más tests de integración
- Usar feature flags para desarrollo incremental

---

## 👥 Equipo y Roles

- **Desarrollo Full-Stack**: Wilson Wilki
- **Machine Learning**: Wilson Wilki
- **Documentación Técnica**: Wilson Wilki
- **DevOps**: Wilson Wilki

---

## 📞 Recursos y Enlaces

### Repositorios y Documentación

- **GitHub**: (privado)
- **Documentación técnica**: `docs/`
- **Guías de ML**: `ml/docs/`
- **API Docs**: http://localhost:8000/docs (Swagger UI)

### Servicios Locales

- **Backend API**: http://localhost:8000
- **Frontend Web**: http://localhost:3000
- **MinIO API**: http://localhost:9000
- **MinIO Console**: http://localhost:9001
- **PostgreSQL**: localhost:5432

### Credenciales de Desarrollo

**MinIO**:
- Usuario: `sirccd_admin`
- Password: `sirccd_password_2026`

**PostgreSQL**:
- Usuario: `sirccd_user`
- Database: `sirccd_db`
- Password: (ver `.env`)

**Admin Backend** (seed):
- Email: `admin@sirccd.com`
- Password: (ver seed script)

---

## 📅 Timeline del Proyecto

| Fecha | Hito |
|-------|------|
| **Enero 2026** | Inicio del proyecto, definición de arquitectura |
| **Febrero 2026** | Implementación de backend (B-01 a B-07) |
| **Febrero 2026** | Procesamiento completo de datasets (D-01 a D-08) |
| **Febrero 2026** | Frontend base con mapa interactivo (W-01 a W-04) |
| **Marzo 2026** | Entrenamiento de modelos ML (M-01, M-02) |
| **Marzo 2026** | **Estado actual** ← ESTAMOS AQUÍ |
| **Abril 2026** | Integración MinIO + Deduplicación (B-08, M-04) |
| **Mayo 2026** | App móvil MVP |
| **Junio 2026** | Testing y optimización |
| **Julio 2026** | Beta privada con municipio piloto |
| **Agosto 2026** | Lanzamiento público |

---

## 📈 Estado General del Proyecto

### Progreso por Componente

```
Backend:     ████████████░░░░░░░░ 70%
Frontend:    ████████░░░░░░░░░░░░ 40%
ML/Data:     ████████████████░░░░ 80%
Mobile:      ░░░░░░░░░░░░░░░░░░░░  0%
DevOps:      ████████████░░░░░░░░ 60%
Docs:        ████████████████████ 100%
```

### Salud del Proyecto

- ✅ **Arquitectura sólida**: Bien diseñada y documentada
- ✅ **Dataset de calidad**: Limpio, balanceado y anonimizado
- ✅ **Backend robusto**: API funcional con autenticación
- ✅ **Frontend funcional**: Dashboard base operativo
- ⚠️ **Modelo ML**: En entrenamiento, falta evaluación
- ⚠️ **Integración**: Falta conectar todos los componentes
- ❌ **App móvil**: No iniciada
- ❌ **Tests E2E**: No implementados

### Bloqueadores Actuales

1. **Modelo ML no entrenado completamente** - Requiere GPU y tiempo
2. **Integración MinIO-Backend pendiente** - Necesaria para imágenes de reportes
3. **App móvil no iniciada** - Crítica para adopción ciudadana

---

## 🎉 Conclusión

El proyecto SIRCCD ha avanzado significativamente en los últimos 2 meses, con una **arquitectura sólida**, un **dataset de alta calidad completamente procesado y anonimizado**, un **backend robusto con autenticación y priorización**, y un **frontend funcional con visualización GIS**.

Los próximos hitos críticos son:
1. ✅ Completar entrenamiento de YOLOv8n
2. ✅ Integrar almacenamiento de imágenes con MinIO
3. ✅ Implementar deduplicación visual
4. ✅ Desarrollar app móvil MVP

Con estos componentes completados, el sistema estará listo para **pruebas piloto** con un municipio real.

---

**Última actualización**: 5 de marzo de 2026  
**Versión del documento**: 1.0  
**Autor**: Wilson Wilki  
**Contacto**: (proyecto académico)
