#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Prueba automatizada de P-01 (Heatmap por densidad de incidentes).

.DESCRIPTION
  Valida por API que el endpoint de heatmap:
  1) Existe y responde autenticado
  2) Soporta frequency, severity y age
  3) Retorna estructura esperada: points, weight_by, count

.USAGE
  .\test_p01_heatmap.ps1 -Username "admin@sirccd.com" -Password "tu_password"

  o con token ya generado:
  .\test_p01_heatmap.ps1 -Token "eyJ..."

.NOTES
  - Requiere backend levantado en http://localhost:8000 (o ajustar -BaseUrl)
  - Endpoint probado: GET /api/v1/incidents/heatmap?weight_by={frequency|severity|age}
#>

[CmdletBinding()]
param(
    [string]$BaseUrl = "http://localhost:8000/api/v1",
    [string]$Username,
    [string]$Password,
    [string]$Token
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "`n>> $Message" -ForegroundColor Cyan
}

function Write-Ok([string]$Message) {
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn([string]$Message) {
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Fail([string]$Message) {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Assert-Field(
    [Parameter(Mandatory = $true)]$Object,
    [Parameter(Mandatory = $true)][string]$FieldName
) {
    if (-not ($Object.PSObject.Properties.Name -contains $FieldName)) {
        throw "Campo faltante en respuesta: $FieldName"
    }
}

try {
    Write-Host "===============================================" -ForegroundColor Magenta
    Write-Host " P-01 Heatmap API Test" -ForegroundColor Magenta
    Write-Host "===============================================" -ForegroundColor Magenta

    Write-Step "Validando disponibilidad del backend"
    $healthUrl = "$BaseUrl/health"
    $health = Invoke-RestMethod -Method Get -Uri $healthUrl -TimeoutSec 15
    if (-not $health) {
        throw "El endpoint de health no devolvio datos"
    }
    Write-Ok "Backend disponible en $BaseUrl"

    if ([string]::IsNullOrWhiteSpace($Token)) {
        Write-Step "Autenticando para obtener token JWT"

        if ([string]::IsNullOrWhiteSpace($Username)) {
            $Username = Read-Host "Usuario (username o email)"
        }
        if ([string]::IsNullOrWhiteSpace($Password)) {
            $secure = Read-Host "Password" -AsSecureString
            $Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
            )
        }

        if ([string]::IsNullOrWhiteSpace($Username) -or [string]::IsNullOrWhiteSpace($Password)) {
            throw "Debes proporcionar Username y Password, o usar -Token"
        }

        $loginBody = @{
            username = $Username
            password = $Password
        } | ConvertTo-Json

        $loginUrl = "$BaseUrl/auth/login"
        $loginResponse = Invoke-RestMethod -Method Post -Uri $loginUrl -Body $loginBody -ContentType "application/json" -TimeoutSec 20

        if (-not $loginResponse.access_token) {
            throw "Login exitoso pero no se recibio access_token"
        }

        $Token = $loginResponse.access_token
        Write-Ok "Autenticacion completada"
    }
    else {
        Write-Ok "Usando token proporcionado por parametro"
    }

    $headers = @{ Authorization = "Bearer $Token" }

    Write-Step "Probando modos de heatmap: frequency, severity, age"
    $weights = @("frequency", "severity", "age")
    $results = @()
    $allPassed = $true

    foreach ($weight in $weights) {
        try {
            $url = "$BaseUrl/incidents/heatmap?weight_by=$weight"
            $response = Invoke-RestMethod -Method Get -Uri $url -Headers $headers -TimeoutSec 20

            Assert-Field -Object $response -FieldName "points"
            Assert-Field -Object $response -FieldName "weight_by"
            Assert-Field -Object $response -FieldName "count"

            if ($response.weight_by -ne $weight) {
                throw "weight_by devuelto '$($response.weight_by)' no coincide con '$weight'"
            }

            $points = @($response.points)
            $pointsCount = $points.Count

            if ([int]$response.count -ne $pointsCount) {
                throw "count=$($response.count) no coincide con points.Count=$pointsCount"
            }

            # Si hay puntos, validar forma [lat, lng, intensity]
            if ($pointsCount -gt 0) {
                $firstPoint = @($points[0])
                if ($firstPoint.Count -lt 3) {
                    throw "El primer punto no contiene [lat, lng, intensity]"
                }
            }

            $results += [PSCustomObject]@{
                mode = $weight
                status = "PASS"
                points = $pointsCount
                weight_by = $response.weight_by
            }

            Write-Ok "Modo '$weight' validado (points=$pointsCount)"
        }
        catch {
            $allPassed = $false
            $results += [PSCustomObject]@{
                mode = $weight
                status = "FAIL"
                points = "-"
                weight_by = "-"
            }
            Write-Fail "Modo '$weight' fallo: $($_.Exception.Message)"
        }
    }

    Write-Step "Resumen"
    $results | Format-Table -AutoSize

    $totalPoints = ($results | Where-Object { $_.status -eq "PASS" } | Measure-Object -Property points -Sum).Sum
    if (-not $totalPoints) { $totalPoints = 0 }

    if ($allPassed) {
        Write-Ok "P-01 API PASS: endpoint heatmap funcional en los 3 modos"

        if ($totalPoints -eq 0) {
            Write-Warn "No hay incidentes para pintar (points=0). La API funciona, pero falta data para validar visualmente el mapa."
        }

        exit 0
    }
    else {
        Write-Fail "P-01 API FAIL: uno o mas modos no cumplieron validacion"
        exit 1
    }
}
catch {
    Write-Fail $_.Exception.Message
    exit 1
}
