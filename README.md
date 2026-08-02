# SIRCCD Monorepo

[![Backend Tests](https://github.com/Gameoversv/sirccd-monorepo/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/Gameoversv/sirccd-monorepo/actions/workflows/backend-tests.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black)](https://nextjs.org/)
[![Flutter](https://img.shields.io/badge/flutter-mobile-02569B)](https://flutter.dev/)

Sistema Inteligente Urbano para Reporte y Priorización de Daños Viales.

Los ciudadanos reportan baches y grietas con una foto georreferenciada; el sistema detecta el tipo de daño, descarta duplicados, calcula la prioridad según la cercanía a puntos sensibles (hospitales, escuelas) y entrega a los equipos operativos una cola de incidentes con seguimiento de SLA.

## Estado

Desarrollo activo. Backend y frontend desplegados en Railway. Ver [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) para el estado detallado y las limitaciones conocidas.

## Funcionalidades principales

- Reportes ciudadanos con foto georreferenciada (web y móvil).
- Detección automática del tipo de daño (Roboflow).
- Deduplicación de reportes por similitud visual, geográfica y temporal.
- Priorización según proximidad a puntos de interés sensibles (hospitales, escuelas, etc.).
- Gestión de incidentes con seguimiento de SLA y alertas.
- Anonimización automática de rostros y placas en las imágenes.
- Guía de usuario pública en `/guia`, sin necesidad de sesión.

Detalle completo en [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md). Manual para usuarios finales en [docs/MANUAL_USUARIO.md](docs/MANUAL_USUARIO.md).

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
├── .github/          Workflows de CI (backend, E2E), plantillas de issue y PR
├── docker-compose.yml
├── docker-compose.prod.yml
├── CONTRIBUTING.md
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
npm run test:e2e        # requiere backend + frontend arriba y usuarios sembrados
```

## Documentación

Índice completo en [docs/README.md](docs/README.md). Documentos clave:

- [Guía de inicio rápido](docs/GETTING_STARTED.md)
- [Arquitectura](docs/ARCHITECTURE.md)
- [API del backend](docs/backend/API.md)
- [Esquema de base de datos](docs/database/SCHEMA.md)
- [Variables de entorno](docs/ENVIRONMENT_VARIABLES.md)
- [Seguridad](docs/SECURITY.md)
- [Manual de usuario](docs/MANUAL_USUARIO.md)
- [Auditoría del repositorio](docs/REPOSITORY_AUDIT.md)

## Contribución

Lee [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir un PR. En resumen:

- Ramas de feature: `feat/mod-XX-descripcion`, `fix/mod-XX-descripcion`. Nunca push directo a `main`.
- Commits en formato Conventional Commits: `feat|fix|refactor|docs|test|chore|perf|ci(alcance): descripción`.
- Los tests del componente tocado y el linter deben pasar antes del PR.
- Cambios de esquema requieren migración de Alembic; variables nuevas van a `.env.example` y a `docs/ENVIRONMENT_VARIABLES.md`.
- PR hacia `main`, usando la plantilla, con el CI en verde y al menos una aprobación.

## Seguridad

Ver [docs/SECURITY.md](docs/SECURITY.md) para autenticación, autorización, manejo de secretos y riesgos conocidos. No reportar vulnerabilidades en issues públicos.

## Limitaciones conocidas

- Sin CI para mobile ni `ml/` (backend y E2E del frontend sí tienen pipeline).
- El CI del frontend cubre E2E con Playwright, pero no `next lint` ni `tsc --noEmit` como pasos propios.
- Protección de rutas del dashboard únicamente del lado cliente.
- El modelo propio de detección (`ml/`) aún no reemplaza al servicio externo (Roboflow) en producción.

Detalle completo en [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md#limitaciones-conocidas).
