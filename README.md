# SIRCCD Monorepo

### Sistema Inteligente Urbano para Reporte y Priorización de Daños Viales mediante Geolocalización y Visión por Computadora

**Estado**: En desarrollo activo · **Última actualización**: 6 de marzo de 2026

---

## Descripción

El **SIRCCD** es un sistema integral para digitalizar y optimizar la gestión de daños viales en zonas urbanas. Combina inteligencia artificial, geolocalización y herramientas de gestión municipal para:

- Recibir reportes ciudadanos con foto + GPS.
- Clasificar automáticamente daños (bache, grieta) con YOLOv8.
- Estimar severidad mediante segmentación de área/longitud.
- Eliminar reportes duplicados con análisis visual (CLIP/FAISS) + geográfico (DBSCAN/Haversine).
- Priorizar incidentes según severidad, riesgo, antigüedad y densidad.
- Visualizar incidentes en un panel municipal GIS con KPIs en tiempo real.
- Proteger la privacidad con difuminado automático de rostros y placas (YOLO11s).

---

## Estructura del Monorepo

```
sirccd-monorepo/
├── backend/           API REST (FastAPI + PostgreSQL/PostGIS + JWT + Redis)
│   ├── api/routes/    Endpoints: auth, reports, incidents, export, deduplication, health
│   ├── services/      Lógica: anonymizer, ML inference, priority, dedup, export
│   ├── models/        SQLAlchemy: User, Report, Incident, WorkOrder, etc.
│   ├── alembic/       Migraciones de base de datos
│   ├── tests/         Tests unitarios, integración y contrato
│   └── docs/          Documentación de tareas B-01 a B-11
│
├── frontend/          Dashboard municipal (Next.js 14 + TypeScript + Tailwind)
│   ├── src/app/       App Router: login, dashboard, reports, incidents, users
│   ├── src/components/  UI reutilizable: Button, Card, Toast, Map, etc.
│   ├── src/i18n/      Internacionalización ES/EN
│   └── docs/          Documentación de tareas W-*
│
├── ml/                Machine Learning
│   ├── anonymization/ Pipeline de anonimización (YOLO11s: rostros + placas)
│   ├── datasets/      57,976 imágenes procesadas (v1.0.0) + 20 scripts
│   ├── notebooks/     Notebooks de entrenamiento y exploración
│   ├── configs/       Configuraciones YOLO
│   ├── scripts/       Utilidades ML (verificación, descarga, upload)
│   └── docs/          Guías de entrenamiento y Colab
│
├── mobile/            App ciudadana (Flutter — scaffolded)
│
├── infra/             Docker, Compose, CI/CD (scaffolded)
│
├── data/              Datos auxiliares, POIs, imágenes de prueba
│
└── docs/              Documentación del proyecto
    ├── arquitectura/  Modelos de datos, RBAC, scoring, privacidad
    ├── analisis/      Historias de usuario, matriz de riesgos
    ├── procesos/      Seguimiento de tareas
    ├── diseno/        Wireframes
    └── acta/          Actas de reunión
```

---

## Progreso del Proyecto

| Épica | Descripción | Estado |
|-------|-------------|--------|
| **D** (D-01 a D-08) | Preparación de datasets | ✅ 100% |
| **B** (B-01 a B-11) | Backend API | ✅ 100% |
| **W** (W-01 a W-10) | Frontend dashboard | 🔧 80% (W-11 a W-14 pendientes) |
| **M** (M-01) | Machine Learning | 🔧 Entrenamiento en progreso |

### Resumen por módulo

**Backend** — API REST completa: autenticación JWT con RBAC (ciudadano/supervisor/admin), CRUD de reportes e incidentes, anonimización automática, inferencia ML con cola asíncrona (Redis), deduplicación visual, priorización multicriterio, exportaciones GeoJSON/CSV, health checks con métricas Prometheus, tests (~75% cobertura).

**Frontend** — Dashboard funcional: login/registro, mapa interactivo Leaflet con marcadores por prioridad, KPIs (TTR, SLA, deduplicación), gestión de incidentes con filtros y panel dividido, gestión de usuarios CRUD, revisión de reportes ciudadanos, i18n ES/EN.

**ML** — Dataset de 57,976 imágenes (2 clases: bache, grieta) procesado, limpio y versionado. Pipeline de anonimización con YOLO11s (2 clases: rostro, placa). Notebooks de entrenamiento para Google Colab.

**Datasets** — 4 fuentes (RDD2022, RDD2020, N-RDD2024, Pothole-600), división 70/20/10, severidad automática, 328 POIs de Santiago (Google Places), anonimización de EXIF, ingesta a MinIO.

---

## Stack Tecnológico

| Capa | Tecnologías |
|------|-------------|
| **Backend** | FastAPI · PostgreSQL + PostGIS · SQLAlchemy 2.0 · Alembic · JWT · Redis · Celery/RQ |
| **Frontend** | Next.js 14 · TypeScript · Tailwind CSS · Zustand · React Leaflet · Recharts · react-i18next |
| **ML** | PyTorch · Ultralytics (YOLOv8/YOLO11) · CLIP · FAISS · Annoy · OpenCV · Albumentations |
| **Infraestructura** | Docker Compose · MinIO (S3) · Prometheus |
| **Mobile** | Flutter (planificado) |

---

## Desarrollo Local

### Requisitos

- Python 3.12+ · Node.js 18+ · PostgreSQL 15 + PostGIS · Docker (para MinIO)

### Backend

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:3000 · API: http://localhost:8000/docs

### Inicio rápido (ambos)

```powershell
powershell -ExecutionPolicy Bypass -File dev.ps1
```

### Entrenamiento ML (Colab)

1. Subir `ml/notebooks/SIRCCD_Training_Colab.ipynb` a Google Colab
2. Seleccionar GPU T4/A100
3. Ver guía: `ml/docs/GUIA_RAPIDA_COLAB.md`

---

## Documentación

| Documento | Ubicación |
|-----------|-----------|
| Resumen completo del proyecto | [docs/PROJECT_IMPLEMENTATION_SUMMARY.md](docs/PROJECT_IMPLEMENTATION_SUMMARY.md) |
| Arquitectura lógica | [docs/arquitectura/arquitectura_logica.md](docs/arquitectura/arquitectura_logica.md) |
| Modelo de datos | [docs/arquitectura/modelo_datos.md](docs/arquitectura/modelo_datos.md) |
| RBAC y roles | [docs/arquitectura/rbac.md](docs/arquitectura/rbac.md) |
| Scoring de prioridad | [docs/arquitectura/score_prioridad.md](docs/arquitectura/score_prioridad.md) |
| Privacidad y anonimización | [docs/arquitectura/privacidad_anonimizacion.md](docs/arquitectura/privacidad_anonimizacion.md) |
| Historias de usuario | [docs/analisis/historias_usuario.md](docs/analisis/historias_usuario.md) |
| Matriz de riesgos | [docs/analisis/matriz_riesgos.md](docs/analisis/matriz_riesgos.md) |
| Wireframes | [docs/diseno/wireframes.md](docs/diseno/wireframes.md) |
| Backend (B-01 a B-11) | [backend/docs/](backend/docs/) |
| Frontend mapa (W-04) | [frontend/docs/W-04-MAPA-IMPLEMENTACION.md](frontend/docs/W-04-MAPA-IMPLEMENTACION.md) |
| Guías de entrenamiento ML | [ml/docs/](ml/docs/) |
| Pipeline de anonimización | [ml/anonymization/docs/](ml/anonymization/docs/) |
| Procesamiento de datasets | [ml/datasets/docs/](ml/datasets/docs/) |

---

## Convención de Commits

```
tipo: descripción breve
```

Tipos: `feat:` · `fix:` · `docs:` · `refactor:` · `test:` · `chore:`

---

## Licencia

MIT License
