# SIRCCD - Documentacion Tecnica Completa

## Sistema Inteligente Urbano para Reporte y Priorizacion de Danos Viales

**Version del documento:** 1.0  
**Fecha:** 2026-04-05  
**Estado del proyecto:** En desarrollo activo

---

## Tabla de Contenidos

1. [Vision General del Proyecto](#1-vision-general-del-proyecto)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Modulo Backend](#3-modulo-backend)
4. [Modulo Frontend](#4-modulo-frontend)
5. [Modulo ML (Machine Learning)](#5-modulo-ml-machine-learning)
6. [Modulo Infraestructura](#6-modulo-infraestructura)
7. [Modulo Mobile](#7-modulo-mobile)
8. [Flujo Funcional Completo](#8-flujo-funcional-completo)
9. [Stack Tecnologico](#9-stack-tecnologico)
10. [Guia de Inicio Rapido](#10-guia-de-inicio-rapido)
11. [Estructura de Directorios](#11-estructura-de-directorios)
12. [API Reference](#12-api-reference)
13. [Modelos de Datos](#13-modelos-de-datos)
14. [Pipeline de Deduplicacion](#14-pipeline-de-deduplicacion)
15. [Internacionalizacion](#15-internacionalizacion)
16. [Testing](#16-testing)
17. [Despliegue y DevOps](#17-despliegue-y-devops)
18. [Notas Tecnicas y Troubleshooting](#18-notas-tecnicas-y-troubleshooting)

---

## 1. Vision General del Proyecto

### Que es SIRCCD?

SIRCCD es una plataforma integral que permite a ciudadanos reportar danos viales (baches, grietas, hundimientos, etc.) mediante fotografias geolocalizadas, y a operadores municipales gestionar, priorizar y resolver dichos reportes de forma eficiente.

### Problema que resuelve

Las ciudades enfrentan desafios criticos en la gestion del mantenimiento vial:

- **Reportes duplicados**: Multiples ciudadanos reportan el mismo dano, generando ruido operativo.
- **Priorizacion subjetiva**: Sin datos objetivos, la priorizacion depende de criterios arbitrarios.
- **Falta de visibilidad**: Los operadores no tienen una vista consolidada del estado vial de la ciudad.
- **Tiempos de respuesta lentos**: Sin automatizacion, el ciclo reporte-resolucion es ineficiente.

### Solucion

SIRCCD aborda estos problemas mediante:

1. **Clasificacion automatica por ML**: Modelos YOLO entrenados clasifican el tipo y severidad del dano vial a partir de fotografias.
2. **Deduplicacion multimodal**: Combinacion de embeddings visuales (ResNet/CLIP), proximidad geografica y similitud textual para detectar reportes duplicados.
3. **Priorizacion inteligente**: Algoritmo que pondera severidad, frecuencia de reportes, ubicacion y contexto urbano.
4. **Dashboard operativo**: Interfaz web con mapas, filtros, tablas y KPIs en tiempo real para operadores municipales.
5. **App movil** (planificada): Aplicacion Flutter para que ciudadanos envien reportes desde el campo.

### Actores del Sistema

| Actor | Rol | Interfaz |
|-------|-----|----------|
| **Ciudadano** | Reporta danos viales con foto y ubicacion | App movil (futuro) / API directa |
| **Operador municipal** | Gestiona reportes, actualiza estados, prioriza | Dashboard web (frontend) |
| **Administrador** | Gestiona usuarios, configuracion del sistema | Dashboard web (frontend) |
| **Sistema ML** | Clasifica imagenes, detecta duplicados | Procesamiento automatico (backend) |

---

## 2. Arquitectura del Sistema

### Diagrama de Alto Nivel

```
                    +-------------------+
                    |   App Movil       |
                    |   (Flutter)       |
                    +--------+----------+
                             |
                             | REST API
                             v
+-------------------+   +-------------------+   +-------------------+
|   Frontend        |   |   Backend         |   |   ML Pipeline     |
|   (Next.js)       |<->|   (FastAPI)       |<--|   (PyTorch/YOLO)  |
|   Dashboard Web   |   |   API + Workers   |   |   Training        |
+-------------------+   +--------+----------+   +-------------------+
                             |       |
                    +--------+--+  +-+----------+
                    |           |  |             |
               +----v---+ +----v--+-+ +--------v--+
               |PostgreSQL| | Redis  | |   MinIO   |
               |+PostGIS | | Queue  | |  Storage  |
               +---------+ +--------+ +-----------+
```

### Flujo de Datos Principal

```
Ciudadano envia reporte (foto + ubicacion + descripcion)
    |
    v
Backend recibe y valida el reporte
    |
    v
Worker async procesa el reporte:
    ├── Clasificacion ML (tipo de dano, severidad)
    ├── Anonimizacion de imagen (si aplica)
    ├── Extraccion de embeddings visuales
    ├── Busqueda de duplicados (FAISS + geo + texto)
    └── Calculo de prioridad
    |
    v
Reporte clasificado y deduplicado almacenado
    |
    v
Frontend muestra al operador en dashboard
    ├── Mapa geoespacial con reportes/incidentes
    ├── Tabla de gestion con filtros
    ├── KPIs y metricas en tiempo real
    └── Flujo de actualizacion de estados
```

### Organizacion del Monorepo

```
sirccd-monorepo/
├── backend/      # Producto: API y logica de negocio
├── frontend/     # Producto: Dashboard web municipal
├── ml/           # Producto: Pipeline de ML y entrenamiento
├── infra/        # Plataforma: Infraestructura y CI/CD
├── mobile/       # Plataforma: App movil ciudadana
└── docs/         # Documentacion centralizada
```

**Convencion de ubicacion**:
- Codigo fuente → dentro de cada modulo
- Tests → `modulo/tests/`
- Tests manuales → `modulo/tests/manual/`
- Scripts → `modulo/scripts/`
- Documentacion → `docs/` (centralizada)

---

## 3. Modulo Backend

### 3.1 Proposito

El backend es el nucleo del sistema. Expone una API REST, gestiona la persistencia, ejecuta la logica de negocio, coordina el procesamiento ML asincrono y ofrece capacidades de exportacion de datos.

### 3.2 Stack Tecnologico

| Componente | Tecnologia | Version |
|-----------|------------|---------|
| Framework web | FastAPI | 0.115.0 |
| ORM | SQLAlchemy | 2.0+ |
| Migraciones | Alembic | - |
| Base de datos | PostgreSQL + PostGIS | 16+ |
| Cola de tareas | Redis + RQ | Redis 7, RQ 5 |
| Almacenamiento | MinIO | 7.2+ |
| ML Inference | PyTorch + torchvision | 2.1+ |
| Busqueda vectorial | FAISS | 1.7.4+ |
| Auth | JWT (python-jose) | - |

### 3.3 Arquitectura en Capas

```
┌─────────────────────────────────────────┐
│              API Layer                   │
│  (FastAPI routes + OpenAPI + deps)       │
├─────────────────────────────────────────┤
│            Service Layer                 │
│  (Logica de negocio, ML, dedup, etc.)   │
├─────────────────────────────────────────┤
│          Models / DB Layer               │
│  (SQLAlchemy ORM + Alembic migrations)  │
├─────────────────────────────────────────┤
│            Tasks Layer                   │
│  (Redis RQ workers asincrono)           │
└─────────────────────────────────────────┘
```

### 3.4 Estructura de Directorios

```
backend/
├── api/
│   ├── routes/
│   │   ├── auth.py              # Autenticacion: login, refresh token
│   │   ├── reports.py           # CRUD de reportes + workflow
│   │   ├── incidents.py         # Gestion de incidentes
│   │   ├── deduplication.py     # Verificacion de duplicados, rebuild index
│   │   ├── export.py            # Exportacion CSV/GeoJSON
│   │   ├── health.py            # Health checks del sistema
│   │   ├── pois.py              # Puntos de interes
│   │   └── users.py             # Gestion de usuarios
│   ├── deps.py                  # Dependencias FastAPI (auth, DB, roles)
│   └── openapi.yaml             # Especificacion OpenAPI
├── core/
│   ├── config.py                # Settings y variables de entorno
│   ├── security.py              # JWT, hashing, utilidades de auth
│   ├── database.py              # Inicializacion de la BD
│   └── metrics.py               # Metricas Prometheus
├── db/
│   ├── base.py                  # Base declarativa SQLAlchemy
│   └── session.py               # Gestion de sesiones
├── models/                      # Entidades ORM
│   ├── user.py                  # Usuario del sistema
│   ├── report.py                # Reporte ciudadano
│   ├── incident.py              # Incidente consolidado
│   ├── poi.py                   # Punto de interes
│   └── metric.py                # Metrica del sistema
├── schemas/                     # Contratos Pydantic (request/response)
│   ├── auth.py
│   ├── report.py
│   ├── incident.py
│   ├── deduplication.py
│   ├── export.py
│   ├── poi.py
│   └── user.py
├── services/                    # Logica de negocio
│   ├── ml_service.py            # Wrapper de inferencia ML
│   ├── anonymizer.py            # Anonimizacion de imagenes
│   ├── deduplication_service.py # Embeddings, FAISS, fusion de scores
│   ├── priority_service.py      # Calculo de prioridad de incidentes
│   ├── export_service.py        # Generacion de exportaciones
│   ├── health_service.py        # Verificacion de salud del sistema
│   ├── queue_service.py         # Gestion de cola de trabajos
│   └── storage.py               # Abstraccion de MinIO
├── tasks/
│   ├── ml_tasks.py              # Tareas worker para procesamiento ML
│   ├── worker.py                # Entry point worker (Linux/Mac)
│   └── worker_windows.py        # Entry point worker (Windows)
├── scripts/
│   ├── evaluate_dedup_embeddings.py
│   ├── verification/
│   │   ├── verify_b02.py        # Verificacion de migraciones/schema
│   │   ├── verify_b03.py        # Verificacion de auth/seguridad
│   │   └── verify_migration.py
│   └── maintenance/
│       └── create_incidents_from_reports.py
├── tests/
│   ├── test_auth.py
│   ├── test_reports.py
│   ├── test_incidents.py
│   ├── test_contract.py
│   ├── test_health.py
│   └── manual/
│       └── fixtures/            # Imagenes y recursos de test
├── main.py                      # Inicializacion de la app FastAPI
├── requirements.txt
├── Dockerfile
├── alembic.ini
└── .env.example
```

### 3.5 Endpoints de la API

#### Autenticacion (`/api/auth`)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/api/auth/login` | Autenticacion con credenciales, retorna JWT |
| POST | `/api/auth/refresh` | Renueva token de acceso |
| POST | `/api/auth/register` | Registro de nuevo usuario |
| GET | `/api/auth/me` | Perfil del usuario autenticado |

#### Reportes (`/api/reports`)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/reports` | Lista reportes con filtros y paginacion |
| POST | `/api/reports` | Crea nuevo reporte (multipart: imagen + datos) |
| GET | `/api/reports/{id}` | Detalle de un reporte |
| PATCH | `/api/reports/{id}` | Actualiza estado/metadata del reporte |
| DELETE | `/api/reports/{id}` | Elimina reporte (admin) |

#### Incidentes (`/api/incidents`)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/incidents` | Lista incidentes con filtros |
| GET | `/api/incidents/{id}` | Detalle de incidente con reportes asociados |
| PATCH | `/api/incidents/{id}` | Actualiza estado/prioridad del incidente |
| POST | `/api/incidents/{id}/merge` | Fusiona reportes en un incidente |

#### Deduplicacion (`/api/deduplication`)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/api/deduplication/check` | Verifica si un reporte es duplicado |
| GET | `/api/deduplication/similar/{id}` | Busca reportes similares |
| POST | `/api/deduplication/rebuild` | Reconstruye indice FAISS |

#### Exportacion (`/api/export`)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/export/csv` | Exporta datos en formato CSV |
| GET | `/api/export/geojson` | Exporta datos en formato GeoJSON |

#### Health (`/api/health`)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/health` | Estado general del sistema |
| GET | `/api/health/db` | Estado de la base de datos |
| GET | `/api/health/redis` | Estado de Redis |
| GET | `/api/health/minio` | Estado de MinIO |

#### Usuarios (`/api/users`)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/users` | Lista usuarios (admin) |
| GET | `/api/users/{id}` | Detalle de usuario |
| PATCH | `/api/users/{id}` | Actualiza usuario |
| DELETE | `/api/users/{id}` | Desactiva usuario (admin) |

#### Puntos de Interes (`/api/pois`)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/pois` | Lista POIs cercanos a una coordenada |

### 3.6 Servicios Principales

#### ML Service (`services/ml_service.py`)
Wrapper que carga modelos YOLO pre-entrenados y ejecuta inferencia sobre imagenes de reportes. Retorna clasificacion de tipo de dano y nivel de severidad.

#### Deduplication Service (`services/deduplication_service.py`)
Pipeline de deduplicacion multimodal:
1. Extrae embeddings visuales (ResNet50 y/o CLIP)
2. Consulta indice FAISS para candidatos cercanos
3. Calcula proximidad geografica (distancia Haversine)
4. Calcula similitud textual (si hay descripcion)
5. Fusiona scores con pesos configurables
6. Decide si es duplicado segun umbral

#### Priority Service (`services/priority_service.py`)
Calcula la prioridad de un incidente considerando:
- Severidad del dano (clasificacion ML)
- Numero de reportes asociados (frecuencia)
- Ubicacion (proximidad a POIs criticos: escuelas, hospitales)
- Antiguedad del primer reporte

#### Storage Service (`services/storage.py`)
Abstraccion sobre MinIO para almacenamiento de archivos:
- Upload de imagenes de reportes
- Generacion de URLs presignadas
- Gestion de buckets

#### Queue Service (`services/queue_service.py`)
Gestion de la cola Redis RQ:
- Encolar tareas de procesamiento ML
- Monitorear estado de trabajos
- Reintentos y manejo de fallos

### 3.7 Modelos de Datos (ORM)

#### User
```python
- id: UUID (PK)
- email: String (unique)
- hashed_password: String
- full_name: String
- role: Enum (citizen, operator, admin)
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime
```

#### Report
```python
- id: UUID (PK)
- user_id: UUID (FK → User)
- incident_id: UUID (FK → Incident, nullable)
- image_url: String
- description: Text (nullable)
- latitude: Float
- longitude: Float
- status: Enum (pending, processing, classified, duplicate, resolved)
- damage_type: String (nullable, set by ML)
- severity: Float (nullable, set by ML)
- embedding: Binary (nullable, vector for dedup)
- created_at: DateTime
- updated_at: DateTime
```

#### Incident
```python
- id: UUID (PK)
- title: String
- description: Text
- latitude: Float
- longitude: Float
- status: Enum (open, in_progress, resolved, closed)
- priority: Float
- damage_type: String
- report_count: Integer
- created_at: DateTime
- updated_at: DateTime
- resolved_at: DateTime (nullable)
```

#### POI (Point of Interest)
```python
- id: UUID (PK)
- name: String
- category: String (school, hospital, government, etc.)
- latitude: Float
- longitude: Float
- source: String
```

### 3.8 Configuracion (Variables de Entorno)

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
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ML
ML_MODEL_PATH=models/best.pt
ML_CONFIDENCE_THRESHOLD=0.5

# FAISS
FAISS_INDEX_PATH=data/faiss_index.bin
DEDUP_SIMILARITY_THRESHOLD=0.85
```

---

## 4. Modulo Frontend

### 4.1 Proposito

Dashboard web para operadores municipales. Permite visualizar reportes e incidentes en mapas, gestionar flujos de trabajo, monitorear KPIs y exportar datos.

### 4.2 Stack Tecnologico

| Componente | Tecnologia | Version |
|-----------|------------|---------|
| Framework | Next.js (App Router) | 14.1+ |
| UI | React | 18.2+ |
| Lenguaje | TypeScript | 5.3+ |
| Estilos | Tailwind CSS | 3.4+ |
| Estado | Zustand | 4.5+ |
| HTTP | Axios | 1.6+ |
| Mapas | React Leaflet | 4.2+ |
| Graficos | Recharts | 3.7+ |
| i18n | i18next + react-i18next | 25.8+ |

### 4.3 Arquitectura

```
┌─────────────────────────────────────┐
│            App Router               │
│  (pages, layouts, route protection) │
├─────────────────────────────────────┤
│           Components                │
│  (MapView, Tables, Filters, Modals)│
├───────────────┬─────────────────────┤
│   Services    │      Store          │
│  (API client) │  (Zustand stores)   │
├───────────────┴─────────────────────┤
│     Hooks / Utils / Types           │
│  (useAuth, geo, dates, labels)      │
└─────────────────────────────────────┘
```

### 4.4 Estructura de Directorios

```
frontend/src/
├── app/                         # Next.js App Router
│   ├── layout.tsx               # Layout raiz (providers, theme)
│   ├── page.tsx                 # Pagina principal
│   ├── login/page.tsx           # Flujo de autenticacion
│   ├── register/page.tsx        # Registro
│   └── dashboard/               # Vistas operativas
│       ├── page.tsx             # Dashboard principal
│       ├── reports/page.tsx     # Gestion de reportes
│       ├── incidents/page.tsx   # Gestion de incidentes
│       ├── map/page.tsx         # Vista de mapa
│       └── admin/page.tsx       # Administracion
├── components/
│   ├── MapView.tsx              # Mapa Leaflet con marcadores
│   ├── HeatmapLayer.tsx         # Capa de calor geoespacial
│   ├── FilterPanel.tsx          # Panel de filtros de busqueda
│   ├── IncidentsTable.tsx       # Tabla operativa de incidentes
│   ├── StatusTimeline.tsx       # Timeline de estados
│   ├── StatusUpdateModal.tsx    # Modal de actualizacion
│   ├── LocationPicker.tsx       # Selector de ubicacion en mapa
│   ├── ImageUpload.tsx          # Upload de imagenes
│   ├── I18nProvider.tsx         # Provider de internacionalizacion
│   ├── LanguageSwitcher.tsx     # Selector ES/EN
│   ├── Button.tsx               # Boton base
│   ├── Card.tsx                 # Tarjeta base
│   ├── Toast.tsx                # Notificaciones
│   └── MiniMap.tsx              # Mapa miniatura
├── services/                    # Capa de cliente API
│   ├── api.ts                   # Cliente HTTP base (Axios)
│   ├── authService.ts           # Operaciones de auth
│   ├── reportsService.ts        # CRUD de reportes
│   ├── incidentsService.ts      # CRUD de incidentes
│   ├── metricsService.ts        # Consulta de metricas
│   ├── poisService.ts           # Consulta de POIs
│   └── usersService.ts          # Gestion de usuarios
├── store/                       # Estado global (Zustand)
│   ├── authStore.ts             # Token, usuario, sesion
│   ├── reportsStore.ts          # Lista y filtros de reportes
│   ├── incidentsStore.ts        # Lista y filtros de incidentes
│   └── uiStore.ts               # Estado de UI (sidebar, modals)
├── hooks/
│   ├── useAuth.ts               # Proteccion de rutas
│   ├── useAsync.ts              # Manejo de flujos async
│   ├── useToast.ts              # Notificaciones
│   └── useMediaQuery.ts         # Responsive design
├── i18n/                        # Archivos de traduccion ES/EN
├── utils/
│   ├── geo.ts                   # Utilidades geoespaciales
│   ├── dates.ts                 # Formateo de fechas
│   ├── labels.ts                # Traduccion de labels de dominio
│   ├── cn.ts                    # Merge de clases CSS
│   └── index.ts                 # Tipos compartidos
└── types/                       # Definiciones TypeScript
```

### 4.5 Componentes Clave

#### MapView
Componente central que renderiza un mapa Leaflet con:
- Marcadores de reportes coloreados por severidad
- Marcadores de incidentes con icono diferenciado
- Clusters para densidad alta
- Popups con detalle al hacer clic
- Integracion con filtros del FilterPanel

#### HeatmapLayer
Capa de calor superpuesta al mapa que muestra densidad de reportes/incidentes. Util para identificar zonas criticas.

#### FilterPanel
Panel lateral con filtros por:
- Tipo de dano
- Severidad (rango)
- Estado
- Fecha (rango)
- Area geografica

#### IncidentsTable
Tabla de datos con:
- Columnas: ID, tipo, severidad, estado, prioridad, reportes, fecha
- Ordenamiento por columna
- Paginacion
- Acciones: ver detalle, actualizar estado

### 4.6 Gestion de Estado (Zustand)

```typescript
// authStore - Sesion del usuario
{
  user: User | null,
  token: string | null,
  isAuthenticated: boolean,
  login(credentials): Promise<void>,
  logout(): void,
  refreshToken(): Promise<void>
}

// reportsStore - Reportes
{
  reports: Report[],
  filters: ReportFilters,
  loading: boolean,
  fetchReports(): Promise<void>,
  setFilters(filters): void
}

// incidentsStore - Incidentes
{
  incidents: Incident[],
  filters: IncidentFilters,
  loading: boolean,
  fetchIncidents(): Promise<void>,
  updateStatus(id, status): Promise<void>
}

// uiStore - UI global
{
  sidebarOpen: boolean,
  activeModal: string | null,
  toggleSidebar(): void,
  openModal(name): void,
  closeModal(): void
}
```

### 4.7 Flujo de Autenticacion

1. Usuario accede a `/login`
2. Ingresa credenciales (email + password)
3. Frontend envia POST a `/api/auth/login`
4. Backend valida y retorna `{ access_token, refresh_token }`
5. `authStore` almacena tokens
6. Axios interceptor adjunta `Authorization: Bearer <token>` a cada request
7. Hook `useAuth` protege rutas del dashboard - redirige a `/login` si no hay sesion
8. Refresh automatico antes de expiracion del access token

---

## 5. Modulo ML (Machine Learning)

### 5.1 Proposito

Pipeline completo de Machine Learning para:
- Entrenar modelos de deteccion/clasificacion de danos viales
- Generar embeddings visuales para deduplicacion
- Anonimizar imagenes (difuminar rostros, placas)
- Evaluar y versionar modelos

### 5.2 Stack Tecnologico

| Componente | Tecnologia |
|-----------|------------|
| Framework DL | PyTorch 2.1+ |
| Deteccion objetos | Ultralytics YOLO |
| Busqueda vectorial | FAISS |
| Augmentacion | Albumentations |
| Geoespacial | GeoPandas |
| Visualizacion | TensorBoard, W&B |
| Notebooks | Jupyter |
| Storage | MinIO |

### 5.3 Estructura de Directorios

```
ml/
├── anonymization/               # Sub-pipeline de anonimizacion
│   ├── train.py                 # Entrenamiento de modelo de anonimizacion
│   ├── inference.py             # Inferencia de anonimizacion
│   ├── data.yaml                # Config de dataset
│   ├── scripts/                 # Utilidades de preparacion
│   ├── notebooks/               # Notebooks de anonimizacion
│   └── docs/                    # Guias especificas
├── datasets/                    # Repositorio de datos de entrenamiento
│   └── pois_google/             # Datos de POIs para contexto geo
├── train/                       # Scripts de entrenamiento estructurado
├── notebooks/                   # Notebooks de experimentacion
│   ├── 01_dataset_exploration.ipynb
│   ├── SIRCCD_Training_Colab.ipynb
│   ├── SIRCCD_Training_v3_FromScratch.ipynb
│   ├── SIRCCD_Training_v4_YOLO11l.ipynb
│   └── SIRCCD_Training_v5_H100_Optimized.ipynb
├── inference/                   # Tests de inferencia
├── embeddings/                  # Utilidades de extraccion vectorial
├── deduplication/               # Soporte experimental de dedup
├── models/                      # Modelos entrenados exportados
├── runs/                        # Salidas de ejecucion de entrenamiento
├── configs/                     # Configuraciones de entrenamiento
├── scripts/
│   ├── verify_environment.py    # Verificacion de ambiente
│   ├── download_from_minio.py   # Descarga de artefactos
│   ├── upload_to_minio.py       # Subida de artefactos
│   └── utils/
├── docs/                        # Guias detalladas de ML
│   ├── M-01_ENVIRONMENT_SETUP.md
│   ├── GUIA_* (guias de Colab)
│   ├── CHECKLIST_COLAB.md
│   ├── V3_TRAINING_OPTIMIZATION.md
│   ├── CLOUD_TRAINING.md
│   └── PYTHON_314_COMPATIBILITY_ISSUE.md
└── requirements-training.txt
```

### 5.4 Pipeline de Entrenamiento

```
1. Preparacion de datos
   ├── Recoleccion de imagenes de danos viales
   ├── Anotacion (bounding boxes + clases)
   ├── Augmentacion (Albumentations)
   └── Split train/val/test

2. Entrenamiento
   ├── Seleccion de arquitectura (YOLO11l, etc.)
   ├── Configuracion de hiperparametros
   ├── Ejecucion (local GPU o Colab/H100)
   └── Monitoreo (TensorBoard / W&B)

3. Evaluacion
   ├── Metricas: mAP, precision, recall, F1
   ├── Matrices de confusion
   ├── Inferencia visual sobre test set
   └── Comparacion con versiones anteriores

4. Versionado y despliegue
   ├── Exportacion de pesos (best.pt)
   ├── Upload a MinIO
   └── Actualizacion en backend (ML_MODEL_PATH)
```

### 5.5 Notebooks Disponibles

| Notebook | Descripcion |
|----------|-------------|
| `01_dataset_exploration.ipynb` | Analisis exploratorio del dataset |
| `SIRCCD_Training_Colab.ipynb` | Entrenamiento base en Google Colab |
| `SIRCCD_Training_v3_FromScratch.ipynb` | Entrenamiento desde cero con optimizaciones |
| `SIRCCD_Training_v4_YOLO11l.ipynb` | Entrenamiento con YOLO11 Large |
| `SIRCCD_Training_v5_H100_Optimized.ipynb` | Optimizado para GPU H100 |
| `SIRCCD_Anonymization_Training.ipynb` | Entrenamiento del modelo de anonimizacion |

### 5.6 Integracion con Backend

Los artefactos ML fluyen al backend de la siguiente manera:

1. **Pesos del modelo** (`best.pt`) → `backend/models/` o MinIO
2. **Configuracion** → Variables de entorno del backend
3. **Embeddings** → Servicio de deduplicacion usa los mismos modelos de extraccion

---

## 6. Modulo Infraestructura

### 6.1 Proposito

Centralizar la configuracion de infraestructura, orquestacion Docker y pipelines CI/CD.

### 6.2 Estado Actual

Estructura base creada, con placeholders para evolucion:

```
infra/
├── ci-cd/       # Pipelines y jobs (placeholder)
├── compose/     # Archivos compose por ambiente (placeholder)
└── docker/      # Dockerfiles reutilizables (placeholder)
```

### 6.3 Docker Compose (actual en raiz)

#### `docker-compose.yml` - Orquestacion principal

Servicios definidos:
- **postgres**: PostgreSQL 16 + PostGIS
- **redis**: Redis 7 (cola de tareas)
- **minio**: MinIO (almacenamiento de objetos)
- **backend**: FastAPI app
- **worker**: Worker RQ para tareas async
- **frontend**: Next.js app

#### `docker-compose.minio.yml` - MinIO standalone

Para desarrollo local con solo MinIO.

#### `backend/docker-compose.db.yml` - Solo base de datos

Para desarrollo del backend con servicios de datos locales.

### 6.4 Scripts de Desarrollo

#### `dev.ps1` - Inicio local (PowerShell)
Levanta todos los servicios necesarios para desarrollo local.

```powershell
powershell -ExecutionPolicy Bypass -File dev.ps1
```

#### `dev-stop.ps1` - Parar servicios
Detiene todos los servicios levantados.

```powershell
powershell -ExecutionPolicy Bypass -File dev-stop.ps1
```

### 6.5 Plan de Migracion

1. Mover compose files a `infra/compose/`
2. Definir convencion de nombres por ambiente (dev, staging, prod)
3. Publicar pipelines CI/CD en `infra/ci-cd/`
4. Centralizar Dockerfiles en `infra/docker/`

---

## 7. Modulo Mobile

### 7.1 Proposito

Aplicacion movil para ciudadanos que permite reportar danos viales desde el campo con captura de foto y ubicacion GPS.

### 7.2 Estado Actual

**Scaffold minimo** - no inicializado como proyecto Flutter completo.

```
mobile/
├── assets/      # Recursos estaticos (placeholder)
└── lib/         # Codigo fuente (placeholder)
```

### 7.3 Arquitectura Planificada

```
lib/
├── features/
│   ├── auth/           # Login y registro
│   ├── reports/        # Creacion y seguimiento de reportes
│   └── profile/        # Perfil del usuario
├── shared/
│   ├── services/       # Cliente API y logica de negocio
│   ├── widgets/        # Componentes UI reutilizables
│   └── state/          # Gestion de estado (GetX o Provider)
```

### 7.4 Funcionalidades Planificadas

1. **Login/Registro**: Autenticacion ciudadana
2. **Captura de imagen**: Camara o galeria
3. **Captura de ubicacion**: GPS automatico + ajuste manual en mapa
4. **Envio de reporte**: Foto + ubicacion + descripcion opcional
5. **Seguimiento**: Ver estado de reportes propios
6. **Offline-first**: Encolar reportes sin conexion, sincronizar cuando haya red

### 7.5 Proximos Pasos

1. Inicializar proyecto Flutter completo (`flutter create`)
2. Definir arquitectura y estrategia de estado
3. Implementar primer vertical: login → crear reporte → ver estado

---

## 8. Flujo Funcional Completo

### 8.1 Ciclo de Vida de un Reporte

```
CIUDADANO                    SISTEMA                      OPERADOR
    |                           |                            |
    |-- Envia reporte --------->|                            |
    |   (foto+ubicacion+desc)   |                            |
    |                           |-- Valida y almacena ------>|
    |                           |-- Encola procesamiento     |
    |                           |                            |
    |                           |<-- Worker procesa:         |
    |                           |    1. Clasificacion ML     |
    |                           |    2. Anonimizacion        |
    |                           |    3. Embeddings           |
    |                           |    4. Deduplicacion        |
    |                           |    5. Prioridad            |
    |                           |                            |
    |                           |-- Si duplicado:            |
    |                           |   Asocia a incidente       |
    |                           |   existente                |
    |                           |                            |
    |                           |-- Si nuevo:                |
    |                           |   Crea nuevo incidente     |
    |                           |                            |
    |                           |-- Notifica dashboard ----->|
    |                           |                            |
    |                           |                            |-- Ve en mapa/tabla
    |                           |                            |-- Actualiza estado
    |                           |                            |-- Asigna prioridad
    |                           |                            |
    |<-- Estado actualizado ----|<-- Cambia estado ----------|
    |                           |                            |
```

### 8.2 Aprobacion y deduplicacion de reportes

Cuando un reporte se aprueba (manual por operador, o automatico si confianza ML >= 0.75):

1. Se ejecuta `_resolve_incident_dedup()`: geo (30m) + visual gate (cosine >= 0.82)
2. Si hay incidente coincidente → el reporte se asocia al incidente existente
3. Si no hay coincidencia → se crea un nuevo incidente con ese reporte

### 8.3 Estados de un Reporte

```
pending → [approved | rejected]
```

- **pending**: Recibido, esperando revision
- **approved**: Aprobado (manual o auto). Incidente creado o actualizado
- **rejected**: Descartado por operador

### 8.3 Estados de un Incidente

```
open → in_progress → resolved → closed
```

- **open**: Nuevo, sin atencion
- **in_progress**: Operador trabajando en el
- **resolved**: Reparacion completada
- **closed**: Verificado y cerrado

---

## 9. Stack Tecnologico

### Resumen Completo

| Capa | Tecnologia | Uso |
|------|------------|-----|
| **Frontend** | Next.js 14, React 18, TypeScript | Dashboard web |
| **Estilos** | Tailwind CSS 3.4 | Diseno responsive |
| **Estado** | Zustand 4.5 | Estado global del frontend |
| **Mapas** | React Leaflet 4.2 | Visualizacion geoespacial |
| **Graficos** | Recharts 3.7 | KPIs y metricas |
| **i18n** | i18next | Internacionalizacion ES/EN |
| **Backend** | FastAPI 0.115 | API REST |
| **ORM** | SQLAlchemy 2.0 | Acceso a datos |
| **Migraciones** | Alembic | Schema evolution |
| **DB** | PostgreSQL 16 + PostGIS | Persistencia + geoespacial |
| **Cache/Queue** | Redis 7 + RQ | Cola de tareas async |
| **Storage** | MinIO 7.2 | Almacenamiento de imagenes |
| **ML Framework** | PyTorch 2.1 | Deep Learning |
| **Deteccion** | Ultralytics YOLO | Deteccion de danos |
| **Vectores** | FAISS 1.7 | Busqueda por similitud |
| **Augmentacion** | Albumentations | Augmentacion de datos |
| **Monitoring** | TensorBoard, W&B | Monitoreo de entrenamiento |
| **Contenedores** | Docker, Docker Compose | Orquestacion |
| **Mobile** | Flutter (planificado) | App ciudadana |

---

## 10. Guia de Inicio Rapido

### Prerequisitos

- Python 3.10+
- Node.js 18+
- Docker y Docker Compose
- Git

### Opcion 1: Docker Compose (recomendado)

```bash
# Clonar repositorio
git clone <repo-url>
cd sirccd-monorepo

# Levantar todos los servicios
docker compose up -d

# Verificar
# Backend: http://localhost:8000/docs (Swagger)
# Frontend: http://localhost:3000
# MinIO: http://localhost:9001 (consola)
```

### Opcion 2: Desarrollo Local (Windows)

```powershell
# Levantar servicios de infraestructura
powershell -ExecutionPolicy Bypass -File dev.ps1

# Terminal 1: Backend
cd backend
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2: Worker
cd backend
..\.venv\Scripts\Activate.ps1
python tasks/worker_windows.py

# Terminal 3: Frontend
cd frontend
npm install
npm run dev
```

### Opcion 3: Solo Backend

```powershell
# Levantar solo BD + Redis + MinIO
cd backend
docker compose -f docker-compose.db.yml up -d

# Ejecutar backend
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Verificacion Post-Inicio

1. Swagger UI: `http://localhost:8000/docs`
2. Health check: `GET http://localhost:8000/api/health`
3. Frontend: `http://localhost:3000`
4. MinIO Console: `http://localhost:9001`

---

## 11. Estructura de Directorios (Arbol Completo)

```
sirccd-monorepo/
│
├── backend/
│   ├── api/
│   │   ├── routes/          # 8 routers (auth, reports, incidents, etc.)
│   │   ├── deps.py          # Dependencias compartidas
│   │   └── openapi.yaml     # Spec OpenAPI
│   ├── core/                # Config, seguridad, DB init, metricas
│   ├── db/                  # Session factory, base declarativa
│   ├── models/              # 5 entidades ORM
│   ├── schemas/             # 7 schemas Pydantic
│   ├── services/            # 8 servicios de negocio
│   ├── tasks/               # Workers async (RQ)
│   ├── scripts/             # Verificacion, evaluacion, mantenimiento
│   ├── tests/               # Unit + manual tests
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router (5+ rutas)
│   │   ├── components/      # 14+ componentes
│   │   ├── services/        # 7 servicios API
│   │   ├── store/           # 4 stores Zustand
│   │   ├── hooks/           # 4 hooks reutilizables
│   │   ├── i18n/            # Traducciones ES/EN
│   │   ├── utils/           # Geo, dates, labels, cn
│   │   └── types/           # Tipos TypeScript
│   ├── public/              # Assets estaticos
│   ├── docs/                # Doc especifica de frontend
│   ├── package.json
│   ├── Dockerfile
│   └── next.config.js
│
├── ml/
│   ├── anonymization/       # Sub-pipeline completo
│   ├── datasets/            # Datos de entrenamiento
│   ├── train/               # Scripts de entrenamiento
│   ├── notebooks/           # 6+ notebooks Jupyter
│   ├── inference/           # Testing de inferencia
│   ├── embeddings/          # Extraccion vectorial
│   ├── deduplication/       # Soporte experimental
│   ├── models/              # Modelos exportados
│   ├── configs/             # Configuraciones
│   ├── scripts/             # Utilidades
│   ├── docs/                # Guias de ML
│   └── requirements-training.txt
│
├── infra/
│   ├── ci-cd/               # (placeholder)
│   ├── compose/             # (placeholder)
│   └── docker/              # (placeholder)
│
├── mobile/
│   ├── assets/              # (placeholder)
│   └── lib/                 # (placeholder)
│
├── docs/                    # Documentacion centralizada
│   ├── README.md            # Indice de documentacion
│   ├── monorepo.md          # Arquitectura global
│   ├── backend.md           # Deep dive backend
│   ├── frontend.md          # Deep dive frontend
│   ├── ml.md                # Deep dive ML
│   ├── infra.md             # Deep dive infraestructura
│   ├── mobile.md            # Deep dive mobile
│   └── DOCUMENTACION_COMPLETA.md  # Este documento
│
├── docker-compose.yml       # Orquestacion principal
├── docker-compose.minio.yml # MinIO standalone
├── dev.ps1                  # Script inicio local
├── dev-stop.ps1             # Script parada local
├── .github/                 # GitHub Actions
└── .gitignore
```

---

## 12. API Reference

### Autenticacion

Todas las rutas protegidas requieren header:
```
Authorization: Bearer <access_token>
```

### Roles

| Rol | Permisos |
|-----|----------|
| `citizen` | Crear reportes, ver reportes propios |
| `operator` | Todo lo de citizen + gestionar incidentes, ver todos los reportes |
| `admin` | Todo lo de operator + gestionar usuarios, configuracion del sistema |

### Formato de Respuesta Estandar

```json
{
  "data": { ... },
  "message": "Success",
  "status_code": 200
}
```

### Paginacion

```
GET /api/reports?page=1&page_size=20
```

Respuesta incluye:
```json
{
  "data": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### Filtros Comunes

```
GET /api/reports?status=classified&damage_type=pothole&severity_min=0.7
GET /api/incidents?status=open&priority_min=0.8&sort_by=priority&sort_order=desc
```

---

## 13. Modelos de Datos

### Diagrama Entidad-Relacion

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
│ created  │       │ status       │       │ damage_type │
│ updated  │       │ damage_type  │       │ report_count│
└──────────┘       │ severity     │       │ created     │
                   │ embedding    │       │ updated     │
                   │ created      │       │ resolved_at │
                   │ updated      │       └─────────────┘
                   └──────────────┘
                          *
                          │
                          │ nearby
                          v
                   ┌──────────────┐
                   │     POI      │
                   │──────────────│
                   │ id (PK)      │
                   │ name         │
                   │ category     │
                   │ lat/lng      │
                   │ source       │
                   └──────────────┘
```

### Relaciones

- **User → Report**: Un usuario puede crear muchos reportes (1:N)
- **Incident → Report**: Un incidente agrupa multiples reportes duplicados (1:N)
- **Report ↔ POI**: Relacion implicita por proximidad geografica

---

## 14. Pipeline de Deduplicacion

### 14.1 Descripcion

El pipeline de deduplicacion es una de las capacidades mas criticas del sistema. Evita que multiples reportes del mismo dano generen incidentes separados.

### 14.2 Enfoque Multimodal

La deduplicacion combina tres senales:

#### Signal 1: Similitud Visual
- Extraccion de embeddings con ResNet50 y/o CLIP
- Busqueda de vecinos cercanos en indice FAISS
- Score de similitud coseno entre vectores

#### Signal 2: Proximidad Geografica
- Query ST_DWithin (PostGIS) en la columna Geography: radio de 30 metros
- Candidatos ordenados por fecha de creacion (mas antiguo primero)

#### Signal 3: Similitud Visual (gate)
- Cosine similarity entre embeddings ResNet50 de la imagen del reporte y la imagen del incidente candidato
- Umbral: `DEDUP_VISUAL_GATE_THRESHOLD = 0.82`
- Sin imagen disponible en reporte o candidato: no se fusiona (no hay geo-only fallback)

### 14.3 Gate geo+visual en aprobacion

El pipeline activo en produccion es un gate secuencial, **no** un score fusionado:

```python
# 1. Filtro geografico (PostGIS)
candidatos = ST_DWithin(incidentes_abiertos, ubicacion_reporte, 30m)

# 2. Gate visual por cada candidato
for candidato in candidatos:
    if reporte.imagen is None: return None  # no fusionar
    if candidato.imagen is None: continue   # saltar sin imagen
    sim = cosine_similarity(embed(reporte.imagen), embed(candidato.imagen))
    if sim >= 0.82:
        return candidato  # fusionar
return None  # crear nuevo incidente
```

### 14.4 Servicio FAISS (exploratorio / API)

Disponible en `/api/v1/deduplication`. Combina tres senales con scores ponderados:

```python
score_final = (0.45 * score_visual_primario) +
              (0.25 * score_visual_secundario) +  # CLIP
              (0.20 * score_geo) +
              (0.10 * score_texto)

# Umbral: score_final >= DEDUPLICATION_SCORE_THRESHOLD (0.72)
```

- Indice FAISS IndexFlatIP, dimension 2048 (ResNet50) o 512 (CLIP)
- Persistencia en `storage/faiss_index.bin` (volumen Docker `backend_storage`)
- Rebuild via `POST /api/v1/deduplication/index/rebuild` (admin)

### 14.5 Flujo completo en aprobacion

```
Operador aprueba reporte  (o confianza ML >= 0.75 → autoaprueba)
    |
    v
_resolve_incident_dedup(db, report, report_image, log)
    |
    ├── Sin imagen del reporte → crear nuevo incidente
    |
    ├── Sin candidatos geo (30m) → crear nuevo incidente
    |
    └── Para cada candidato geo:
            ├── Sin imagen del candidato → saltar
            ├── sim = cosine(embed(img_reporte), embed(img_candidato))
            ├── sim >= 0.82 → fusionar con candidato
            └── sim < 0.82 → saltar
        Ningun candidato pasa → crear nuevo incidente
```

### 14.6 Precarga de modelos

Los embedders ResNet50 y CLIP se precalentam en un hilo de fondo al arrancar el backend.  
Volumenes Docker: `torch_cache` (`/root/.cache/torch`) y `hf_cache` (`/root/.cache/huggingface`) evitan re-descarga entre reinicios.

---

## 15. Internacionalizacion

### Idiomas Soportados

- **Espanol (ES)**: Idioma principal
- **Ingles (EN)**: Idioma secundario

### Implementacion

- Libreria: `i18next` + `react-i18next`
- Archivos de traduccion en `frontend/src/i18n/`
- Componente `LanguageSwitcher` para cambio en tiempo real
- Provider `I18nProvider` en layout raiz

### Uso en Componentes

```typescript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  return <h1>{t('dashboard.title')}</h1>;
}
```

---

## 16. Testing

### Backend

```bash
# Ejecutar todos los tests
cd backend
pytest

# Con cobertura
pytest --cov=. --cov-report=html

# Tests especificos
pytest tests/test_auth.py
pytest tests/test_reports.py
pytest tests/test_incidents.py
pytest tests/test_contract.py
pytest tests/test_health.py
```

#### Tests disponibles:
- `test_auth.py`: Autenticacion, JWT, refresh, permisos
- `test_reports.py`: CRUD de reportes, validaciones
- `test_incidents.py`: Gestion de incidentes
- `test_contract.py`: Contratos de API (schemas)
- `test_health.py`: Health checks

### Frontend

```bash
cd frontend
npm test          # Unit tests
npm run lint      # ESLint
npm run type-check # TypeScript
```

### ML

Tests manuales via notebooks y scripts de inferencia en `ml/inference/`.

---

## 17. Despliegue y DevOps

### Ambientes

| Ambiente | Descripcion | Estado |
|----------|-------------|--------|
| **Local** | Docker Compose + dev scripts | Operativo |
| **Staging** | Por definir | Pendiente |
| **Produccion** | Por definir | Pendiente |

### Docker

Cada modulo productivo tiene su `Dockerfile`:
- `backend/Dockerfile`
- `frontend/Dockerfile`

### Orquestacion

```yaml
# docker-compose.yml levanta:
services:
  postgres:    # BD principal + PostGIS
  redis:       # Cola de tareas
  minio:       # Object storage
  minio-init:  # Job unico: crea buckets y permisos publicos
  backend:     # API FastAPI (precarga embedders ResNet50+CLIP al arranque)
  frontend:    # Dashboard Next.js

volumes:
  backend_storage:   # Imagenes de reportes e indice FAISS
  torch_cache:       # Cache PyTorch/torchvision (evita re-descarga)
  hf_cache:          # Cache HuggingFace (modelos CLIP)
```

### CI/CD (planificado)

Estructura preparada en `infra/ci-cd/` para:
- Lint y type-check en cada PR
- Tests automatizados
- Build de imagenes Docker
- Deploy a staging/produccion

---

## 18. Notas Tecnicas y Troubleshooting

### Windows: FAISS + PyTorch

En Windows, puede ser necesario configurar:
```powershell
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
```
Esto resuelve conflictos de la libreria OpenMP cuando FAISS y PyTorch coexisten.

### Python 3.14 Compatibility

Documentado en `ml/docs/PYTHON_314_COMPATIBILITY_ISSUE.md`. Algunas dependencias de ML pueden no ser compatibles con Python 3.14. Usar Python 3.10-3.12 para el modulo ML.

### Worker en Windows

Usar `tasks/worker_windows.py` en lugar de `tasks/worker.py`, ya que RQ tiene limitaciones en Windows con fork().

### MinIO Local

Credenciales por defecto:
- Access Key: `minioadmin`
- Secret Key: `minioadmin`
- Consola: `http://localhost:9001`

### Base de Datos

- Migraciones con Alembic: `alembic upgrade head`
- PostGIS habilitado para queries geoespaciales
- Session management via `db/session.py`

### Puertos por Defecto

| Servicio | Puerto |
|----------|--------|
| Backend (FastAPI) | 8000 |
| Frontend (Next.js) | 3000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| MinIO API | 9000 |
| MinIO Console | 9001 |

---

*Documento generado el 2026-04-05. Consultar la documentacion individual de cada modulo en `docs/` para detalles actualizados.*
