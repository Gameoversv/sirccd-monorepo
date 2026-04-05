# Modulo Infra (Infraestructura)

## 1. Proposito del modulo

El modulo Infra centraliza toda la infraestructura del proyecto SIRCCD:

1. **Orquestacion de servicios**: definiciones Docker Compose para levantar el stack completo.
2. **Contenedorizacion**: Dockerfiles para cada modulo productivo.
3. **CI/CD**: pipelines de integracion y despliegue continuo (planificado).
4. **Gestion de ambientes**: configuracion diferenciada por entorno (dev, staging, produccion).

## 2. Stack tecnologico

| Componente | Tecnologia | Proposito |
|-----------|------------|-----------|
| Contenedores | Docker | Empaquetado de servicios |
| Orquestacion | Docker Compose | Levantamiento coordinado de servicios |
| BD | PostgreSQL 16 + PostGIS | Persistencia relacional + geoespacial |
| Cache/Queue | Redis 7 | Cola de tareas RQ + cache |
| Object Storage | MinIO | Almacenamiento S3-compatible para imagenes |
| CI/CD | GitHub Actions (planificado) | Pipelines de build, test y deploy |
| Scripts | PowerShell | Automatizacion de desarrollo local (Windows) |

## 3. Estado actual

### 3.1 Estructura del modulo

```
infra/
├── ci-cd/       # Destino de pipelines, checks y jobs (placeholder, .gitkeep)
├── compose/     # Destino de compose por ambiente (placeholder, .gitkeep)
└── docker/      # Destino de Dockerfiles reutilizables (placeholder, .gitkeep)
```

Las carpetas contienen `.gitkeep` como placeholders. La estructura esta preparada para recibir definiciones productivas.

### 3.2 Archivos de infraestructura actuales (fuera de infra/)

Actualmente los archivos de infraestructura estan distribuidos en la raiz y modulos:

| Archivo | Ubicacion | Descripcion |
|---------|-----------|-------------|
| `docker-compose.yml` | Raiz | Compose principal: PostgreSQL, Redis, MinIO, backend, worker, frontend |
| `docker-compose.minio.yml` | Raiz | Compose standalone para MinIO |
| `backend/docker-compose.db.yml` | Backend | Compose con solo servicios de datos (PostgreSQL, Redis, MinIO) |
| `backend/Dockerfile` | Backend | Imagen Docker del backend FastAPI |
| `frontend/Dockerfile` | Frontend | Imagen Docker del frontend Next.js |
| `dev.ps1` | Raiz | Script PowerShell de arranque local |
| `dev-stop.ps1` | Raiz | Script PowerShell de detencion local |
| `.github/` | Raiz | GitHub Actions y workflows |

## 4. Docker Compose (detalle)

### 4.1 Compose principal (`docker-compose.yml`)

Orquesta todos los servicios necesarios para ejecutar el sistema completo:

| Servicio | Imagen | Puerto | Descripcion |
|----------|--------|--------|-------------|
| `postgres` | postgres:16 + PostGIS | 5432 | Base de datos principal con extension geoespacial |
| `redis` | redis:7-alpine | 6379 | Cola de tareas RQ y cache |
| `minio` | minio/minio:latest | 9000 (API), 9001 (Console) | Object storage para imagenes de reportes |
| `backend` | Build desde `backend/Dockerfile` | 8000 | API REST FastAPI |
| `worker` | Build desde `backend/Dockerfile` | - | Worker RQ para procesamiento asincrono |
| `frontend` | Build desde `frontend/Dockerfile` | 3000 | Dashboard web Next.js |

#### Dependencias entre servicios

```
frontend → backend → postgres, redis, minio
worker → postgres, redis, minio
```

#### Volumenes persistentes

- `postgres_data`: datos de PostgreSQL
- `redis_data`: datos de Redis
- `minio_data`: archivos almacenados en MinIO

### 4.2 Compose MinIO standalone (`docker-compose.minio.yml`)

Para desarrollo que solo necesita almacenamiento de objetos:

| Servicio | Puerto | Credenciales default |
|----------|--------|---------------------|
| MinIO API | 9000 | minioadmin / minioadmin |
| MinIO Console | 9001 | minioadmin / minioadmin |

### 4.3 Compose de BD (`backend/docker-compose.db.yml`)

Para desarrollo del backend con solo servicios de datos:

| Servicio | Puerto |
|----------|--------|
| PostgreSQL + PostGIS | 5432 |
| Redis | 6379 |
| MinIO | 9000 / 9001 |

## 5. Dockerfiles

### 5.1 Backend (`backend/Dockerfile`)

```
Base: python:3.11-slim
Dependencias: requirements.txt
Entry point: uvicorn main:app
Expose: 8000
```

- Instala dependencias del sistema (libpq, etc.)
- Copia requirements.txt e instala con pip
- Copia codigo fuente
- Ejecuta uvicorn en modo produccion

### 5.2 Frontend (`frontend/Dockerfile`)

```
Base: node:18-alpine
Build: npm run build (Next.js)
Entry point: npm start
Expose: 3000
```

- Multi-stage build: install → build → run
- Stage 1: instala dependencias
- Stage 2: ejecuta build de Next.js
- Stage 3: imagen minima con solo artifacts de build

## 6. Scripts de desarrollo local

### 6.1 `dev.ps1` - Arranque local

Script PowerShell que levanta el entorno de desarrollo completo:

```powershell
powershell -ExecutionPolicy Bypass -File dev.ps1
```

Acciones:
1. Levanta servicios de infraestructura (PostgreSQL, Redis, MinIO) via Docker Compose
2. Verifica que los servicios esten healthy
3. Muestra URLs de acceso

### 6.2 `dev-stop.ps1` - Detencion local

```powershell
powershell -ExecutionPolicy Bypass -File dev-stop.ps1
```

Acciones:
1. Detiene todos los contenedores del compose
2. Opcionalmente limpia volumenes

## 7. Puertos y URLs

| Servicio | Puerto | URL local |
|----------|--------|-----------|
| Backend (FastAPI) | 8000 | http://localhost:8000 |
| Swagger UI | 8000 | http://localhost:8000/docs |
| ReDoc | 8000 | http://localhost:8000/redoc |
| Frontend (Next.js) | 3000 | http://localhost:3000 |
| PostgreSQL | 5432 | postgresql://localhost:5432/sirccd |
| Redis | 6379 | redis://localhost:6379 |
| MinIO API | 9000 | http://localhost:9000 |
| MinIO Console | 9001 | http://localhost:9001 |

## 8. Ejecucion

### 8.1 Stack completo con Docker Compose

```bash
# Levantar todo
docker compose up -d

# Ver logs
docker compose logs -f backend
docker compose logs -f worker

# Detener todo
docker compose down

# Detener y limpiar volumenes
docker compose down -v
```

### 8.2 Solo infraestructura (para desarrollo local)

```bash
# Solo BD + Redis + MinIO
docker compose -f backend/docker-compose.db.yml up -d

# Backend manual
cd backend
uvicorn main:app --reload --port 8000

# Frontend manual
cd frontend
npm run dev
```

### 8.3 Solo MinIO

```bash
docker compose -f docker-compose.minio.yml up -d
```

## 9. Plan de consolidacion

### 9.1 Objetivo

Migrar todos los archivos de infraestructura dispersos al modulo `infra/` como fuente unica de verdad.

### 9.2 Pasos planificados

1. **Compose**: mover archivos compose a `infra/compose/` con convencion de nombres:
   - `infra/compose/docker-compose.dev.yml`
   - `infra/compose/docker-compose.staging.yml`
   - `infra/compose/docker-compose.prod.yml`
   - `infra/compose/docker-compose.db-only.yml`
   - `infra/compose/docker-compose.minio-only.yml`

2. **Dockerfiles**: centralizar en `infra/docker/`:
   - `infra/docker/backend.Dockerfile`
   - `infra/docker/frontend.Dockerfile`
   - `infra/docker/worker.Dockerfile`

3. **CI/CD**: publicar pipelines en `infra/ci-cd/`:
   - `infra/ci-cd/lint-and-typecheck.yml`
   - `infra/ci-cd/test.yml`
   - `infra/ci-cd/build-images.yml`
   - `infra/ci-cd/deploy-staging.yml`
   - `infra/ci-cd/deploy-production.yml`

4. **Secretos y variables**: documentar gestion de secretos por ambiente.

5. **Scripts**: mover `dev.ps1` y `dev-stop.ps1` a `infra/scripts/`.

### 9.3 Resultado esperado

`infra/` sera la referencia unica para toda la operacion y despliegue, eliminando dependencia de archivos sueltos en la raiz.

## 10. Ambientes

| Ambiente | Estado | Descripcion |
|----------|--------|-------------|
| **Local (dev)** | Operativo | Docker Compose + scripts PowerShell |
| **Staging** | Pendiente | Pre-produccion para validacion |
| **Produccion** | Pendiente | Ambiente productivo final |

### 10.1 Diferencias entre ambientes (planificado)

| Aspecto | Dev | Staging | Produccion |
|---------|-----|---------|------------|
| BD | PostgreSQL local (Docker) | PostgreSQL managed | PostgreSQL managed (HA) |
| Redis | Redis local (Docker) | Redis managed | Redis managed (cluster) |
| MinIO | MinIO local (Docker) | MinIO o S3 | S3 |
| SSL | No | Si | Si |
| Replicas | 1 | 1 | 2+ |
| Logs | Console | Structured (JSON) | Structured + aggregation |
| Secrets | .env file | Vault / env vars | Vault / env vars |

## 11. Integraciones

| Sistema | Mecanismo | Datos |
|---------|-----------|-------|
| Backend | Dockerfile + Compose | Contenedor FastAPI + Worker |
| Frontend | Dockerfile + Compose | Contenedor Next.js |
| PostgreSQL | Compose service | Persistencia de datos |
| Redis | Compose service | Cola de tareas |
| MinIO | Compose service | Object storage |
| GitHub | Actions (planificado) | CI/CD pipelines |
