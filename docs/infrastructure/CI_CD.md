# CI/CD

[← Volver al índice](../README.md)

## Estado actual

Dos workflows de GitHub Actions: `.github/workflows/backend-tests.yml` ("Backend Tests (B-11)") y `.github/workflows/e2e-tests.yml` ("E2E Tests (Playwright)"). No hay CI para mobile ni `ml/`, y no hay workflow de despliegue (CD) — el despliegue a Railway ocurre fuera de este repositorio.

## `backend-tests.yml`

**Disparadores**: `push`/`pull_request` a `main`/`dev` con filtro de path (`backend/**`, el propio workflow), más `workflow_dispatch` para ejecución manual.

> Hasta 2026-08-02 el workflow apuntaba a `develop`, rama que no existe en el remoto (la de integración es `dev`), así que nada excepto `main` disparaba el CI. Corregido.

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

## `e2e-tests.yml`

**Disparadores**: `push`/`pull_request` a `main`/`dev` cuando cambia `frontend/**`, `backend/**` o el propio workflow, más `workflow_dispatch`.

Job único `e2e` (timeout 30 min) que levanta el stack completo en el runner:

1. Servicios `postgres` (`postgis/postgis:15-3.3`) y `redis:7-alpine` con healthcheck.
2. Instala dependencias del backend y corre `alembic upgrade head`.
3. Arranca `uvicorn` en el puerto 8000 y espera hasta 60s a que `/api/v1/health` responda.
4. Siembra los usuarios de prueba: el admin con `python -m scripts.seed_admin`, el ciudadano vía `POST /api/v1/auth/register`.
5. `npm ci` + `npm run build` con `NEXT_PUBLIC_API_URL` apuntando al backend (Next.js inlinea las `NEXT_PUBLIC_*` en build), y arranca el frontend en el 3001.
6. `npx playwright install --with-deps chromium` y `npx playwright test`.
7. Sube el reporte HTML siempre; trazas y vídeos solo en fallo; vuelca los logs de ambos servicios si algo revienta.

Sin `ROBOFLOW_API_KEY` el backend usa el detector mock, y sin MinIO `storage.py` cae a disco local. Ambos comportamientos son suficientes para los flujos cubiertos. Detalle de los specs en [../frontend/TESTING.md](../frontend/TESTING.md).

## Historial de fallos del backend

Hasta 2026-08-02, **todos** los runs de `backend-tests.yml` fallaban en el paso "Run unit tests" con:

```text
ImportError while loading conftest '.../backend/tests/conftest.py'
E   RuntimeError: Directory 'storage' does not exist
```

`main.py` montaba `StaticFiles(directory="storage")` sobre un directorio gitignoreado: existe en las máquinas de desarrollo, pero no en un checkout limpio, así que la app no llegaba a importarse y pytest moría antes del primer test. Resuelto creando el directorio con `os.makedirs(..., exist_ok=True)` antes del `mount`.

## Brechas conocidas

- El CI del frontend cubre E2E, pero no corre `next lint` ni `tsc --noEmit` como pasos separados.
- Sin pipeline de CI para `mobile/` (no se corre `flutter analyze` ni `flutter test`).
- Sin pipeline de CI para `ml/` (no aplica de la misma forma al ser entrenamiento offline, pero tampoco hay validación automática de los scripts de `ml/scripts/`).
- Sin workflow de CD — el despliegue a Railway no está automatizado desde este repositorio.
- Sin pruebas E2E de la app móvil; `e2e-tests.yml` cubre solo las superficies web.

Ver clasificación de este hallazgo como riesgo en [REPOSITORY_AUDIT.md](../REPOSITORY_AUDIT.md#8-riesgos-detectados).
