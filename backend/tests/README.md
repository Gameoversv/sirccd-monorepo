# Testing - SIRCCD Backend (B-11)

Suite completa de pruebas unitarias, de integración y de contrato para el backend del SIRCCD.

## 📋 Tabla de Contenidos

- [Estructura de Tests](#estructura-de-tests)
- [Tipos de Tests](#tipos-de-tests)
- [Ejecución Local](#ejecución-local)
- [Cobertura de Código](#cobertura-de-código)
- [CI/CD](#cicd)
- [Convenciones](#convenciones)

## 📁 Estructura de Tests

```
backend/tests/
├── conftest.py              # Fixtures compartidas
├── test_auth.py             # Tests de autenticación
├── test_reports.py          # Tests de reportes
├── test_incidents.py        # Tests de incidentes
├── test_contract.py         # Tests de contrato OpenAPI
└── test_health.py           # Tests de health check
```

## 🧪 Tipos de Tests

### Tests Unitarios (`@pytest.mark.unit`)

Tests aislados que validan componentes individuales sin dependencias externas.

```python
@pytest.mark.unit
def test_password_hashing():
    password = "SecurePass123!"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
```

**Características:**
- Rápidos (<100ms)
- Sin DB real (usa SQLite en memoria)
- Mocks de servicios externos
- Alta cobertura de código

### Tests de Integración (`@pytest.mark.integration`)

Tests que validan interacción entre múltiples componentes.

```python
@pytest.mark.integration
def test_create_report_full_flow(client, auth_headers):
    response = client.post("/api/v1/reportes", ...)
    assert response.status_code == 201
```

**Características:**
- Más lentos (100ms-1s)
- Base de datos real (PostgreSQL en CI)
- Simulan flujos completos
- Validan integraciones

### Tests de Contrato (`@pytest.mark.contract`)

Tests que validan que la API cumple con el esquema OpenAPI.

```python
@pytest.mark.contract
@schema.parametrize()
def test_api_schema_conformance(case):
    response = case.call_asgi(app)
    case.validate_response(response)
```

**Características:**
- Usa Schemathesis
- Valida requests/responses contra OpenAPI
- Detecta discrepancias
- Genera tests automáticamente

## 🚀 Ejecución Local

### Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

### Ejecutar Todos los Tests

```bash
pytest
```

### Ejecutar Tests Específicos

```bash
# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Solo tests de contrato
pytest -m contract

# Tests de un módulo específico
pytest tests/test_auth.py

# Un test específico
pytest tests/test_auth.py::TestUserLogin::test_login_success
```

### Ejecutar con Coverage

```bash
# Con reporte en terminal
pytest --cov --cov-report=term-missing

# Con reporte HTML (ver en htmlcov/index.html)
pytest --cov --cov-report=html

# Con ambos
pytest --cov --cov-report=term --cov-report=html
```

### Ejecutar con Verbosidad

```bash
# Verbose (-v)
pytest -v

# Muy verbose (-vv)
pytest -vv

# Mostrar print() statements
pytest -s

# Detener en primer fallo
pytest -x

# Ver logs en tiempo real
pytest --log-cli-level=INFO
```

### Tests Rápidos (Skip Slow Tests)

```bash
pytest -m "not slow"
```

## 📊 Cobertura de Código

### Ver Reporte de Coverage

Después de ejecutar `pytest --cov --cov-report=html`:

```bash
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

### Objetivo de Coverage

- **Mínimo**: 70% (PR no se puede mergear con menos)
- **Objetivo**: 80%
- **Ideal**: 90%+

### Áreas Críticas (90%+ requerido)

- `core/security.py` - Autenticación y autorización
- `services/priority_service.py` - Cálculo de prioridad
- `api/routes/auth.py` - Endpoints de autenticación

## 🔄 CI/CD (GitHub Actions)

### Workflow: `.github/workflows/backend-tests.yml`

Se ejecuta automáticamente en:
- Push a `main` o `develop`
- Pull Requests
- Manualmente desde GitHub Actions UI

### Jobs del Workflow

1. **unit-tests**
   - Matrix: Python 3.11, 3.12
   - Services: PostgreSQL, Redis
   - Coverage: Sube a Codecov

2. **contract-tests**
   - Valida esquema OpenAPI
   - Ejecuta tests de Schemathesis

3. **code-quality**
   - Black (formatting)
   - isort (imports)
   - Flake8 (linting)
   - Pylint (análisis)
   - Bandit (seguridad)
   - Safety (vulnerabilidades)

4. **test-summary**
   - Consolida resultados
   - Falla si tests críticos fallan

### Ver Resultados en GitHub

1. Ir a la pestaña "Actions"
2. Seleccionar el workflow "Backend Tests (B-11)"
3. Ver detalles de cada job

## 📝 Convenciones

### Nombres de Tests

```python
# ✅ Bueno
def test_user_login_with_valid_credentials():
    ...

# ❌ Malo
def test1():
    ...
```

### Estructura AAA (Arrange-Act-Assert)

```python
def test_example():
    # Arrange - Preparar datos
    user = create_test_user()
    
    # Act - Ejecutar acción
    result = login(user.email, "password")
    
    # Assert - Verificar resultado
    assert result.success is True
```

### Uso de Fixtures

```python
# Usar fixtures en lugar de crear datos manualmente
def test_with_fixtures(client, auth_headers_citizen):
    response = client.get("/api/v1/reportes", headers=auth_headers_citizen)
    assert response.status_code == 200
```

### Mocks

```python
from unittest.mock import Mock, patch

def test_with_mock(mock_ml_service):
    with patch("services.ml_service.ml_service", mock_ml_service):
        result = process_image("image.jpg")
        assert result is not None
```

## 🛠️ Scripts Útiles

### `run_tests.sh` (Linux/Mac)

```bash
#!/bin/bash
# Ejecutar suite completa de tests

echo "🧪 Ejecutando tests unitarios..."
pytest -m unit --cov --cov-report=term

echo "🔗 Ejecutando tests de integración..."
pytest -m integration --cov --cov-append

echo "📄 Ejecutando tests de contrato..."
pytest -m contract

echo "✅ Tests completados!"
```

### `run_tests.bat` (Windows)

```batch
@echo off
echo 🧪 Ejecutando tests unitarios...
pytest -m unit --cov --cov-report=term

echo 🔗 Ejecutando tests de integración...
pytest -m integration --cov --cov-append

echo 📄 Ejecutando tests de contrato...
pytest -m contract

echo ✅ Tests completados!
```

## 🐛 Debugging Tests

### Ejecutar con Debugger

```python
# Agregar breakpoint en el test
def test_example():
    import pdb; pdb.set_trace()
    result = some_function()
    assert result is not None
```

### Ver SQL Queries

```python
# Agregar en conftest.py
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Ejecutar un Solo Test en VSCode

1. Instalar extensión "Python Test Explorer"
2. Abrir test file
3. Click en ▶️ junto al test
4. Ver output en panel de Tests

## 📚 Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [Schemathesis Documentation](https://schemathesis.readthedocs.io/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## 🤝 Contribuir

### Antes de hacer PR

1. Ejecutar tests localmente: `pytest`
2. Verificar coverage: `pytest --cov`
3. Ejecutar linters: `black . && flake8 .`
4. Agregar tests para nuevo código

### Criterios de Aceptación

- ✅ Todos los tests pasan
- ✅ Coverage >= 70%
- ✅ No hay vulnerabilidades de seguridad
- ✅ Code quality checks pasan

## 📞 Soporte

Si tienes problemas con los tests:

1. Revisar logs: `pytest.log`
2. Ver este README
3. Preguntar en Slack: #sirccd-backend
4. Abrir issue en GitHub

---

**Última actualización**: 2026-03-03  
**Responsables**: Equipo Backend SIRCCD
