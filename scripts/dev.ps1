#!/usr/bin/env pwsh
# ============================================================
# SIRCCD - Script de desarrollo local
# Inicia Backend (FastAPI) + Frontend (Next.js)
# Uso: .\scripts\dev.ps1
# ============================================================

$ROOT = Split-Path -Parent $PSScriptRoot

function Write-Step { param($msg) Write-Host "`n  >> $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function Write-Err  { param($msg) Write-Host "  [X]  $msg" -ForegroundColor Red }

Write-Host "`n============================================================" -ForegroundColor Magenta
Write-Host "  SIRCCD - Entorno de desarrollo local" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta

# -- 1. Matar procesos existentes en los puertos ---------------
Write-Step "Liberando puertos 8000 y 3000..."

foreach ($port in @(8000, 3000)) {
    $pids = netstat -ano 2>$null |
        Select-String ":$port\s" |
        ForEach-Object { ($_ -split '\s+')[-1] } |
        Where-Object { $_ -match '^\d+$' } |
        Sort-Object -Unique

    foreach ($p in $pids) {
        try {
            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
            Write-OK "Proceso $p en puerto $port detenido"
        } catch {}
    }
}

Start-Sleep -Seconds 1

# -- 2. Verificar entorno virtual --------------------------------
Write-Step "Verificando entorno virtual Python..."

$venvPython = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Err "No se encontro .venv en $ROOT"
    Write-Err "Ejecuta: python -m venv .venv && .venv\Scripts\pip install -r backend\requirements.txt"
    exit 1
}
Write-OK "Entorno virtual: $venvPython"

# -- 3. Verificar node_modules -----------------------------------
Write-Step "Verificando node_modules del frontend..."

$nodeModules = Join-Path $ROOT "frontend\node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Warn "node_modules no encontrado. Instalando dependencias..."
    Push-Location (Join-Path $ROOT "frontend")
    npm install
    Pop-Location
}
Write-OK "node_modules listo"

# -- 4. Iniciar Backend ------------------------------------------
Write-Step "Iniciando Backend FastAPI en http://localhost:8000 ..."

$backendDir = Join-Path $ROOT "backend"
$backendLog = Join-Path $backendDir "dev.log"
$backendErr = Join-Path $backendDir "dev.err.log"

$backendJob = Start-Process -FilePath $venvPython `
    -ArgumentList "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory $backendDir `
    -RedirectStandardOutput $backendLog `
    -RedirectStandardError  $backendErr `
    -NoNewWindow `
    -PassThru

Write-OK "Backend PID: $($backendJob.Id)  - log: backend\dev.log"

# -- 5. Esperar a que el backend levante -------------------------
Write-Step "Esperando que el backend responda..."

$maxWait = 25
$waited  = 0
$up      = $false

while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 1
    $waited++
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" `
             -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $up = $true; break }
    } catch {}
    Write-Host "    espera $waited/$maxWait s..." -ForegroundColor DarkGray
}

if ($up) {
    Write-OK "Backend listo  -->  http://localhost:8000/api/v1/docs"
} else {
    Write-Warn "Backend no respondio en ${maxWait}s. Revisa backend\dev.err.log"
    if (Test-Path $backendErr) {
        Write-Host (Get-Content $backendErr -Tail 10 | Out-String) -ForegroundColor DarkGray
    }
}

# -- 6. Iniciar Frontend -----------------------------------------
Write-Step "Iniciando Frontend Next.js en http://localhost:3000 ..."

$frontendDir = Join-Path $ROOT "frontend"
$frontendLog = Join-Path $frontendDir "dev.log"

$frontendJob = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", "npm run dev > `"$frontendLog`" 2>&1" `
    -WorkingDirectory $frontendDir `
    -NoNewWindow `
    -PassThru

Write-OK "Frontend PID: $($frontendJob.Id)  - log: frontend\dev.log"

# -- 7. Esperar a que Next.js levante ----------------------------
Write-Step "Esperando que el frontend responda..."

$maxWait = 35
$waited  = 0
$up      = $false

while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 1
    $waited++
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:3000" `
             -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -in @(200, 307, 308)) { $up = $true; break }
    } catch {}
    Write-Host "    espera $waited/$maxWait s..." -ForegroundColor DarkGray
}

if ($up) {
    Write-OK "Frontend listo  -->  http://localhost:3000"
} else {
    Write-Warn "Frontend no respondio en ${maxWait}s (puede seguir compilando)."
    Write-Warn "Revisa frontend\dev.log para detalles."
}

# -- 8. Resumen --------------------------------------------------
Write-Host "`n============================================================" -ForegroundColor Magenta
Write-Host "  Servicios iniciados" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  Backend API  -->  http://localhost:8000/api/v1/docs" -ForegroundColor White
Write-Host "  Frontend     -->  http://localhost:3000" -ForegroundColor White
Write-Host "  Nuevo reporte -> http://localhost:3000/dashboard/reports/new" -ForegroundColor White
Write-Host ""
Write-Host "  PIDs  - Backend: $($backendJob.Id)  Frontend: $($frontendJob.Id)" -ForegroundColor DarkGray
Write-Host "  Logs  - backend\dev.log  |  frontend\dev.log" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Para detener: .\scripts\dev-stop.ps1" -ForegroundColor DarkGray
Write-Host "  Ctrl+C aqui detiene ambos procesos." -ForegroundColor DarkGray
Write-Host "============================================================`n" -ForegroundColor Magenta

# -- 9. Mantener consola activa hasta Ctrl+C ---------------------
try {
    while ($true) {
        Start-Sleep -Seconds 5
        if ($backendJob.HasExited) {
            Write-Warn "Backend detenido (exit: $($backendJob.ExitCode)). Revisa backend\dev.err.log"
        }
        if ($frontendJob.HasExited) {
            Write-Warn "Frontend detenido (exit: $($frontendJob.ExitCode)). Revisa frontend\dev.log"
        }
    }
} finally {
    Write-Host "`n  Deteniendo servicios..." -ForegroundColor Yellow
    Stop-Process -Id $backendJob.Id  -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendJob.Id -Force -ErrorAction SilentlyContinue
    Write-OK "Servicios detenidos."
}
