# Pruebas — Backend

[← Volver al índice](../README.md)

## Framework y configuración

pytest (`pytest.ini`), con marcadores: `unit`, `integration`, `contract`, `slow`, `auth`, `reports`, `incidents`, `ml`. `tests/conftest.py` configura una base de datos SQLite en memoria y mockea Redis/MinIO/ML mediante variables de entorno antes de importar la app, con fixtures de `TestClient` y usuarios de prueba por rol.

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

## `tests/manual/` — no cubierto por CI

21 scripts de verificación manual, **no descubiertos automáticamente por pytest** (`pytest.ini` apunta `testpaths=tests`, pero no se ejecutan por defecto salvo que se apunten explícitamente). Parecen ligados a tickets específicos (b04–b10) — útiles para verificación puntual durante desarrollo, no como parte de la suite regular.

## Cobertura

`.coveragerc` excluye migraciones, `tests/`, `worker*.py` y `verify_*.py` del cálculo de cobertura. El porcentaje de cobertura actual no se verificó en esta fase (requiere ejecutar `run_tests.sh coverage` y revisar `htmlcov/index.html`).

## Dependencias externas en pruebas

Las pruebas usan una base SQLite en memoria (no Postgres real) y mocks de Redis/MinIO/Roboflow vía variables de entorno — no requieren Docker levantado para correr localmente. El CI (`.github/workflows/backend-tests.yml`) sí usa contenedores reales de Postgres/Redis para las pruebas de integración y contrato, más cercano a producción.

## Pruebas de contrato

`test_contract.py` usa `schemathesis` para generar casos de prueba automáticamente a partir de `api/openapi.yaml` — detecta violaciones del contrato declarado (tipos de respuesta, códigos de estado) sin necesidad de escribir cada caso a mano. Requiere la variable `INTEGRATION_TEST` para activarse contra un servidor real en algunos modos (ver `conftest.py`).

## Limitaciones conocidas

- Sin pruebas de carga/performance documentadas.
- `tests/manual/` no forma parte de la cobertura reportada — cualquier regresión que solo esas pruebas detectarían no se atrapa en CI.
- No se auditó el porcentaje real de cobertura en esta fase (pendiente, ver [../REPOSITORY_AUDIT.md](../REPOSITORY_AUDIT.md)).
