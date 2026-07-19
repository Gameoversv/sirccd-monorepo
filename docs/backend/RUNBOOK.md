# Runbook — Backend

[← Volver al índice](../README.md)

Operaciones comunes de desarrollo y mantenimiento del backend. Para el flujo completo de instalación desde cero, ver [../GETTING_STARTED.md](../GETTING_STARTED.md).

## Arrancar el backend localmente

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

En producción (Railway/Docker), el `Dockerfile` ejecuta `alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips="*"` en cada arranque.

## Migraciones

```bash
cd backend
alembic upgrade head                                  # aplicar todas las pendientes
alembic revision --autogenerate -m "descripción"       # crear una nueva a partir de cambios en models/
alembic downgrade -1                                   # revertir la última (usar con cuidado)
alembic history                                        # ver el historial de migraciones
```

9 migraciones existentes en `alembic/versions/` al momento de esta documentación. Nota: dos archivos comparten el prefijo `001_` en el nombre (`001_initial_schema_with_postgis.py` y `001_sla_fields.py`) — **no es un conflicto real**, sus `revision`/`down_revision` internos son distintos (`001` y `001_sla_fields`, con `down_revision="005"`), solo coincide el nombre de archivo.

## Crear el usuario administrador inicial

```bash
cd backend
ADMIN_USERNAME=admin ADMIN_EMAIL=admin@sirccd.com ADMIN_PASSWORD='<contraseña-segura>' \
    python -m scripts.seed_admin
```

Idempotente — no sobrescribe un admin ya existente, solo corrige rol/estado si quedaron mal. Falla explícitamente si `ADMIN_PASSWORD` no está definida.

**En Railway**, ejecutar dentro del contenedor (`railway ssh --service backend -- env ADMIN_USERNAME=... ADMIN_PASSWORD='...' python -m scripts.seed_admin`). `railway run` **no funciona** para esto: inyecta las variables pero corre el proceso en la máquina local, y `POSTGRES_HOST` interno (`postgres.railway.internal`) solo resuelve dentro de la red privada de Railway.

## Levantar el worker de tareas

```bash
cd backend
python worker.py           # Linux/Railway (usa fork)
python worker_windows.py   # Windows (fork no soportado por RQ en Windows)
```

## Reconstruir el índice de deduplicación (FAISS)

Vía API (requiere rol supervisor): `POST /api/v1/deduplication/index/rebuild` (form `batch_size`, default 100). Reconstruye el índice desde todos los reportes aprobados.

## Chequear SLA manualmente

Vía API (requiere rol admin): `POST /api/v1/incidents/sla/check` — encola el job `check_sla_alerts` sin esperar al scheduler externo.

## Diagnóstico rápido

```bash
curl http://localhost:8000/api/v1/health          # estado general
curl http://localhost:8000/api/v1/health/ready     # BD + Redis
curl http://localhost:8000/api/v1/ping             # liveness simple
curl http://localhost:8000/api/v1/metrics          # métricas Prometheus
```

## Scripts de mantenimiento

`backend/scripts/maintenance/` contiene scripts de mantenimiento puntual (ej. `create_incidents_from_reports.py`). Los 3 backfills ligados a las migraciones 007/008 (`backfill_priority_breakdown.py`, `backfill_report_duplicate_of.py`, `backfill_merged_report_links.py`) ya cumplieron su propósito (confirmado sin candidatos pendientes en producción) y fueron eliminados. `backend/scripts/verification/` contiene scripts de verificación manual por ticket (`verify_b02.py`, etc.). Ninguno corre automáticamente — son de ejecución manual, puntual, documentados en sus propios docstrings.
