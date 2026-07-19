# Backend

[← Volver al índice](../README.md)

## Resumen

API REST construida con FastAPI, organizada en capas: `api/` (routers HTTP), `core/` (configuración, seguridad, cifrado, métricas), `models/` (SQLAlchemy ORM), `schemas/` (Pydantic, validación de entrada/salida), `services/` (lógica de negocio), `tasks/` (jobs asíncronos vía RQ).

## Documentos

- [API](API.md) — cada endpoint: método, ruta, autenticación, parámetros, cuerpo, respuesta, errores.
- [Servicios](SERVICES.md) — responsabilidad y dependencias de cada servicio.
- [Modelos de datos](DATA_MODELS.md) — tablas, campos, relaciones, enums.
- [Tareas en segundo plano](BACKGROUND_TASKS.md) — cola RQ, jobs de ML y SLA.
- [Pruebas](TESTING.md) — cómo ejecutar y qué cubren.
- [Runbook](RUNBOOK.md) — operaciones comunes (migraciones, seed, arranque, troubleshooting).

Ver también, a nivel de todo el proyecto: [../SECURITY.md](../SECURITY.md) (autenticación/autorización), [../ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md) (todas las variables leídas por `core/config.py`).

## Puntos de entrada

| Archivo | Rol |
|---|---|
| `main.py` | App FastAPI: registra CORS, middleware de métricas Prometheus, todos los routers bajo `/api/v1`, monta `/storage` como estático. En `startup` precalienta métricas de Roboflow y precarga los modelos de embeddings (ResNet50/CLIP) en un hilo de fondo. |
| `worker.py` | Worker RQ estándar (usa `fork`, para Linux/Railway), escucha las colas `ml_inference` y `default`. |
| `worker_windows.py` | Variante para Windows (sin `fork`): intenta `work(burst=False)` y cae a un loop manual de polling si falla. |

## Capas

| Carpeta | Contenido |
|---|---|
| `api/routes/` | Un router por recurso: `auth`, `deduplication`, `reports`, `settings`, `incidents`, `pois`, `export`, `users`, `zones`, `health` |
| `api/deps.py` | Dependencias compartidas: extracción de usuario actual, RBAC (`require_role`/`require_admin`/`require_supervisor`), variantes opcionales para acceso a imágenes con URL firmada |
| `core/` | `config.py` (Settings), `database.py`, `security.py` (JWT/bcrypt), `field_encryption.py` (Fernet), `image_tokens.py` (firma de URLs de imágenes), `metrics.py` (Prometheus) |
| `models/` | 9 modelos SQLAlchemy — ver [DATA_MODELS.md](DATA_MODELS.md) |
| `schemas/` | Esquemas Pydantic de request/response, uno por recurso |
| `services/` | 12 servicios — ver [SERVICES.md](SERVICES.md) |
| `tasks/` | `ml_tasks.py`, `sla_tasks.py` — ver [BACKGROUND_TASKS.md](BACKGROUND_TASKS.md) |
| `db/` | `base.py`, `session.py` — engine y sesión de SQLAlchemy |
| `scripts/` | `seed_admin.py` (setup inicial), `maintenance/` (backfills puntuales), `verification/` (scripts de verificación manual) |

## Notas técnicas relevantes

- Deduplicación: embeddings multimodelo (ResNet50 + CLIP) fusionados con FAISS, más señal geográfica y temporal (`services/deduplication_service.py`).
- Clustering espacial de reportes duplicados vía DBSCAN (`services/spatial_clustering_service.py`).
- Las imágenes se sirven mediante un proxy propio del backend (`GET /reportes/{id}/image`, `GET /incidents/{id}/image`) con soporte de URLs firmadas de corta duración, no URLs directas y anónimas de MinIO.
- El worker de RQ corre en un contenedor/proceso separado del API — al procesar un reporte, resuelve la imagen desde `report.image_url` en vez de asumir un filesystem compartido con el proceso del API.
