# Pruebas — Backend

[← Volver al índice](../README.md)

## Framework y configuración

pytest (`pytest.ini`), con marcadores: `unit`, `integration`, `contract`, `slow`, `auth`, `reports`, `incidents`, `ml`, `db`. `pytest.ini` usa `--strict-markers`, así que un marcador no declarado hace fallar la corrida. `tests/conftest.py` configura una base de datos SQLite en memoria y mockea Redis/MinIO/ML mediante variables de entorno antes de importar la app, con fixtures de `TestClient` y usuarios de prueba por rol.

Convenciones de escritura de tests (estructura AAA, nombres, cuándo son obligatorios) en [../../CONTRIBUTING.md](../../CONTRIBUTING.md#pruebas).

## Ejecución

```bash
cd backend
./run_tests.sh              # todos (unit + integration + contract + reporte HTML)
./run_tests.sh unit         # solo unitarios
./run_tests.sh integration  # solo integración
./run_tests.sh contract     # solo contrato (schemathesis)
./run_tests.sh auth         # solo tests de autenticación
./run_tests.sh reports      # solo tests de reportes
./run_tests.sh incidents    # solo tests de incidentes
./run_tests.sh fast         # todos menos los marcados "slow"
./run_tests.sh coverage     # con reporte HTML en htmlcov/index.html
```

En Windows: `run_tests.bat` (mismo comportamiento).

## Qué cubre la suite automática (`tests/test_*.py`)

Auth, contrato (`test_contract.py`, basado en `schemathesis` — valida la API contra su propio `api/openapi.yaml`), servicio EXIF, health, proxy de imágenes, incidentes (incluyendo filtros P03), reportes, RBAC (S02 + extendido), cifrado de campos (S03), modelo de zonas.

## Tests que se saltan en local (SQLite sin PostGIS)

Correr solo los unitarios en local (`pytest -m unit`) deja **25 tests en estado `skipped`**: los de `tests/test_reports.py` que necesitan la tabla `reports` con columnas geográficas (`ST_GeogFromText`), que SQLite no soporta. Se saltan de forma explícita con el mensaje `PostGIS tables not available in SQLite test env`, no fallan.

En CI sí corren, porque el workflow levanta `postgis/postgis:15-3.3` como servicio. Para reproducir el entorno completo en local, apunta `DATABASE_URL` a una instancia PostGIS (por ejemplo la del `docker compose` de desarrollo) en vez de usar el default SQLite en memoria.

Medición de referencia local (2026-08-02, `pytest -m unit`): 59 pasados, 25 saltados, 202 deseleccionados; cobertura parcial de 30.54% (solo unitarios, no comparable con el 39.51% de la suite completa más abajo).

## Nota para Windows

Al importar la app en una consola con codificación `cp1252`, `services/anonymizer.py` intenta imprimir un mensaje con caracteres Unicode (`⚠`, `—`) cuando `ultralytics` no está instalado, y el `print` revienta con `UnicodeEncodeError`, abortando el arranque completo. Solución: exportar `PYTHONIOENCODING=utf-8` antes de correr pytest o el servidor, o instalar `ultralytics` para que la rama del mensaje no se ejecute.

## `tests/manual/` — no cubierto por CI

21 scripts de verificación manual, **no descubiertos automáticamente por pytest** (`pytest.ini` apunta `testpaths=tests`, pero no se ejecutan por defecto salvo que se apunten explícitamente). Parecen ligados a tickets específicos (b04–b10) — útiles para verificación puntual durante desarrollo, no como parte de la suite regular.

## Tests de servicios añadidos (2026-08-02)

| Archivo | Cubre | Cobertura del módulo |
|---|---|---|
| `tests/test_sla_service.py` | Horas de SLA por prioridad y override por `SLAConfig`, cálculo de deadline, los cinco estados (`not_started`, `on_track`, `warning`, `overdue`, `completed`), umbral de aviso configurable y `get_sla_info` | `sla_service.py`: 0% → **91.78%** |
| `tests/test_priority_service.py` | Tramos de score (POIs, duplicados, edad), límites de nivel de prioridad, normalización de pesos y la matriz completa de transiciones de estado | `priority_service.py`: 15.91% → **47.73%** |
| `tests/test_pois.py` | RBAC del endpoint, validación de parámetros y coherencia del mapeo capa ↔ categorías de origen | `api/routes/pois.py`: 39.53% (sin cambio, ver abajo) |

### Qué queda fuera y por qué

`tests/conftest.py` solo crea la tabla `users` en SQLite: todo lo que use columnas PostGIS (`incidents`, `reports`, `pois`) no se puede materializar ahí. Por eso estos tests trabajan con objetos en memoria y con las tablas de configuración (`sla_configs`, `priority_settings`), que sí son columnas planas.

Sin cubrir, a la espera de una suite de integración contra PostGIS real:

- `sla_service.get_expiring_incidents` y `get_overdue_incidents` — construyen queries sobre `incidents`.
- `priority_service._count_nearby_pois`, `_count_nearby_duplicates`, `recalculate_priority`, `update_incident_status`.
- El cuerpo de `GET /pois` (líneas 70-115): por eso su porcentaje no sube pese a tener ya tests de RBAC y de mapeo.

## Cobertura

`.coveragerc` excluye migraciones, `tests/`, `worker*.py` y `verify_*.py` del cálculo de cobertura.

**Medido el 2026-07-19** (`pytest --cov --cov-report=term-missing`, suite completa contra SQLite local): **39.51% total** (4346 statements, 2411 sin cubrir).

Módulos con **0% de cobertura** — sin ningún test automático, solo scripts en `tests/manual/` (excluidos de CI):

| Módulo | Statements |
|---|---|
| `services/anonymizer.py` | 109 |
| `services/deduplication_service.py` | 462 |
| `services/notification_service.py` | 37 |
| `services/queue_service.py` | 59 |
| `tasks/ml_tasks.py` | 26 |
| `tasks/sla_tasks.py` | 38 |

Módulos con cobertura muy baja (<25%): `services/priority_service.py` (15.91%), `services/export_service.py` (18.66%), `services/sla_service.py` (23.29%), `services/spatial_clustering_service.py` (24.47%), `services/report_processing_service.py` (13.26%).

`api/routes/pois.py` en 39.53% — sin ningún test dedicado, la cobertura parcial viene de imports/fixtures compartidos con otros tests, no de pruebas reales del endpoint.

En contraste, `models/*` está en 100% (cubierto indirectamente por fixtures de `conftest.py`) y varios `schemas/*` también en 100%.

## Dependencias externas en pruebas

Las pruebas usan una base SQLite en memoria (no Postgres real) y mocks de Redis/MinIO/Roboflow vía variables de entorno — no requieren Docker levantado para correr localmente. El CI (`.github/workflows/backend-tests.yml`) sí usa contenedores reales de Postgres/Redis para las pruebas de integración y contrato, más cercano a producción.

## Pruebas de contrato

`test_contract.py` usa `schemathesis` para generar casos de prueba automáticamente a partir de `api/openapi.yaml` — detecta violaciones del contrato declarado (tipos de respuesta, códigos de estado) sin necesidad de escribir cada caso a mano. Requiere la variable `INTEGRATION_TEST` para activarse contra un servidor real en algunos modos (ver `conftest.py`).

## Limitaciones conocidas

- Sin pruebas de carga/performance documentadas.
- `tests/manual/` no forma parte de la cobertura reportada — cualquier regresión que solo esas pruebas detectarían no se atrapa en CI. Esto incluye toda la lógica de deduplicación (`test_b07_*.py`), scoring de prioridad (`test_b08_*.py`), exportación (`test_b09_export.py`) y cola ML (`test_b06_queue_inference.py`).
- **`GET /pois` no tiene ningún test dedicado** — ni RBAC ni funcional. Es el endpoint del incidente de producción del 2026-07-19 (capa de POIs vacía); su ausencia de cobertura no habría atrapado ese problema de todos modos (el bug era de datos, no de código), pero sí deja sin probar la lógica de agrupación por categorías de riesgo (`LAYER_TO_SOURCE_CATEGORIES` en `api/routes/pois.py`).
- `pytest.ini` declara una sección `[env]` que requiere el plugin `pytest-env` — **no está en `requirements.txt`**, por lo que esa configuración es ignorada silenciosamente (sin error visible). `conftest.py` logra el mismo resultado seteando variables de entorno manualmente antes de importar la app, así que no rompe nada, pero la sección `[env]` de `pytest.ini` es configuración muerta.
- ✅ **Resuelto**: `POST /auth/login` no incluía `refresh_token` en la respuesta pese a que `POST /auth/refresh` existía y lo requería. Confirmado que `api/openapi.yaml` (spec usado por los tests de contrato) **siempre documentó `refresh_token`** en la respuesta de login — el código había quedado atrás del contrato, no al revés. Arreglado: `LoginResponse` ahora incluye `refresh_token` (`schemas/auth.py`), y `login()` lo genera con `create_refresh_token()` (`api/routes/auth.py`). `test_refresh_token_success` ya no se autosalta — pasa de verdad. El frontend web no se tocó: nunca consume `/auth/refresh` (usa redirect a login en 401 en vez de refresh silencioso), así que no había nada que conectar ahí; el par login/refresh queda disponible para mobile u otros clientes.
- Bajo SQLite local, 48 tests se saltan (`PostGIS tables not available in SQLite test env`) — sí corren completos en CI contra Postgres+PostGIS real.
