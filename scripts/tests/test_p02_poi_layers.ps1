#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Prueba automatizada de P-02 (Capas de POIs y zonas de riesgo peatonal).

.DESCRIPTION
  Valida por API que el endpoint de POIs:
  1) Existe y responde autenticado
  2) Soporta categorías school, hospital, fire_station, community_center
  3) Retorna estructura esperada de POIs
  4) Expone buffers peatonales en rango 50-200m

.USAGE
  .\test_p02_poi_layers.ps1
  .\test_p02_poi_layers.ps1 -Username "admin@sirccd.com" -Password "tu_password"
  .\test_p02_poi_layers.ps1 -Token "eyJ..."

.NOTES
  - Requiere backend levantado en http://localhost:8000 (o ajustar -BaseUrl)
  - Endpoint probado: GET /api/v1/pois
#>

[CmdletBinding()]
param(
    [string]$BaseUrl = "http://localhost:8000/api/v1",
    [string]$Username,
    [string]$Password,
    [string]$Token,
    [switch]$NoAutoRegister
)

$ErrorActionPreference = "Stop"

$requiredCategories = @("school", "hospital", "fire_station", "community_center")

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

function Invoke-Login([string]$Url, [string]$User, [string]$Pass) {
    $loginBody = @{
        username = $User
        password = $Pass
    } | ConvertTo-Json

    return Invoke-RestMethod -Method Post -Uri $Url -Body $loginBody -ContentType "application/json" -TimeoutSec 20
}

try {
    Write-Host "===============================================" -ForegroundColor Magenta
    Write-Host " P-02 POIs + Buffers API Test" -ForegroundColor Magenta
    Write-Host "===============================================" -ForegroundColor Magenta

    Write-Step "Validando disponibilidad del backend"
    $healthUrl = "$BaseUrl/health"
    $health = Invoke-RestMethod -Method Get -Uri $healthUrl -TimeoutSec 15
    if (-not $health) {
        throw "El endpoint de health no devolvio datos"
    }
    Write-Ok "Backend disponible en $BaseUrl"

    if ([string]::IsNullOrWhiteSpace($Token)) {
        Write-Step "Obteniendo token JWT"

        if ([string]::IsNullOrWhiteSpace($Username) -or [string]::IsNullOrWhiteSpace($Password)) {
            if ($NoAutoRegister) {
                throw "Sin token ni credenciales, y -NoAutoRegister activo."
            }

            $stamp = Get-Date -Format "yyyyMMddHHmmss"
            $Username = "p02user$stamp"
            $email = "$Username@sirccd.com"
            $Password = "P02Pass123!"

            Write-Step "Registrando usuario temporal para pruebas"
            $registerBody = @{
                email = $email
                username = $Username
                password = $Password
                full_name = "P02 Test User"
            } | ConvertTo-Json

            $registerUrl = "$BaseUrl/auth/register"
            try {
                $null = Invoke-RestMethod -Method Post -Uri $registerUrl -Body $registerBody -ContentType "application/json" -TimeoutSec 20
                Write-Ok "Usuario temporal registrado: $Username"
            }
            catch {
                # Si el usuario ya existe por alguna ejecución previa, continuar con login.
                if ($_.Exception.Response -and ($_.Exception.Response.StatusCode.value__ -eq 400)) {
                    Write-Warn "Usuario temporal ya existente, continuando con login: $Username"
                }
                else {
                    throw
                }
            }
        }

        $loginUrl = "$BaseUrl/auth/login"
        $loginResponse = Invoke-Login -Url $loginUrl -User $Username -Pass $Password

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

    Write-Step "Validando endpoint base de capas POI"
    $basePoiUrl = "$BaseUrl/pois/"
    $response = Invoke-RestMethod -Method Get -Uri $basePoiUrl -Headers $headers -TimeoutSec 20

    Assert-Field -Object $response -FieldName "total"
    Assert-Field -Object $response -FieldName "pois"
    Assert-Field -Object $response -FieldName "categories"
    Assert-Field -Object $response -FieldName "min_buffer_m"
    Assert-Field -Object $response -FieldName "default_buffer_m"
    Assert-Field -Object $response -FieldName "max_buffer_m"

    if (($response.min_buffer_m -lt 50) -or ($response.max_buffer_m -gt 200)) {
        throw "Rango de buffers invalido: min=$($response.min_buffer_m), max=$($response.max_buffer_m)"
    }
    if (($response.default_buffer_m -lt $response.min_buffer_m) -or ($response.default_buffer_m -gt $response.max_buffer_m)) {
        throw "default_buffer_m fuera de rango: $($response.default_buffer_m)"
    }

    Write-Ok "Contrato base valido (total=$($response.total), buffers=$($response.min_buffer_m)-$($response.max_buffer_m)m)"

    $pois = @($response.pois)
    $invalidPoiCount = 0
    foreach ($poi in $pois) {
        foreach ($requiredField in @("id", "name", "category", "latitude", "longitude", "recommended_buffer_m")) {
            if (-not ($poi.PSObject.Properties.Name -contains $requiredField)) {
                $invalidPoiCount += 1
                break
            }
        }
        if (($poi.recommended_buffer_m -lt 50) -or ($poi.recommended_buffer_m -gt 200)) {
            $invalidPoiCount += 1
        }
    }

    if ($invalidPoiCount -gt 0) {
        throw "Se detectaron $invalidPoiCount POIs con estructura o buffer invalido"
    }
    Write-Ok "Estructura de POIs valida"

    Write-Step "Validando filtros por categoria"
    $results = @()
    $allPassed = $true

    foreach ($category in $requiredCategories) {
        try {
            $url = "$BaseUrl/pois/?categories=$category"
            $catResponse = Invoke-RestMethod -Method Get -Uri $url -Headers $headers -TimeoutSec 20

            Assert-Field -Object $catResponse -FieldName "pois"
            Assert-Field -Object $catResponse -FieldName "categories"

            $catPois = @($catResponse.pois)
            $wrongCategory = $catPois | Where-Object { $_.category -ne $category }
            if ($wrongCategory.Count -gt 0) {
                throw "Retorno contiene categorias distintas a '$category'"
            }

            $results += [PSCustomObject]@{
                category = $category
                status = "PASS"
                points = $catPois.Count
            }
            Write-Ok "Categoria '$category' valida (points=$($catPois.Count))"
        }
        catch {
            $allPassed = $false
            $results += [PSCustomObject]@{
                category = $category
                status = "FAIL"
                points = "-"
            }
            Write-Fail "Categoria '$category' fallo: $($_.Exception.Message)"
        }
    }

    Write-Step "Resumen"
    $results | Format-Table -AutoSize

    $totalPoints = ($results | Where-Object { $_.status -eq "PASS" } | Measure-Object -Property points -Sum).Sum
    if (-not $totalPoints) { $totalPoints = 0 }

    if ($allPassed) {
        Write-Ok "P-02 API PASS: capas POI y buffers funcionales"
        if ($totalPoints -eq 0) {
            Write-Warn "No hay POIs cargados para visualizar, pero la API y filtros funcionan correctamente."
        }
        exit 0
    }
    else {
        Write-Fail "P-02 API FAIL: una o mas validaciones de categoria fallaron"
        exit 1
    }
}
catch {
    Write-Fail $_.Exception.Message
    exit 1
}
