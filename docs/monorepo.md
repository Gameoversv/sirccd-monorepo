# Monorepo SIRCCD

## Proposito general

SIRCCD integra, en un solo repositorio, todo el sistema de reporte y gestion de danos viales:

- captura ciudadana,
- procesamiento con ML,
- deduplicacion y priorizacion,
- operacion municipal desde panel web,
- base para infraestructura y app movil.

## Arquitectura por modulos

### Modulos de producto

1. `backend/`: API, reglas de negocio, procesamiento asincrono y persistencia.
2. `frontend/`: dashboard web de operacion.
3. `ml/`: entrenamiento, datasets y artefactos.

### Modulos de plataforma

1. `infra/`: estructura para CI/CD, compose y docker reutilizable.
2. `mobile/`: espacio de app movil Flutter (aun scaffold).

### Modulo de documentacion

1. `docs/`: fuente unica de documentacion por modulo.

## Flujo funcional transversal

1. Ciudadano envia reporte (imagen + ubicacion + descripcion).
2. Backend crea reporte y encola procesamiento.
3. ML/servicios estiman tipo y severidad, y aplican anonimizado.
4. Backend calcula deduplicacion multimodelo.
5. Backend actualiza prioridad del incidente.
6. Frontend consume datos para operacion y seguimiento.

## Mapa de raiz del repositorio

- `backend/`: servicio principal de negocio.
- `frontend/`: cliente web.
- `ml/`: pipelines y activos de modelos.
- `infra/`: definiciones/plans de despliegue.
- `mobile/`: codigo movil (pendiente).
- `docs/`: documentacion central.
- `dev.ps1`: arranque local integral.
- `dev-stop.ps1`: detencion local integral.
- `docker-compose.yml`: compose principal.
- `docker-compose.minio.yml`: compose para almacenamiento MinIO.

## Decisiones de organizacion ya aplicadas

1. Se elimino documentacion historica fragmentada en `docs/`.
2. Se centralizo documentacion por modulo en `docs/*.md`.
3. Se vacio `backend/docs` para evitar duplicidad.
4. En backend se separo codigo fuente de scripts/manual tests:
	- `backend/tests/manual/`
	- `backend/tests/manual/fixtures/`
	- `backend/scripts/verification/`
	- `backend/scripts/maintenance/`
5. Se removieron artefactos generados (logs/caches/coverage) de raices de modulo.

## Convencion de ubicacion de archivos

1. Codigo de producto: dentro del modulo correspondiente.
2. Pruebas automaticas: `tests/` del modulo.
3. Pruebas manuales/smoke: `tests/manual/`.
4. Fixtures: `tests/manual/fixtures/` o `tests/fixtures/`.
5. Scripts operativos: `scripts/` del modulo.
6. Documentacion: `docs/` central.

## Comandos operativos rapidos

### Levantar entorno local

```powershell
powershell -ExecutionPolicy Bypass -File dev.ps1
```

### Detener entorno local

```powershell
powershell -ExecutionPolicy Bypass -File dev-stop.ps1
```

### Ver cambios locales

```powershell
git status --short
```
