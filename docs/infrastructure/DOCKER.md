# Docker y Docker Compose

[← Volver al índice](../README.md)

## Servicios (desarrollo — `docker-compose.yml`)

| Servicio | Imagen / build | Puerto interno | Puerto expuesto | Depende de | Volúmenes | Healthcheck |
|---|---|---|---|---|---|---|
| `postgres` | `postgis/postgis:16-3.4` | 5432 | 5432 | — | `postgres_data` | `pg_isready` |
| `redis` | `redis:7-alpine` | 6379 | 6379 | — | `redis_data` | `redis-cli ping` |
| `minio` | `minio/minio:latest` | 9000 (API), 9001 (consola) | 9000, 9001 | — | `minio_data` | `curl /minio/health/live` |
| `minio-init` | `minio/mc:latest` | — | — | `minio` (healthy) | — | (job de un solo uso, crea buckets `sirccd-images`/`sirccd-models`) |
| `backend` | build `./backend` | 8000 | 8000 | `postgres`, `redis`, `minio` (healthy) | `backend_storage`, `backend_logs`, `torch_cache`, `hf_cache` | — |
| `frontend` | build `./frontend` | 3000 | 3000 | `backend` | — | — |

Variables importantes ya embebidas con defaults de desarrollo en el propio `docker-compose.yml` (usuario/clave de Postgres, MinIO, `SECRET_KEY` de ejemplo) — no requiere `.env` completo para levantar el stack local.

## Servicios (producción — `docker-compose.prod.yml`)

Diferencias clave respecto a desarrollo:

- Se añade el servicio **`nginx`** (`nginx:1.27-alpine`) como terminador TLS, expone `80`, `443` y `9443` (consola MinIO). Monta `infra/nginx/nginx.conf` y los certificados.
- `postgres`, `redis` y `minio` **no exponen puertos al host** — solo son alcanzables dentro de la red Docker interna (`sirccd-network`). Todo el tráfico externo pasa por `nginx`.
- `redis` requiere contraseña (`--requirepass ${REDIS_PASSWORD}`).
- `minio` habilita cifrado automático (`MINIO_KMS_AUTO_ENCRYPTION: "on"`); `minio-init` además activa SSE-S3 explícitamente en ambos buckets.
- `backend` y `frontend` **no exponen puertos al host** — solo `nginx` los alcanza vía la red interna.
- Todos los secretos se inyectan por variable de entorno (`${VAR}`), ninguno queda hardcodeado en el archivo.
- `ALLOWED_ORIGINS` se limita a `https://${DOMAIN}` y `https://www.${DOMAIN}`.

Los volúmenes nombrados son los mismos en ambos archivos (`postgres_data`, `redis_data`, `minio_data`, `backend_storage`, `backend_logs`, `torch_cache`, `hf_cache`).

## Dockerfiles

### Backend (`backend/Dockerfile`)

- Base: `python:3.11-slim`.
- Dependencias de sistema: `gcc`, `libpq-dev` (Postgres), `libgeos-dev`/`libspatialindex-dev` (GeoAlchemy2/Shapely), `curl`.
- `torch`/`torchvision` se instalan explícitamente desde el índice CPU-only de PyTorch (`https://download.pytorch.org/whl/cpu`) **antes** del resto de `requirements.txt`, para evitar arrastrar ~2.5 GB de dependencias CUDA innecesarias en el despliegue.
- Comando de arranque (definido en Railway/compose, no en el `Dockerfile` mismo): `alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips="*"` — las migraciones corren automáticamente en cada arranque.

### Frontend (`frontend/Dockerfile`)

- Base: `node:20-alpine`.
- `npm ci` para instalación reproducible.
- `NEXT_PUBLIC_API_URL` se recibe como **build arg** — queda inlineado en el bundle de JavaScript en tiempo de build, no es reconfigurable cambiando solo la variable de entorno del contenedor en runtime.
- `npm run build` seguido de `npm start -- --port ${PORT}`.

## Nginx (`infra/nginx/nginx.conf`)

- Redirección HTTP → HTTPS (puerto 80 → 301 a `https://`).
- Servidor HTTPS principal (443): TLS 1.2/1.3 únicamente, cifrados modernos (ECDHE), HSTS a 1 año con `includeSubDomains`, cabeceras `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`.
- `client_max_body_size 11M` — límite alineado con el tamaño máximo de imagen del backend.
- Rutas: `/api/` → proxy a `backend:8000`; todo lo demás → proxy a `frontend:3000` (con soporte de upgrade para WebSocket/HMR).
- Servidor separado en el puerto **9443** exclusivamente para la consola de administración de MinIO (`minio:9001`), aislado del tráfico público de la aplicación.
- Certificados esperados en `/etc/nginx/certs/` (montados como volumen); generación de certificados de desarrollo vía `infra/nginx/generate-dev-certs.sh`.

## MinIO standalone (`infra/compose/docker-compose.minio.yml`)

Archivo alternativo para levantar solo MinIO en desarrollo, sin el resto del stack — útil cuando se trabaja únicamente en `ml/` o en scripts que solo necesitan almacenamiento de objetos.
