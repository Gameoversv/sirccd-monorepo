# Documentación — SIRCCD Monorepo

Índice de toda la documentación técnica del proyecto. Generada de forma incremental (ver [REPOSITORY_AUDIT.md](REPOSITORY_AUDIT.md) para el estado de cada fase).

## General

- [Auditoría del repositorio](REPOSITORY_AUDIT.md) — inventario completo, riesgos y acciones recomendadas (Fase 1).
- [Visión general del proyecto](PROJECT_OVERVIEW.md) — propósito, usuarios, funcionalidades, estado actual.
- [Arquitectura](ARCHITECTURE.md) — componentes, comunicación entre ellos, decisiones y deuda técnica.
- [Guía de inicio rápido](GETTING_STARTED.md) — cómo levantar el proyecto desde cero.
- [Guía de contribución](../CONTRIBUTING.md) — ramas, commits, estándares de código, checklist de PR y proceso de revisión.
- [Manual de usuario](MANUAL_USUARIO.md) — uso del portal ciudadano y del dashboard, dirigido a usuarios finales (versión web en `/guia`).
- [Configuración](CONFIGURATION.md) — qué hace cada archivo de configuración del repositorio.
- [Variables de entorno](ENVIRONMENT_VARIABLES.md) — tabla completa por componente.
- [Seguridad](SECURITY.md) — autenticación, autorización, manejo de secretos, riesgos.
- [Auditoría de seguridad completa](SECURITY_AUDIT.md) — vulnerabilidades de dependencias, hallazgos con severidad y remediación (2026-07-19).
- [Decisiones arquitectónicas (ADR)](decisions/README.md)
- [Reporte de limpieza](CLEANUP_REPORT.md) — resumen completo de todo lo hecho en esta sesión (Fase 6).
- [Estructura del proyecto](PROJECT_STRUCTURE.md) — árbol final del repositorio.

## Backend

- [Resumen](backend/README.md)
- [API](backend/API.md) — cada endpoint: método, ruta, auth, parámetros, respuesta, errores.
- [Servicios](backend/SERVICES.md)
- [Modelos de datos](backend/DATA_MODELS.md)
- [Tareas en segundo plano](backend/BACKGROUND_TASKS.md)
- [Pruebas](backend/TESTING.md)
- [Runbook](backend/RUNBOOK.md) — operaciones comunes

## Frontend

- [Resumen](frontend/README.md)
- [Rutas](frontend/ROUTING.md)
- [Componentes](frontend/COMPONENTS.md)
- [Gestión de estado](frontend/STATE_MANAGEMENT.md)
- [Integración con la API](frontend/API_INTEGRATION.md)
- [Pruebas](frontend/TESTING.md)

## Base de datos

- [Resumen](database/README.md)
- [Esquema](database/SCHEMA.md) — tablas, relaciones, diagrama ER.
- [Migraciones](database/MIGRATIONS.md)

## Infraestructura

- [Resumen](infrastructure/README.md)
- [Docker](infrastructure/DOCKER.md)
- [CI/CD](infrastructure/CI_CD.md)

## Mobile

- [Resumen](mobile/README.md)
- [Arquitectura](mobile/ARCHITECTURE.md)

## Machine Learning

- [Resumen](ml/README.md) — referencia a la documentación de entrenamiento existente en `ml/docs/`.

## Pendiente (próximas fases)

Documentos que quedan fuera del alcance de esta fase, a validar con el equipo antes de escribirse como oficiales:

- `DEVELOPMENT_GUIDE.md`, `DEPLOYMENT.md`, `TROUBLESHOOTING.md`, `CHANGELOG_GUIDE.md`
- `api/` (colección de ejemplos de request/response, códigos de error consolidados)
- `diagrams/` adicionales más allá de los ya incluidos en ARCHITECTURE.md/SCHEMA.md
- Documentación operativa de Railway (fuera del repositorio, pendiente de confirmación con el equipo)

## Hallazgos resueltos en esta sesión

- ~~`reportsService.deleteReport`/`updateReport` apuntaban a endpoints inexistentes~~ — eran código muerto, nunca usado desde ninguna página; eliminados. Ver [frontend/API_INTEGRATION.md](frontend/API_INTEGRATION.md).
- ~~`SECRET_KEY` con valor por defecto en código~~ — confirmado que producción usa un valor real distinto del default. Ver [SECURITY.md](SECURITY.md).
- ~~`refresh_token` ausente en `LoginResponse`~~ — `POST /auth/refresh` existía pero era inalcanzable. Arreglado. Ver [backend/TESTING.md](backend/TESTING.md).
- ~~Tabla `pois` vacía en producción~~ — incidente real, diagnosticado y resuelto en vivo. Ver [CLEANUP_REPORT.md](CLEANUP_REPORT.md#incidente-de-producción-resuelto).
- Resto de hallazgos, clasificados por severidad, en [REPOSITORY_AUDIT.md](REPOSITORY_AUDIT.md).

## Pendiente real (no resuelto en esta sesión)

- Cobertura de tests del backend: **39.51%**, con 6 servicios en 0% — ver [backend/TESTING.md](backend/TESTING.md).
- `GET /pois` sin ningún test.
- Detalle completo de deuda técnica en [CLEANUP_REPORT.md](CLEANUP_REPORT.md#riesgos-y-deuda-técnica-pendiente).
