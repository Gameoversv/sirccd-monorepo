# Estructura del proyecto

[← Volver al índice](README.md)

Árbol final del repositorio (2026-07-19), tras el proceso de limpieza y documentación de esta sesión. Solo se listan carpetas/archivos de primer y segundo nivel relevantes — omite `node_modules/`, `.next/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `htmlcov/`, `build/` y artefactos locales equivalentes.

```text
sirccd-monorepo/
├── backend/                    API FastAPI, lógica de negocio, base de datos
│   ├── alembic/                 Migraciones (9 revisiones)
│   ├── api/                     Routers HTTP (auth, reports, incidents, pois, ...) + deps.py (RBAC)
│   ├── core/                    Config, seguridad JWT, cifrado de campos, métricas Prometheus
│   ├── db/                      Engine y sesión de SQLAlchemy
│   ├── db/seed/pois_google/     Datos semilla de POIs (movido desde ml/ en esta sesión)
│   ├── models/                  9 modelos SQLAlchemy
│   ├── schemas/                 Esquemas Pydantic de request/response
│   ├── scripts/                 Setup inicial (seed_admin.py) + verification/ (manual)
│   ├── services/                13 servicios de lógica de negocio
│   ├── tasks/                   Jobs RQ (ml_tasks.py, sla_tasks.py)
│   ├── tests/                   Suite pytest (unit/integration/contract) + manual/ (excluido de CI)
│   ├── main.py                  Entry point de la API
│   ├── worker.py                Worker RQ (Linux/Railway)
│   ├── worker_windows.py        Worker RQ (Windows, sin fork)
│   ├── start.sh / start.bat     Scripts de arranque rápido por SO
│   └── Dockerfile
│
├── frontend/                   Dashboard operativo + portal ciudadano (Next.js 14)
│   ├── src/app/                  Rutas (App Router): dashboard/*, portal, login, register, guia
│   ├── src/components/           18 componentes (mapa, tablas, modales, layout)
│   ├── src/hooks/                useAuth, useToast
│   ├── src/lib/                  exifGps.ts, geocode.ts
│   ├── src/services/              Un archivo por recurso backend, sobre api.ts (Axios)
│   ├── src/store/                 Zustand: authStore, incidentsStore, uiStore
│   ├── src/types/                 Tipos TypeScript compartidos
│   ├── src/utils/                 labels.ts, cn.ts
│   ├── src/i18n/                  Locales ES/EN
│   ├── tests/                    Playwright (portal.spec.ts)
│   └── Dockerfile
│
├── mobile/                     App ciudadana (Flutter)
│   ├── lib/core/                 DI (get_it), servicios compartidos, network
│   ├── lib/presentation/         Router (go_router), tema, widgets compartidos
│   ├── lib/features/              auth, camera, permissions, profile, reports (clean architecture)
│   └── test/                     unit/ y widget/
│
├── ml/                         Entrenamiento (offline) y anonimización
│   ├── anonymization/             Pipeline activo en producción (train.py, inference.py)
│   ├── models/baseline/           Métricas de una corrida base (sin pesos versionados)
│   ├── notebooks/                 4 notebooks activos + archive/ (v3, v4 superados)
│   ├── scripts/                   Utilidades de MinIO/entorno
│   └── docs/                      9 guías de entrenamiento existentes (Colab, optimización)
│
├── infra/                      Infraestructura
│   ├── nginx/                     Reverse proxy TLS (producción)
│   └── compose/                   MinIO standalone para desarrollo
│
├── scripts/                    Scripts de desarrollo local
│   ├── dev.ps1 / dev-stop.ps1      Levantan/detienen backend+frontend en paralelo
│   └── tests/                     Smoke tests PowerShell
│
├── docs/                       Documentación técnica (generada esta sesión)
│   ├── README.md                  Índice
│   ├── REPOSITORY_AUDIT.md        Auditoría inicial (Fase 1)
│   ├── PROJECT_OVERVIEW.md, ARCHITECTURE.md, GETTING_STARTED.md,
│   │   CONFIGURATION.md, ENVIRONMENT_VARIABLES.md, SECURITY.md   (Fase 2)
│   ├── backend/, frontend/, database/, infrastructure/, mobile/, ml/  (Fase 3)
│   ├── decisions/                 ADR-001 (arquitectura actual)
│   ├── SECURITY_AUDIT.md          Auditoría de seguridad completa
│   ├── MANUAL_USUARIO.md          Manual para usuarios finales (versión web en /guia)
│   ├── CLEANUP_REPORT.md          Reporte de esta limpieza (Fase 6)
│   └── PROJECT_STRUCTURE.md       Este archivo
│
├── docker-compose.yml           Orquestación de desarrollo
├── docker-compose.prod.yml      Orquestación de producción (TLS, secretos por env, SSE-S3)
├── .env.example                 Plantilla completa de variables (backend, raíz)
├── .github/
│   ├── workflows/                 CI: backend-tests.yml (único pipeline existente)
│   ├── ISSUE_TEMPLATE/            Plantillas de bug y propuesta de funcionalidad
│   └── PULL_REQUEST_TEMPLATE.md   Plantilla de PR con checklist
├── CONTRIBUTING.md              Guía de contribución (ramas, commits, tests, revisión)
└── README.md                    Punto de entrada del repositorio
```

## Notas sobre la estructura

- **`ml/` y `backend/` comparten dependencias de ML pesadas** (torch, transformers) pero no código: `ml/` es offline/experimental, `backend/services/anonymizer.py` es la única integración de código real entre ambos.
- **`backend/db/seed/`** es nuevo en esta sesión — antes los datos semilla de POIs vivían incorrectamente en `ml/datasets/pois_google/`.
- **`infra/ci-cd/` y `infra/docker/`** existen pero están vacías (solo `.gitkeep`) — no se documentan como componentes activos hasta tener contenido real.
- **Carpetas de módulo (`docs/backend/`, `docs/frontend/`, etc.)** solo existen para componentes reales del proyecto — no se crearon `docs/api/` ni `docs/diagrams/` como carpetas separadas porque su contenido ya vive dentro de `ARCHITECTURE.md`/`SCHEMA.md`/`API.md` sin necesidad de fragmentarlo más.
