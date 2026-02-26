# Scripts de inicio rápido para SIRCCD Backend

## start.bat (Windows)
@echo off
echo ========================================
echo SIRCCD Backend - Inicio Rapido
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python no encontrado
    exit /b 1
)

REM Activar entorno virtual
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [OK] Entorno virtual activado
) else (
    echo [!] Creando entorno virtual...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

REM Verificar .env
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] Archivo .env creado
        echo [!] Edita .env con tus configuraciones
    )
)

REM Instalar dependencias
echo.
echo Instalando dependencias...
pip install -r requirements.txt

REM Iniciar servidor
echo.
echo ========================================
echo Iniciando servidor...
echo   API: http://localhost:8000
echo   Docs: http://localhost:8000/api/v1/docs
echo ========================================
echo.
python main.py
