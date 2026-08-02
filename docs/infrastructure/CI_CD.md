# CI/CD

[← Volver al índice](../README.md)

## Estado actual

Existe **un único workflow** de GitHub Actions: `.github/workflows/backend-tests.yml` ("Backend Tests (B-11)"). No hay CI para frontend, mobile ni `ml/`, y no hay workflow de despliegue (CD) — el despliegue a Railway ocurre fuera de este repositorio.

## `backend-tests.yml`

**Disparadores**: `push`/`pull_request` a `main`/`develop` con filtro de path (`backend/**`, el propio workflow), más `workflow_dispatch` para ejecución manual.

> **Desajuste de nombre de rama**: el workflow apunta a `develop`, pero la rama de integración que existe en el remoto se llama `dev` (`origin/dev`). Con la configuración actual, ningún push o PR contra `dev` dispara el CI: solo lo hacen los de `main`. Se corrige cambiando `develop` por `dev` en las dos listas `branches:` del workflow, o renombrando la rama remota.

### Job `unit-tests`

- Matriz: Python 3.11 y 3.12.
- Servicios: `postgres` (`postgis/postgis:15-3.3`), `redis:7-alpine`, ambos con healthcheck.
- Pasos: instala dependencias (`pip install -r requirements.txt`), corre `alembic upgrade head`, ejecuta `pytest tests/ -m "unit"` y luego `pytest tests/ -m "integration"` (con cobertura acumulada), sube el reporte a Codecov.

### Job `contract-tests`

- Un solo Python 3.11, con `postgres` como servicio.
- Ejecuta `pytest tests/test_contract.py -m "contract"` (basado en `schemathesis`, valida la API contra su propio esquema OpenAPI).
- Valida `api/openapi.yaml` con `openapi-spec-validator`.

### Job `code-quality`

- Corre `black --check`, `isort --check-only`, `flake8` (solo errores críticos: `E9,F63,F7,F82`), `pylint` (modo `--exit-zero`, no bloquea), `bandit` (seguridad estática) y `safety check` (vulnerabilidades de dependencias).
- **Importante**: casi todos los pasos de este job usan `|| echo "... failed"` en vez de fallar el build — es decir, **actualmente no bloquea el merge si el formato, el lint o el escaneo de seguridad fallan**, solo lo registra en el log. Esto es una decisión existente del pipeline, no un error de este documento; si se quiere que estos checks bloqueen, requiere cambiar el propio workflow (fuera del alcance de esta documentación).

### Job `test-summary`

- Depende de los tres jobs anteriores, corre siempre (`if: always()`).
- Falla explícitamente el pipeline solo si `unit-tests` no fue exitoso; `contract-tests` y `code-quality` solo generan advertencias en el resumen.

## Brechas conocidas

- Sin pipeline de CI para `frontend/` (no se corre `npm run build`, `tsc --noEmit`, `next lint` ni Playwright automáticamente en PRs).
- Sin pipeline de CI para `mobile/` (no se corre `flutter analyze` ni `flutter test`).
- Sin pipeline de CI para `ml/` (no aplica de la misma forma al ser entrenamiento offline, pero tampoco hay validación automática de los scripts de `ml/scripts/`).
- Sin workflow de CD — el despliegue a Railway no está automatizado desde este repositorio.
- El workflow solo se dispara en `main` por el desajuste `develop` / `dev` descrito arriba.

Ver clasificación de este hallazgo como riesgo en [REPOSITORY_AUDIT.md](../REPOSITORY_AUDIT.md#8-riesgos-detectados).
