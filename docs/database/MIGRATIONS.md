# Migraciones

[← Volver al índice](../README.md)

Gestionadas con Alembic (`backend/alembic/`, configuración en `backend/alembic.ini`).

## Historial (9 migraciones)

| Archivo | revision | down_revision | Propósito (por nombre) |
|---|---|---|---|
| `001_initial_schema_with_postgis.py` | `001` | `None` | Esquema inicial: `users`, `reports`, `incidents`, `pois`, `metrics`, extensión PostGIS |
| `001_sla_fields.py` | `001_sla_fields` | `005` | Campos de SLA — **nota**: pese al prefijo `001_` en el nombre de archivo, su `down_revision` real es `005`; no es la segunda migración en aplicarse, es la sexta. El prefijo es solo una coincidencia de nombre, no un conflicto de grafo (confirmado leyendo `revision`/`down_revision` de ambos archivos) |
| `002_add_priority_settings_table.py` | — | — | Tabla `priority_settings` |
| `003_add_clustering_params.py` | — | — | Parámetros de clustering (DBSCAN) en `priority_settings` |
| `004_add_zones_table.py` | — | — | Tabla `zones` |
| `005_add_incident_audit_log.py` | — | — | Tabla `incident_audit_logs` |
| `006_widen_encrypted_phone.py` | — | — | Amplía el ancho de columna de `users.phone` (cifrado ocupa más espacio que el valor plano) |
| `007_add_incident_priority_breakdown.py` | — | — | Columna `priority_breakdown` (JSON) en `incidents` |
| `008_add_report_duplicate_of.py` | — | — | Columna `duplicate_of_report_id` (autorreferencia) en `reports` |

> El orden real de aplicación se determina por la cadena `revision`/`down_revision` de Alembic, no por el nombre de archivo — usar `alembic history` para el orden verdadero si se necesita certeza absoluta.

## Comandos

```bash
cd backend
alembic upgrade head                              # aplicar todas las pendientes
alembic downgrade -1                               # revertir la última
alembic history --verbose                          # ver cadena completa de revisiones
alembic revision --autogenerate -m "descripción"    # generar una nueva a partir de cambios en models/
```

## Al crear una migración nueva

1. Modificar el modelo SQLAlchemy correspondiente en `backend/models/`.
2. `alembic revision --autogenerate -m "descripción clara"`.
3. **Revisar manualmente** el archivo generado — `autogenerate` no detecta todos los cambios (ej. cambios de tipo en columnas con PostGIS, renombrados) y puede generar operaciones incompletas o destructivas.
3. Probar con `alembic upgrade head` en una base de datos local antes de commitear.
4. Si la migración afecta datos existentes en producción (no solo el esquema), evaluar si se necesita también un script de backfill en `backend/scripts/maintenance/` — ver ejemplos de migraciones anteriores que sí lo requirieron (007, 008).

## Migraciones en CI/despliegue

- **CI** (`backend-tests.yml`): corre `alembic upgrade head` contra un Postgres efímero antes de las pruebas.
- **Producción**: el `Dockerfile` del backend ejecuta `alembic upgrade head` automáticamente en cada arranque del contenedor, antes de iniciar `uvicorn`.
