#!/usr/bin/env pwsh
# Detiene todos los procesos en puertos 8000 y 3000

Write-Host "`n  Deteniendo backend (8000) y frontend (3000)..." -ForegroundColor Yellow

foreach ($port in @(8000, 3000)) {
    $pids = netstat -ano 2>$null |
        Select-String ":$port\s" |
        ForEach-Object { ($_ -split '\s+')[-1] } |
        Where-Object { $_ -match '^\d+$' } |
        Sort-Object -Unique

    foreach ($p in $pids) {
        try {
            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Proceso $p (puerto $port) detenido" -ForegroundColor Green
        } catch {
            Write-Host "  [!] No se pudo detener PID $p" -ForegroundColor Yellow
        }
    }
}

Write-Host "  [OK] Listo.`n" -ForegroundColor Green
