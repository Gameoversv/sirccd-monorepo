# Guía de inicio rápido

[← Volver al índice](README.md)

## Requisitos previos

| Herramienta | Uso |
|---|---|
| Docker + Docker Compose | Levantar Postgres/PostGIS, Redis, MinIO (y opcionalmente backend/frontend completos) |
| Python 3.11 | Ejecutar el backend fuera de Docker |
| Node.js 20+ y npm | Ejecutar el frontend fuera de Docker |
| Flutter SDK | Compilar/ejecutar la app móvil (`mobile/`) |
| PowerShell | Ejecutar `scripts/dev.ps1` (entorno Windows) |

## Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd sirccd-monorepo
```

## Variables de entorno

Copiar el archivo de ejemplo y completar los valores necesarios (ver detalle de cada variable en [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)):

```bash
cp .env.example .env
```

Para desarrollo local, `docker-compose.yml` ya trae valores por defecto para Postgres/Redis/MinIO — no es obligatorio completar `.env` para levantar el stack local, solo es necesario si se quiere usar Roboflow real (`ROBOFLOW_API_KEY`).

El frontend tiene su propio archivo de ejemplo:

```bash
cp frontend/.env.example frontend/.env.local
```

## Opción A: levantar todo con Docker Compose

```bash
docker compose up --build
```

Esto levanta: `postgres` (puerto 5432), `redis` (6379), `minio` (9000 API / 9001 consola), `minio-init` (crea buckets), `backend` (8000) y `frontend` (3000). El backend corre migraciones automáticamente en su `Dockerfile` (`alembic upgrade head`) antes de iniciar `uvicorn`.

Servicios expuestos:

| Servicio | URL local |
|---|---|
| Backend API (docs Swagger) | http://localhost:8000/api/v1/docs |
| Frontend (dashboard/portal) | http://localhost:3000 |
| Consola MinIO | http://localhost:9001 |

## Opción B: ejecución manual (sin Docker para backend/frontend)

Requiere Postgres/Redis/MinIO disponibles (pueden seguir corriendo vía Docker: `docker compose up postgres redis minio minio-init`).

### Backend

```powershell
cd backend
python -m venv ../.venv
../.venv/Scripts/Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Script combinado (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

Este script libera los puertos 8000/3000 si están ocupados, verifica que exista `.venv` y `node_modules`, y levanta backend + frontend en paralelo con logs en `backend/dev.log` / `frontend/dev.log`. Para detener: `scripts/dev-stop.ps1`.

> `dev.ps1` busca el intérprete en `.venv/Scripts/python.exe` **en la raíz del repositorio**, no en `backend/.venv/`. Si creaste el entorno virtual dentro de `backend/`, el script aborta con `No se encontro .venv`. Crea el entorno en la raíz (como en el bloque de arriba, `python -m venv ../.venv`) o ajusta la ruta en el script.

## Base de datos y migraciones

Las migraciones viven en `backend/alembic/versions/` (9 migraciones al momento de esta guía). Para aplicarlas manualmente:

```bash
cd backend
alembic upgrade head
```

Para crear una nueva migración tras cambiar un modelo:

```bash
alembic revision --autogenerate -m "descripción del cambio"
```

## Crear el usuario administrador inicial

```bash
cd backend
ADMIN_USERNAME=admin ADMIN_EMAIL=admin@sirccd.com ADMIN_PASSWORD='<contraseña-segura>' \
    python -m scripts.seed_admin
```

El script es idempotente (no sobrescribe un admin ya existente) y no acepta una contraseña por defecto — falla si `ADMIN_PASSWORD` no está definida. En Railway debe ejecutarse dentro del contenedor (`railway ssh`), no con `railway run` (el `POSTGRES_HOST` interno solo resuelve dentro de la red privada de Railway).

## Ejecutar la app móvil

```bash
cd mobile
flutter pub get
flutter run
```

Requiere apuntar `lib/core/network/backend_url.dart` (o la configuración equivalente) al backend accesible desde el dispositivo/emulador — en un emulador Android, `localhost` del host no es directamente accesible, usar `10.0.2.2` o la IP de la máquina.

## Verificación del funcionamiento

1. Backend: `GET http://localhost:8000/api/v1/health` debe responder `200`.
2. Frontend: http://localhost:3000 debe cargar la landing y redirigir a `/login`.
3. Login con el usuario admin creado en el paso anterior.
4. Documentación interactiva de la API: http://localhost:8000/api/v1/docs (Swagger UI de FastAPI).

## Problemas frecuentes

| Problema | Causa probable | Solución |
|---|---|---|
| Backend no arranca, error de conexión a Postgres | Postgres no está healthy todavía | Esperar al healthcheck de `docker compose` o revisar `docker compose logs postgres` |
| Worker de RQ no procesa nada en Windows | RQ usa `fork`, no soportado en Windows | Usar `worker_windows.py` en vez de `worker.py` en desarrollo local |
| Imágenes no se ven en el frontend | MinIO no configurado o buckets no creados | Confirmar que el contenedor `minio-init` corrió sin error y creó `sirccd-images`/`sirccd-models` |
| Reportes se quedan sin clasificar | `ROBOFLOW_API_KEY` vacía | El backend usa un detector simulado (mock) si falta la key — definirla en `.env` para inferencia real |
| Puerto 8000 o 3000 ocupado al usar `dev.ps1` | Proceso previo no se cerró bien | El script ya intenta liberar esos puertos automáticamente; si falla, cerrar manualmente el proceso con `Stop-Process` |
| `dev.ps1` termina con `No se encontro .venv` | El entorno virtual está en `backend/.venv/`, no en la raíz | Crear el entorno en la raíz del repositorio (`python -m venv .venv`) o editar la ruta en `scripts/dev.ps1` |
| `UnicodeEncodeError: 'charmap' codec can't encode character '⚠'` al arrancar el backend en Windows | `ultralytics` no instalado + consola en `cp1252`: el mensaje de aviso de `services/anonymizer.py` no se puede imprimir y aborta el import | `$env:PYTHONIOENCODING = "utf-8"` antes de arrancar, o instalar `ultralytics` |
