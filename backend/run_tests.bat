@echo off
REM Script para ejecutar suite completa de tests del backend SIRCCD (Windows)

setlocal enabledelayedexpansion

echo ======================================
echo 🧪 SIRCCD Backend Test Suite (B-11)
echo ======================================
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Activar entorno virtual si existe
if exist ".venv\Scripts\activate.bat" (
    echo 📦 Activando entorno virtual...
    call .venv\Scripts\activate.bat
) else if exist ".venv-py314-backup\Scripts\activate.bat" (
    echo 📦 Activando entorno virtual backup...
    call .venv-py314-backup\Scripts\activate.bat
)

REM Verificar que pytest esté instalado
pytest --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pytest no está instalado
    echo Instalando dependencias...
    pip install -r requirements.txt
)

REM Parse argumentos
set TEST_TYPE=%1
if "%TEST_TYPE%"=="" set TEST_TYPE=all

if "%TEST_TYPE%"=="unit" (
    echo 🧪 Ejecutando tests unitarios...
    pytest -m unit -v --cov --cov-report=term-missing
    goto :end
)

if "%TEST_TYPE%"=="integration" (
    echo 🔗 Ejecutando tests de integración...
    pytest -m integration -v --cov --cov-report=term-missing
    goto :end
)

if "%TEST_TYPE%"=="contract" (
    echo 📄 Ejecutando tests de contrato...
    pytest -m contract -v
    goto :end
)

if "%TEST_TYPE%"=="auth" (
    echo 🔐 Ejecutando tests de autenticación...
    pytest tests/test_auth.py -v --cov --cov-report=term-missing
    goto :end
)

if "%TEST_TYPE%"=="reports" (
    echo 📝 Ejecutando tests de reportes...
    pytest tests/test_reports.py -v --cov --cov-report=term-missing
    goto :end
)

if "%TEST_TYPE%"=="incidents" (
    echo 🚨 Ejecutando tests de incidentes...
    pytest tests/test_incidents.py -v --cov --cov-report=term-missing
    goto :end
)

if "%TEST_TYPE%"=="fast" (
    echo ⚡ Ejecutando tests rápidos (sin slow^)...
    pytest -m "not slow" -v --cov --cov-report=term-missing
    goto :end
)

if "%TEST_TYPE%"=="coverage" (
    echo 📊 Ejecutando tests con coverage completo...
    pytest --cov --cov-report=html --cov-report=term-missing
    echo.
    echo ✅ Reporte HTML generado en: htmlcov\index.html
    REM Abrir en navegador
    start htmlcov\index.html
    goto :end
)

REM Por defecto: ejecutar todos los tests
echo 🧪 Ejecutando TODOS los tests...
echo.

echo 1️⃣  Tests Unitarios
pytest -m unit --cov --cov-report=term-missing
echo.

echo 2️⃣  Tests de Integración
pytest -m integration --cov --cov-append --cov-report=term-missing
echo.

echo 3️⃣  Tests de Contrato
pytest -m contract -v
echo.

echo 4️⃣  Generando reporte HTML...
pytest --cov --cov-report=html >nul 2>&1
echo.

:end
REM Verificar resultado
if errorlevel 1 (
    echo ======================================
    echo ❌ Algunos tests fallaron
    echo ======================================
    exit /b 1
) else (
    echo ======================================
    echo ✅ Tests completados exitosamente!
    echo ======================================
)

REM Mostrar comandos disponibles
echo.
echo 💡 Comandos disponibles:
echo    run_tests.bat unit         - Solo tests unitarios
echo    run_tests.bat integration  - Solo tests de integración
echo    run_tests.bat contract     - Solo tests de contrato
echo    run_tests.bat auth         - Tests de autenticación
echo    run_tests.bat reports      - Tests de reportes
echo    run_tests.bat incidents    - Tests de incidentes
echo    run_tests.bat fast         - Tests rápidos (sin slow^)
echo    run_tests.bat coverage     - Tests con reporte HTML
echo.

endlocal
