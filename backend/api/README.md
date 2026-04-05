# API Backend SIRCCD

## Proposito

Esta carpeta contiene la capa HTTP del backend:

1. dependencias FastAPI,
2. rutas por dominio,
3. especificacion OpenAPI.

## Estructura

- `deps.py`: dependencias comunes (usuario actual, roles, DB session).
- `openapi.yaml`: contrato OpenAPI de la API.
- `routes/auth.py`: autenticacion y sesion.
- `routes/reports.py`: reportes.
- `routes/incidents.py`: incidentes.
- `routes/deduplication.py`: deduplicacion.
- `routes/export.py`: exportaciones.
- `routes/health.py`: health/readiness.
- `routes/pois.py`: puntos de interes.
- `routes/users.py`: administracion de usuarios.

## Convencion de rutas

Cada archivo de `routes/` agrupa endpoints de un dominio funcional.

## Seguridad

- autenticacion JWT bearer.
- rutas protegidas por dependencias de rol en `deps.py`.

## Fuente de verdad de documentacion API

1. Swagger runtime: `http://localhost:8000/docs`
2. OpenAPI estatico: `api/openapi.yaml`
3. Documentacion de modulo: `../README.md` y `../../docs/backend.md`
