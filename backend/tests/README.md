# Testing Backend

Organizacion de pruebas para backend despues de la reestructura.

## Estructura actual

```text
backend/tests/
|- conftest.py
|- test_auth.py
|- test_contract.py
|- test_health.py
|- test_incidents.py
|- test_reports.py
|- manual/
   |- fixtures/
   |- test_auth_manual.py
   |- test_b04_reports.py
   |- test_b05_anonymization.py
   |- test_b06_*.py
   |- test_b07_*.py
   |- test_b08_*.py
   |- test_b09_export.py
   |- test_b10_observability.py
   |- test_geospatial.py
   |- TESTING_B06.py
```

## Que va en cada zona

- `tests/` (raiz): pruebas automatizadas de CI.
- `tests/manual/`: pruebas manuales, smoke y utilitarios de validacion puntual.
- `tests/manual/fixtures/`: imagenes y artefactos usados por pruebas manuales.

## Ejecucion

### Automatizado

```powershell
cd backend
pytest
```

### Manual (ejemplos)

```powershell
cd backend
pytest tests/manual/test_b07_deduplication.py -q
pytest tests/manual/test_b05_anonymization.py -q
```

## Nota

Las pruebas manuales pueden requerir servicios levantados (API, Redis, DB) y no deben considerarse bloqueantes de CI salvo que se promuevan explicitamente a suite automatica.
