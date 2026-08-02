# Guía de contribución — SIRCCD

Gracias por contribuir. Este documento describe el flujo de trabajo, las convenciones y los checks que debe pasar cualquier cambio antes de entrar a `main`.

Antes de empezar, lee [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) para levantar el entorno local, y [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para entender cómo se comunican los componentes.

## Índice

- [Preparar el entorno](#preparar-el-entorno)
- [Flujo de trabajo](#flujo-de-trabajo)
- [Convención de ramas](#convención-de-ramas)
- [Convención de commits](#convención-de-commits)
- [Estándares de código](#estándares-de-código)
- [Pruebas](#pruebas)
- [Checklist antes del PR](#checklist-antes-del-pr)
- [Proceso de revisión](#proceso-de-revisión)
- [Documentación](#documentación)
- [Seguridad](#seguridad)

## Preparar el entorno

Requisitos: Docker + Docker Compose, Python 3.11, Node.js 20+, Flutter SDK (solo si tocas `mobile/`).

```bash
cp .env.example .env
docker compose up --build
```

O el flujo manual (backend + frontend en paralelo):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

`scripts/dev.ps1` asume un virtualenv en `.venv/` en la raíz del repositorio y `frontend/node_modules` instalado (lo instala si falta). Detalle completo en [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).

## Flujo de trabajo

1. Sincroniza `main` y crea una rama de feature desde ahí.
2. Haz commits pequeños y atómicos siguiendo la convención de abajo.
3. Corre los tests del componente que tocaste antes de abrir el PR.
4. Abre un Pull Request hacia `main` usando la plantilla.
5. Espera a que el CI esté en verde y a la aprobación de un revisor.

Nunca se hace push directo a `main`.

## Convención de ramas

```text
feat/mod-XX-descripcion-corta      Nueva funcionalidad del módulo XX
fix/mod-XX-descripcion-corta       Corrección de bug
refactor/descripcion-corta         Refactor sin cambio de comportamiento
docs/descripcion-corta             Solo documentación
chore/descripcion-corta            Tooling, dependencias, configuración
```

`XX` es el número del módulo del proyecto (por ejemplo `feat/mod-07-sla-alerts`). Usa kebab-case y evita nombres genéricos como `fix/bugs`.

## Convención de commits

Conventional Commits, en español, en imperativo y sin punto final:

```text
<tipo>(<alcance opcional>): <descripción>

<cuerpo opcional: qué cambió y por qué, no cómo>
```

Tipos permitidos: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.

Alcances habituales: `backend`, `frontend`, `mobile`, `ml`, `db`, `infra`, `docs`.

Ejemplos reales del repositorio:

```text
feat(frontend): add public user guide at /guia
fix(backend): complete the login/refresh-token pair
fix(db): correct stale pois_insert.sql and seed production POIs
docs: add SIRCCD user manual
```

Si el commit cierra un issue, referencia el número en el cuerpo: `Closes #42`.

## Estándares de código

Las reglas transversales (funciones < 50 líneas, archivos < 800 líneas, sin anidamiento profundo, sin secretos en código, errores manejados explícitamente) aplican a todos los componentes.

### Backend (Python / FastAPI)

- Formateo con `black`, orden de imports con `isort`.
- Linting con `flake8` y `pylint`; análisis de seguridad con `bandit`.
- La lógica de negocio va en `services/`, no en los routers de `api/`.
- Toda consulta a base de datos parametrizada vía SQLAlchemy — nunca concatenación de strings.
- Los cambios de esquema requieren una migración de Alembic (`alembic revision --autogenerate -m "..."`). Revisa siempre la migración generada antes de commitearla.

```bash
cd backend
black .
isort .
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
bandit -r . -ll
```

### Frontend (Next.js / TypeScript)

- `npm run lint` y `npm run type-check` deben pasar sin errores.
- Sin `any` implícito ni `console.log` en el código que se mergea.
- Estado de servidor y estado de cliente separados; no dupliques respuestas de la API dentro de los stores de Zustand.
- Las llamadas a la API pasan por la capa de servicios existente, no por `axios` suelto en los componentes.

```bash
cd frontend
npm run lint
npm run type-check
```

### Mobile (Flutter / Dart)

```bash
cd mobile
dart format .
flutter analyze
flutter test
```

### ML

`ml/` es offline y desacoplado del runtime de producción: entrenamiento en Google Colab, artefactos versionados fuera del repositorio. No introduzcas dependencias de `ml/` dentro de `backend/`.

## Pruebas

Todo cambio de comportamiento necesita pruebas. El backend es el componente con la barra más alta, por ser el que concentra la lógica de negocio.

### Backend

```bash
cd backend
./run_tests.sh              # suite completa (unit + integration + contract)
./run_tests.sh unit         # solo unitarios
./run_tests.sh integration  # solo integración
./run_tests.sh contract     # contrato OpenAPI (Schemathesis)
./run_tests.sh fast         # todo menos los tests marcados slow
./run_tests.sh coverage     # reporte HTML en htmlcov/index.html
```

En Windows, usa `run_tests.bat` con los mismos argumentos.

Marca cada test con su categoría (`pytest.ini` usa `--strict-markers`, un marker no declarado hace fallar la corrida):

```python
@pytest.mark.unit
@pytest.mark.auth
def test_login_rejects_invalid_password():
    ...
```

Markers disponibles: `unit`, `integration`, `contract`, `slow`, `auth`, `reports`, `incidents`, `ml`, `db`.

Estructura Arrange–Act–Assert y nombres que describen el comportamiento (`test_returns_empty_list_when_no_reports_match`), no la implementación.

### Frontend

```bash
cd frontend
npx playwright test
```

### Cobertura

El objetivo del proyecto es 80%. La cobertura actual del backend está por debajo de ese número (ver [docs/backend/TESTING.md](docs/backend/TESTING.md)), así que la regla práctica es: **un PR no puede bajar la cobertura**, y todo servicio nuevo entra con tests.

## Checklist antes del PR

- [ ] Los tests del componente tocado pasan localmente.
- [ ] Linter y type-check en verde.
- [ ] Sin secretos, tokens ni credenciales en el diff.
- [ ] Sin `console.log`, `print()` de depuración ni código comentado.
- [ ] Cambios de esquema acompañados de su migración de Alembic.
- [ ] Variables de entorno nuevas añadidas a `.env.example` y a [docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md).
- [ ] Endpoints nuevos o modificados reflejados en [docs/backend/API.md](docs/backend/API.md).
- [ ] La rama está actualizada con `main` y sin conflictos.

## Proceso de revisión

- Un PR necesita al menos una aprobación antes del merge.
- El CI de backend (`.github/workflows/backend-tests.yml`) debe estar en verde. Solo corre para cambios bajo `backend/`; frontend, mobile y `ml/` se validan manualmente por ahora.
- Los comentarios de revisión se clasifican por severidad: **CRITICAL** (bloquea), **HIGH** (debería arreglarse antes del merge), **MEDIUM** / **LOW** (opcional o para seguimiento).
- Se hace merge con squash, dejando el mensaje del commit final en formato Conventional Commits.

## Documentación

La documentación vive en `docs/` y está indexada en [docs/README.md](docs/README.md). Si un cambio altera comportamiento observable, actualiza el documento correspondiente **en el mismo PR**:

| Cambio | Documento a actualizar |
|---|---|
| Endpoint nuevo o modificado | `docs/backend/API.md` |
| Tabla, columna o migración | `docs/database/SCHEMA.md`, `docs/database/MIGRATIONS.md` |
| Variable de entorno | `.env.example` + `docs/ENVIRONMENT_VARIABLES.md` |
| Ruta o pantalla del frontend | `docs/frontend/ROUTING.md` |
| Componente o flujo de datos nuevo | `docs/ARCHITECTURE.md` |
| Decisión arquitectónica | Nuevo ADR en `docs/decisions/` |

## Seguridad

**No abras un issue público para reportar una vulnerabilidad.** Repórtala en privado al mantenedor del repositorio.

Antes de cada commit, verifica: sin secretos hardcodeados, entradas de usuario validadas, consultas parametrizadas, HTML sanitizado y mensajes de error que no filtren detalles internos. Ver [docs/SECURITY.md](docs/SECURITY.md) y [docs/SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md).
