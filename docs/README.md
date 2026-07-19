# Documentación — SIRCCD Monorepo

Índice de toda la documentación técnica del proyecto. Generada de forma incremental (ver [REPOSITORY_AUDIT.md](REPOSITORY_AUDIT.md) para el estado de cada fase).

## General

- [Auditoría del repositorio](REPOSITORY_AUDIT.md) — inventario completo, riesgos y acciones recomendadas (Fase 1).
- [Visión general del proyecto](PROJECT_OVERVIEW.md) — propósito, usuarios, funcionalidades, estado actual.
- [Arquitectura](ARCHITECTURE.md) — componentes, comunicación entre ellos, decisiones y deuda técnica.
- [Guía de inicio rápido](GETTING_STARTED.md) — cómo levantar el proyecto desde cero.
- [Configuración](CONFIGURATION.md) — qué hace cada archivo de configuración del repositorio.
- [Variables de entorno](ENVIRONMENT_VARIABLES.md) — tabla completa por componente.
- [Seguridad](SECURITY.md) — autenticación, autorización, manejo de secretos, riesgos.
- [Decisiones arquitectónicas (ADR)](decisions/README.md)

## Pendiente (próximas fases)

Estos documentos se generarán en fases posteriores, una vez validado el contenido actual con el equipo:

- `DEVELOPMENT_GUIDE.md`, `TESTING.md`, `DEPLOYMENT.md`, `TROUBLESHOOTING.md`, `CHANGELOG_GUIDE.md`, `CONTRIBUTING.md`
- `backend/` — documentación detallada de API, servicios, modelos de datos
- `frontend/` — documentación de componentes, rutas, integración con la API
- `database/` — esquema, relaciones, migraciones
- `infrastructure/` — Docker, CI/CD, monitoreo
- `mobile/` — arquitectura, navegación, permisos
- `ml/` — datasets, entrenamiento, evaluación, versionado de modelos

No se crean carpetas vacías para estas áreas hasta tener contenido real que documentar — ver la nota sobre alcance en [REPOSITORY_AUDIT.md](REPOSITORY_AUDIT.md).
