# Script para copiar datasets desde su ubicación original
# Ejecutar desde: ml/datasets/

$SOURCE_DIR = "C:\Users\wilki\Desktop\Proyecto de Grado\Datasets"
$DEST_DIR = ".\raw"

Write-Host "🔄 Copiando datasets a ml/datasets/raw/..." -ForegroundColor Cyan
Write-Host ""

# RDD2022 (tiene subcarpeta RDD_SPLIT)
Write-Host "📦 Copiando RDD2022..." -ForegroundColor Yellow
if (Test-Path "$SOURCE_DIR\RDD2022\RDD_SPLIT") {
    Copy-Item -Path "$SOURCE_DIR\RDD2022\RDD_SPLIT\*" -Destination "$DEST_DIR\RDD2022\" -Recurse -Force
    Write-Host "   ✅ RDD2022 copiado" -ForegroundColor Green
} elseif (Test-Path "$SOURCE_DIR\RDD2022") {
    Copy-Item -Path "$SOURCE_DIR\RDD2022\*" -Destination "$DEST_DIR\RDD2022\" -Recurse -Force
    Write-Host "   ✅ RDD2022 copiado" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  RDD2022 no encontrado" -ForegroundColor Red
}

# N-RDD2024
Write-Host "📦 Copiando N-RDD2024..." -ForegroundColor Yellow
if (Test-Path "$SOURCE_DIR\N-RDD2024.v2i.yolov8") {
    Copy-Item -Path "$SOURCE_DIR\N-RDD2024.v2i.yolov8\*" -Destination "$DEST_DIR\N-RDD2024\" -Recurse -Force
    Write-Host "   ✅ N-RDD2024 copiado" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  N-RDD2024 no encontrado" -ForegroundColor Red
}

# CRACK500 (pavement-crack-detection-master - solo necesitamos la carpeta tools con los datasets)
Write-Host "📦 Copiando CRACK500..." -ForegroundColor Yellow
if (Test-Path "$SOURCE_DIR\pavement-crack-detection-master\tools") {
    Copy-Item -Path "$SOURCE_DIR\pavement-crack-detection-master\tools\*" -Destination "$DEST_DIR\CRACK500\" -Recurse -Force
    Write-Host "   ✅ CRACK500 copiado" -ForegroundColor Green
} elseif (Test-Path "$SOURCE_DIR\pavement-crack-detection-master") {
    Copy-Item -Path "$SOURCE_DIR\pavement-crack-detection-master\*" -Destination "$DEST_DIR\CRACK500\" -Recurse -Force
    Write-Host "   ✅ CRACK500 copiado" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  CRACK500 no encontrado" -ForegroundColor Red
}

# CFD (CrackForest-dataset-master)
Write-Host "📦 Copiando CFD..." -ForegroundColor Yellow
if (Test-Path "$SOURCE_DIR\CrackForest-dataset-master") {
    Copy-Item -Path "$SOURCE_DIR\CrackForest-dataset-master\*" -Destination "$DEST_DIR\CFD\" -Recurse -Force
    Write-Host "   ✅ CFD copiado" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  CFD no encontrado" -ForegroundColor Red
}

# Pothole-600 (tiene subcarpeta pothole600)
Write-Host "📦 Copiando Pothole-600..." -ForegroundColor Yellow
if (Test-Path "$SOURCE_DIR\pothole600\pothole600") {
    Copy-Item -Path "$SOURCE_DIR\pothole600\pothole600\*" -Destination "$DEST_DIR\Pothole-600\" -Recurse -Force
    Write-Host "   ✅ Pothole-600 copiado" -ForegroundColor Green
} elseif (Test-Path "$SOURCE_DIR\pothole600") {
    Copy-Item -Path "$SOURCE_DIR\pothole600\*" -Destination "$DEST_DIR\Pothole-600\" -Recurse -Force
    Write-Host "   ✅ Pothole-600 copiado" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Pothole-600 no encontrado" -ForegroundColor Red
}

# RDD2020 (puede servir como dataset adicional)
Write-Host "📦 Copiando RDD2020 (adicional)..." -ForegroundColor Yellow
if (Test-Path "$SOURCE_DIR\RDD2020.v1i.yolov8") {
    # Crear carpeta para dataset adicional
    New-Item -Path "$DEST_DIR\RDD2020" -ItemType Directory -Force | Out-Null
    Copy-Item -Path "$SOURCE_DIR\RDD2020.v1i.yolov8\*" -Destination "$DEST_DIR\RDD2020\" -Recurse -Force
    Write-Host "   ✅ RDD2020 copiado (adicional)" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  RDD2020 no encontrado" -ForegroundColor Red
}

# Nota sobre SUT-Crack
Write-Host ""
Write-Host "ℹ️  Nota: No se encontró SUT-Crack en la carpeta de origen." -ForegroundColor Cyan
Write-Host "   Si tienes este dataset, cópialo manualmente a raw\SUT-Crack\" -ForegroundColor Cyan

Write-Host ""
Write-Host "✅ Proceso de copia completado!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Próximos pasos:" -ForegroundColor Yellow
Write-Host "   1. Verifica que los datasets se copiaron correctamente:" -ForegroundColor White
Write-Host "      Get-ChildItem .\raw\ -Recurse | Measure-Object -Property Length -Sum" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Convierte los datasets a formato YOLO:" -ForegroundColor White
Write-Host "      python organize_datasets.py --convert" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Genera estadísticas:" -ForegroundColor White
Write-Host "      python organize_datasets.py --stats" -ForegroundColor Gray
