# Dataset SIRCCD - Road Damage Detection

Este directorio contiene todos los datasets, scripts de procesamiento y documentación relacionada con el conjunto de datos de detección de daños viales.

## 📁 Estructura del Directorio

```
ml/datasets/
├── raw/                      # Datasets originales sin procesar
├── processed/                # Datasets procesados y limpios
│   ├── cleaned/             # Dataset balanceado y limpio
│   ├── combined/            # Datasets combinados
│   └── split/               # Dataset dividido en train/val/test
│       ├── images/          # Imágenes por split
│       └── labels/          # Anotaciones YOLO por split
├── metadata/                 # Metadatos y archivos de configuración
├── pois_google/             # Puntos de interés (POIs) de Google Places
├── scripts/                 # Scripts de procesamiento
└── docs/                    # Documentación de procesos
```

## 🔧 Scripts Disponibles

### Procesamiento de Datos
- **`organize_datasets.py`** - Organiza y unifica datasets de diferentes fuentes
- **`process_pothole600.py`** - Procesa el dataset Pothole-600
- **`clean_and_balance.py`** - Limpia y balancea el dataset combinado
- **`split_dataset.py`** - Divide el dataset en train/val/test con estratificación
- **`validate_split.py`** - Valida la división del dataset

### Etiquetado y Catalogación
- **`label_severity.py`** - Etiqueta la severidad de los daños (baja/media/alta)
- **`catalog_pois.py`** - Descarga POIs desde OpenStreetMap (obsoleto)
- **`google_places_pois.py`** - Descarga POIs desde Google Places API
- **`generate_theoretical_risk_zones.py`** - Genera zonas de riesgo teóricas

### Almacenamiento y Privacidad
- **`upload_to_minio.py`** - Ingesta el dataset a MinIO con metadatos y versionado
- **`anonymize_dataset.py`** - Elimina metadatos EXIF sensibles completamente
- **`detect_sensitive_content.py`** - Detecta rostros/placas (funcional con .venv-cv)
- **`blur_detected_faces.py`** - Difumina rostros detectados con Gaussian Blur
- **`verify_anonymization.py`** - Verifica que la anonimización se completó correctamente

## 📄 Documentación

### Reportes de Procesos
- **`CONVERSION_SUMMARY.md`** - Resumen de conversión de formatos
- **`CLEANING_REPORT.md`** - Reporte de limpieza y balanceo
- **`SPLIT_REPORT.md`** - Reporte de división del dataset
- **`SEVERITY_REPORT.md`** - Reporte de etiquetado de severidad
- **`D-07_MINIO_INGESTION.md`** - Guía de ingesta a MinIO
- **`D-08_ANONYMIZATION.md`** - Guía de anonimización y protección de privacidad

### Configuración y Criterios
- **`augmentation_config.md`** - Configuración de data augmentation
- **`severity_criteria.md`** - Criterios de clasificación de severidad

## 📊 Dataset Actual (v1.0.0)

- **Total de imágenes**: 58,209
- **Clases**: bache (0), grieta (2)
- **Divisiones**:
  - Train: 40,745 imágenes (70%)
  - Val: 11,641 imágenes (20%)
  - Test: 5,823 imágenes (10%)
- **Fuentes**: RDD2022, RDD2020, N-RDD2024, Pothole-600
- **Formato**: YOLO con etiquetas de severidad
- **Seed**: 42 (reproducibilidad)

## 🗺️ Puntos de Interés (POIs)

Se descargaron **328 POIs** de Santiago de los Caballeros, RD:
- Escuelas: 60
- Universidades: 60
- Hospitales: 60
- Clínicas: 60
- Estaciones de bomberos: 19
- Estaciones de policía: 49
- Puentes: 20

## 🚀 Uso Rápido

### 1. Procesar Dataset Completo
```bash
# Desde el directorio ml/datasets/

# 1. Organizar datasets crudos
python scripts/organize_datasets.py

# 2. Limpiar y balancear
python scripts/clean_and_balance.py

# 3. Dividir en train/val/test
python scripts/split_dataset.py

# 4. Validar división
python scripts/validate_split.py

# 5. Etiquetar severidad
python scripts/label_severity.py
```

### 2. Descargar POIs
```bash
# Usando Google Places API
python scripts/google_places_pois.py
```

### 3. Certificar Privacidad
```bash
# Generar certificación GDPR/CCPA
python scripts/certify_privacy.py
```

### 4. Subir a MinIO
```bash
# Desde el directorio raíz del monorepo

# Iniciar contenedor MinIO
docker-compose -f docker-compose.minio.yml up -d

# Ingestar dataset
python ml/datasets/scripts/upload_to_minio.py
```

## 🔐 Configuración MinIO

- **Endpoint**: http://localhost:9000
- **Consola**: http://localhost:9001
- **Bucket**: sirccd-datasets
- **Versión actual**: v1.0.0

## 📝 Notas

- Todos los scripts asumen que se ejecutan desde el directorio raíz del proyecto
- Los datasets raw deben colocarse en `ml/datasets/raw/` antes de procesarlos
- Las rutas usan Path de pathlib para compatibilidad multiplataforma
- El seed 42 se usa en todos los procesos aleatorios para reproducibilidad
