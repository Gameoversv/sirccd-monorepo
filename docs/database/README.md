# Base de datos

[← Volver al índice](../README.md)

## Motor

PostgreSQL 16 con extensión PostGIS 3.4 (imagen `postgis/postgis:16-3.4` en desarrollo, `postgis/postgis:15-3.3` en CI). Los campos geográficos (`location`, `boundary`) usan el tipo `Geography` de GeoAlchemy2 con SRID 4326 (WGS 84, el sistema estándar de coordenadas GPS).

## Configuración de conexión

Vía variables de entorno leídas por `backend/core/config.py`: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`. Ver detalle completo en [../ENVIRONMENT_VARIABLES.md](../ENVIRONMENT_VARIABLES.md). Motor y sesión de SQLAlchemy en `backend/db/session.py` / `backend/db/base.py`.

## Documentos

- [Esquema](SCHEMA.md) — tablas, campos, relaciones, diagrama ER.
- [Migraciones](MIGRATIONS.md) — Alembic, historial, cómo crear una nueva.

## Datos sensibles

El campo `users.phone` está cifrado en reposo (Fernet/AES-128-CBC, ver `backend/core/field_encryption.py`) — ver [../SECURITY.md](../SECURITY.md) para el detalle de esta protección y su comportamiento de fallback si falta la clave.

## Respaldo y recuperación

No se encontró en el repositorio un script o job de backup automatizado de PostgreSQL. Si Railway gestiona backups automáticos de la base de datos administrada, esa configuración vive en el panel de Railway, no en este repositorio — pendiente de documentar una vez confirmado con el equipo (ver pendiente en [../REPOSITORY_AUDIT.md](../REPOSITORY_AUDIT.md)).
