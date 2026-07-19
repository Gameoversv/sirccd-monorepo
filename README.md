# SIRCCD Monorepo

Sistema Inteligente Urbano para Reporte y Priorización de Daños Viales.

## Estado

Desarrollo activo. Backend y frontend desplegados en Railway. Ver [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) para el estado detallado y las limitaciones conocidas.

## Funcionalidades principales

- Reportes ciudadanos con foto georreferenciada (web y móvil).
- Detección automática del tipo de daño (Roboflow).
- Deduplicación de reportes por similitud visual, geográfica y temporal.
- Priorización según proximidad a puntos de interés sensibles (hospitales, escuelas, etc.).
- Gestión de incidentes con seguimiento de SLA y alertas.
- Anonimización automática de rostros y placas en las imágenes.

Detalle completo en [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md).

## Arquitectura resumida

Backend FastAPI centralizado, consumido por tres clientes independientes (dashboard web, portal ciudadano web, app móvil). Cola de tareas Redis/RQ para procesamiento asíncrono (inferencia ML, alertas SLA). El módulo `ml/` es offline/desacoplado: entrena modelos vía Google Colab, no se sirve directamente en producción.

Diagrama y detalle completo en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Tecnologías

| Área | Stack |
|---|---|
| Backend | FastAPI, SQLAlchemy, PostgreSQL/PostGIS, Redis, RQ, MinIO |
| Frontend | Next.js 14, TypeScript, Zustand, Tailwind CSS, react-leaflet |
| Mobile | Flutter, flutter_bloc, go_router, dio |
| ML | PyTorch, Ultralytics YOLO, transformers, FAISS |
| Infraestructura | Docker, Docker Compose, Nginx |

## Estructura del repositorio

```text
sirccd-monorepo/
├── backend/          API FastAPI, lógica de negocio, base de datos
├── frontend/         Dashboard operativo + portal ciudadano (Next.js)
├── mobile/           App ciudadana (Flutter)
├── ml/               Entrenamiento y anonimización (offline)
├── infra/            Nginx y Docker Compose de MinIO
├── scripts/          Scripts de desarrollo local (dev.ps1, dev-stop.ps1)
├── docs/             Documentación técnica (ver docs/README.md)
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
└── .gitignore
```

## Requisitos previos

Docker + Docker Compose, Python 3.11, Node.js 20+, Flutter SDK (solo para mobile). Detalle en [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).

## Inicio rápido

```bash
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000/api/v1/docs
- Frontend: http://localhost:3000

### Ejecución manual (sin Docker)

```powershell
# Backend
cd backend
python -m venv ../.venv
../.venv/Scripts/Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000

# Frontend (otra terminal)
cd frontend
npm install
npm run dev
```

O usar el script combinado: `powershell -ExecutionPolicy Bypass -File scripts/dev.ps1`.

Guía paso a paso completa, incluyendo creación del usuario admin, en [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).

## Variables de entorno

Ver tabla completa por variable en [docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md). Plantilla en [`.env.example`](.env.example) (raíz, backend) y [`frontend/.env.example`](frontend/.env.example) (frontend).

## Pruebas

```bash
# Backend
cd backend
./run_tests.sh          # o run_tests.bat en Windows
./run_tests.sh coverage # con reporte HTML de cobertura

# Frontend (E2E, Playwright)
cd frontend
npx playwright test
```

## Documentación

Índice completo en [docs/README.md](docs/README.md). Documentos clave:

- [Auditoría del repositorio](docs/REPOSITORY_AUDIT.md)
- [Arquitectura](docs/ARCHITECTURE.md)
- [Guía de inicio rápido](docs/GETTING_STARTED.md)
- [Seguridad](docs/SECURITY.md)

## Contribución

Ramas de feature (`feat/mod-XX-*`), PR hacia `main`. Convenciones de commit: `feat|fix|refactor|docs|test|chore|perf|ci: descripción`.

## Seguridad

Ver [docs/SECURITY.md](docs/SECURITY.md) para autenticación, autorización, manejo de secretos y riesgos conocidos. No reportar vulnerabilidades en issues públicos.

## Limitaciones conocidas

- Sin CI para frontend, mobile ni `ml/` (solo backend).
- Protección de rutas del dashboard únicamente del lado cliente.
- El modelo propio de detección (`ml/`) aún no reemplaza al servicio externo (Roboflow) en producción.

Detalle completo en [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md#limitaciones-conocidas).
