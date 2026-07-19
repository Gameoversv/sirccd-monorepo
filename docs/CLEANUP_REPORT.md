# Reporte de limpieza y documentación

[← Volver al índice](README.md)

Resumen de todo el trabajo realizado en esta sesión (2026-07-18 a 2026-07-19), organizado por fase. 14 commits en `main`, del `794bb05` (estado inicial) al `a985e8d` (estado final de esta sesión).

## Tabla de contenido

- [Resumen ejecutivo](#resumen-ejecutivo)
- [Fase 1 — Auditoría](#fase-1--auditoría)
- [Fase 2 y 3 — Documentación](#fase-2-y-3--documentación)
- [Fase 4 — Limpieza](#fase-4--limpieza)
- [Correcciones de bugs reales](#correcciones-de-bugs-reales)
- [Incidente de producción resuelto](#incidente-de-producción-resuelto)
- [Validaciones ejecutadas](#validaciones-ejecutadas)
- [Riesgos y deuda técnica pendiente](#riesgos-y-deuda-técnica-pendiente)
- [Elementos no modificados por falta de certeza](#elementos-no-modificados-por-falta-de-certeza)
- [Recomendaciones futuras](#recomendaciones-futuras)

## Resumen ejecutivo

- **35 archivos creados** (34 documentos + 2 assets de favicon), **34 eliminados**, **9 movidos/renombrados**, **18 modificados**.
- **0 cambios de comportamiento funcional no intencionales** — cada cambio de código (no documentación) está listado explícitamente en la sección de bugs abajo, con su verificación.
- **1 incidente de producción real diagnosticado y resuelto** (POIs vacíos) durante la sesión, no relacionado con la limpieza en sí.
- **2 bugs de código reales encontrados y corregidos**: `reportsService.updateReport`/`deleteReport` apuntando a endpoints inexistentes (eliminados, eran código muerto), y `refresh_token` ausente en `LoginResponse` (agregado).
- Cobertura de tests del backend medida por primera vez: **39.51%**, con 6 servicios en 0% — documentado, no resuelto (fuera de alcance de esta sesión).

## Fase 1 — Auditoría

`docs/REPOSITORY_AUDIT.md` (commit `28a26e3`): inventario completo vía 4 agentes de exploración en paralelo (backend, frontend, ml+mobile+infra, root+env-vars). Encontró:

- Un submódulo git huérfano (`sirccd-monorepo/sirccd-monorepo`) apuntando a un fork stale de 2 meses.
- `docs/` raíz desactualizada (ya reorganizada una vez antes, había vuelto a quedar obsoleta).
- Código muerto en frontend y backend.
- `.env.example` incompleto (~28 variables faltantes).
- Dataset de POIs mal ubicado dentro de `ml/`.
- 4 scripts de arranque de backend redundantes.
- `SECRET_KEY` con default hardcodeado (riesgo a validar).

## Fase 2 y 3 — Documentación

**Fase 2** (commit `14275a6`): documentación general — `README.md` (índice), `PROJECT_OVERVIEW.md`, `ARCHITECTURE.md` (con diagramas Mermaid), `GETTING_STARTED.md`, `CONFIGURATION.md`, `ENVIRONMENT_VARIABLES.md`, `SECURITY.md`, `decisions/ADR-001`. Reescribió el `README.md` raíz (tenía un typo "do#" al inicio, rutas desactualizadas, mobile descrito como "espacio reservado" cuando ya está implementado).

**Fase 3** (commit `f3bc1d3`): documentación por módulo — `backend/` (7 archivos, incluyendo tabla de 47 endpoints método-por-método), `frontend/` (6 archivos), `database/` (esquema + diagrama ER + migraciones), `infrastructure/` (Docker, CI/CD), `mobile/` (2 archivos), `ml/README.md` (referencia la documentación de entrenamiento ya existente en vez de duplicarla).

Todo el contenido se basó en lectura directa de código (rutas, modelos, migraciones, `docker-compose.yml`, `nginx.conf`, workflow de CI) — no se inventó ningún dato.

## Fase 4 — Limpieza

### Segura (commit `1880b9e`)

- 3 `.gitkeep` sobrantes en carpetas ya pobladas (`frontend/src/{components,hooks,store}`).
- `backend/tests/pytest.log` (artefacto local, nunca estuvo trackeado — corregido un error propio del audit que decía lo contrario).

### Riesgo bajo (commit `e9fa8a7`)

- `ml/datasets/pois_google/` → `backend/db/seed/pois_google/` (dato semilla de BD, no de entrenamiento ML — cero referencias de código a la ruta anterior).
- `.env.example` completado con ~28 variables verificadas línea por línea contra `backend/core/config.py`.
- `backend/start.py` y `start_server.py` eliminados (redundantes con `main.py`/`start.sh`/`start.bat`, sin referencias reales).

### Validación manual resuelta (commits `8a77242`, `d89e204`)

- `SECRET_KEY`/`FIELD_ENCRYPTION_KEY`/etc. confirmados como secretos reales en Railway, distintos de los defaults del código.
- 3 scripts de backfill (`backfill_priority_breakdown.py`, `backfill_report_duplicate_of.py`, `backfill_merged_report_links.py`) eliminados tras confirmar **0 candidatos pendientes** en la base de datos de producción real.
- Notebooks `v3`/`v4` archivados en `ml/notebooks/archive/` (confirmado `v5_H100_Optimized` como vigente); corregidas 3 docs de `ml/docs/` que referenciaban las rutas viejas (una marcaba v3 con ⭐ como recomendado).
- `frontend/docs/W-04-MAPA-IMPLEMENTACION.md` eliminado tras confirmar que describía una versión de `MapView.tsx` de marzo 2026, sin filtros/heatmap/capas POI, y referenciaba archivos ya eliminados.

## Correcciones de bugs reales

Estos son cambios de **comportamiento de código**, no solo de organización — cada uno se verificó antes y después.

| Commit | Cambio | Motivo | Verificación |
|---|---|---|---|
| `c6fcb27` | `pois_insert.sql`: quitada columna `is_active` inexistente, categorías pasadas a mayúsculas | El seed nunca corrió contra ninguna BD y ya no coincidía con el schema actual | Ejecutado contra producción: 328 filas insertadas, conteo por categoría verificado |
| `8dfb84a` | `reportsService.updateReport`/`deleteReport` eliminados | Apuntaban a endpoints inexistentes en el backend (`PATCH /reportes/{id}` genérico y `DELETE /reports/{id}` no existen); no se llamaban desde ninguna página | `grep` confirmó cero usos; `tsc --noEmit` y `npm run build` limpios |
| `844b744` | Favicon agregado (`icon.svg` + `favicon.ico`) | 404 en `/favicon.ico` reportado por el usuario en consola de producción | Build incluye ambos archivos en `.next/server/app/` |
| `a985e8d` | `LoginResponse` incluye `refresh_token`; `login()` lo genera | `POST /auth/refresh` existía y funcionaba pero era inalcanzable — ningún cliente podía obtener un refresh token. Confirmado contra `api/openapi.yaml` que el contrato siempre esperó este campo | `test_refresh_token_success` dejó de autosaltarse; suite completa 239 passed / 0 failed |

## Incidente de producción resuelto

**Síntoma reportado**: capa de puntos de interés (POIs) vacía en el mapa del dashboard.

**Diagnóstico**: tabla `pois` en producción con 0 filas — el script de seed existía en el repo pero nunca se había ejecutado contra ninguna base de datos, ni siquiera en desarrollo.

**Causa secundaria descubierta durante el fix**: el seed además estaba desactualizado — referenciaba una columna `is_active` que ya no existe en el schema, y usaba valores de categoría en minúscula cuando el enum de Postgres los define en mayúscula (`HOSPITAL`, no `hospital`). Habría fallado igual si alguien lo hubiera intentado correr antes.

**Resolución**: corregido el script, ejecutado contra producción vía `railway ssh` (el contenedor no tiene cliente `psql`, se ejecutó a través de SQLAlchemy). Verificado end-to-end: 328 POIs insertados, y la query exacta que usa `MapView.tsx` (capturada de logs de tráfico real) confirmada devolviendo 259 resultados con coordenadas válidas.

**Efecto colateral detectado y confirmado transitorio**: un error de CORS reportado por el usuario justo después de un despliegue (disparado automáticamente por los pushes de esta sesión) — verificado en los logs del backend que el contenedor solo estuvo indisponible ~1 minuto durante el reinicio, y que todo el tráfico posterior (incluida esa misma query) respondió `200 OK` con headers CORS correctos. No requirió ningún cambio de código.

## Validaciones ejecutadas

| Validación | Comando | Resultado |
|---|---|---|
| Type-check frontend | `npx tsc --noEmit` | Limpio, ejecutado 3 veces en distintos puntos de la sesión |
| Build de producción frontend | `npm run build` | 14/14 páginas generadas, sin errores, ejecutado 3 veces |
| Lint frontend | `npm run lint` | Solo warnings preexistentes (hooks deps, `<img>` sin optimizar), nada nuevo |
| Suite de tests backend | `pytest` (venv local, SQLite) | **239 passed, 47 skipped, 0 failed** |
| Cobertura backend | `pytest --cov` | **39.51% total** — 6 servicios en 0%, ver `backend/TESTING.md` |
| Validación de `docker-compose.yml` | `docker compose config --quiet` | OK (solo warnings de vars no seteadas, esperado sin `.env`) |
| Validación de `docker-compose.prod.yml` | `docker compose config --quiet` | OK — nota menor: atributo `version:` obsoleto, cosmético |
| Verificación de secretos de producción | `railway variables --service backend` | `SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `MINIO_SECRET_KEY` confirmados como reales, no defaults |
| Verificación de backfills en producción | Consulta directa a la BD vía `railway ssh` | 0 candidatos pendientes en los 3 scripts, confirmando que ya habían corrido o no eran necesarios |

No se ejecutaron `flake8`/`black`/`bandit`/`safety` (los corre el job `code-quality` de CI, que además no bloquea el merge — ver `docs/infrastructure/CI_CD.md`).

## Riesgos y deuda técnica pendiente

Ítems documentados pero **no resueltos** en esta sesión — decisión consciente de no ampliar el alcance sin pedirlo:

- **Cobertura de tests: 39.51%**, con `services/anonymizer.py`, `deduplication_service.py`, `notification_service.py`, `queue_service.py`, `tasks/ml_tasks.py`, `tasks/sla_tasks.py` en **0%** — solo cubiertos por scripts en `tests/manual/`, excluidos de CI. Ver detalle completo en `docs/backend/TESTING.md`.
- **`GET /pois` sin ningún test** — ni RBAC ni funcional. Es justo el endpoint del incidente de producción de esta sesión.
- **Job `code-quality` de CI no bloquea el merge** — casi todos sus pasos (`black`, `isort`, `pylint`, `bandit`, `safety`) usan `|| echo "... failed"` en vez de fallar el build.
- **Sin CI para frontend, mobile ni `ml/`** — solo existe `backend-tests.yml`.
- **Protección de rutas del dashboard solo en cliente** — sin `middleware.ts` de Next.js.
- **`docker-compose.prod.yml`** tiene el atributo `version:` obsoleto (cosmético, Docker Compose lo ignora con un warning).

## Elementos no modificados por falta de certeza

- **`ml/anonymization/docs/ANONYMIZATION_TRAINING_PLAN.md`** y el resto de `ml/docs/` no revisados en profundidad más allá de corregir las referencias a notebooks archivados — su vigencia de contenido no se auditó línea por línea.
- **Backups/estrategia de recuperación de la base de datos de producción** — no se encontró configuración en el repositorio; no se investigó si Railway lo gestiona automáticamente fuera del repo.
- **`POST /auth/login/oauth2`** (endpoint de tooling/Swagger) no recibió el mismo fix de `refresh_token` que `POST /auth/login` — se dejó igual por ser un endpoint secundario, no el flujo principal de clientes.

## Recomendaciones futuras

1. Escribir tests reales (no solo scripts manuales) para los 6 servicios en 0% de cobertura, priorizando `deduplication_service.py` y `priority_service.py` por ser lógica de negocio central.
2. Agregar tests (RBAC + funcional) para `GET /pois`.
3. Decidir si el job `code-quality` de CI debe empezar a bloquear el merge, o si el comportamiento actual (solo informativo) es intencional.
4. Evaluar `middleware.ts` de Next.js para protección de rutas a nivel de servidor, si el equipo lo considera necesario — es una decisión de arquitectura, no de limpieza.
5. Considerar mover los scripts de `tests/manual/` con lógica de negocio real (`test_b07_deduplication.py`, `test_b08_priority_service.py`, `test_b09_export.py`) a la suite principal con mocks apropiados, en vez de dejarlos como scripts de verificación puntual.
