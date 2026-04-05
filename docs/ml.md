# Modulo ML (Machine Learning)

## 1. Proposito del modulo

El modulo ML concentra todo el ciclo de vida de datos y modelos de inteligencia artificial para SIRCCD:

1. **Deteccion y clasificacion de danos viales**: modelos YOLO entrenados para identificar tipo de dano (bache, grieta, hundimiento, etc.) y estimar severidad.
2. **Anonimizacion de imagenes**: deteccion y difuminado de rostros y placas vehiculares para proteccion de privacidad.
3. **Embeddings visuales**: extraccion de vectores para alimentar el pipeline de deduplicacion del backend.
4. **Experimentacion y evaluacion**: notebooks, metricas y herramientas para iterar sobre modelos.
5. **Versionado de artefactos**: gestion de pesos, configuraciones y resultados de entrenamiento.

## 2. Stack tecnologico

| Componente | Tecnologia | Version | Proposito |
|-----------|------------|---------|-----------|
| Framework DL | PyTorch | 2.1+ | Motor de deep learning |
| Vision | torchvision | 0.16+ | Modelos pre-entrenados, transforms |
| Deteccion objetos | Ultralytics YOLO | 8.0+ | Deteccion y clasificacion de danos |
| Busqueda vectorial | FAISS | 1.7.4+ | Indexacion de embeddings para similitud |
| Augmentacion | Albumentations | 1.3+ | Transformaciones de datos para entrenamiento |
| Geoespacial | GeoPandas | 0.14+ | Manejo de datos de POIs y contexto geo |
| Procesamiento img | OpenCV + Pillow + scikit-image | - | Manipulacion y analisis de imagenes |
| Monitoring | TensorBoard | 2.14+ | Visualizacion de metricas de entrenamiento |
| Experiment tracking | Weights & Biases | 0.16+ | Tracking de experimentos y comparacion |
| Notebooks | Jupyter | 1.0+ | Experimentacion interactiva |
| Storage | MinIO SDK | 7.2+ | Descarga/subida de artefactos |

## 3. Arquitectura del pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    1. PREPARACION DE DATOS                    │
│  datasets/ → recoleccion, anotacion, augmentacion, split     │
├─────────────────────────────────────────────────────────────┤
│                    2. ENTRENAMIENTO                           │
│  train/ + notebooks/ → YOLO, ResNet, CLIP, anonimizacion     │
├─────────────────────────────────────────────────────────────┤
│                    3. EVALUACION                              │
│  inference/ → mAP, precision, recall, F1, confusion matrix   │
├─────────────────────────────────────────────────────────────┤
│                    4. VERSIONADO                              │
│  models/ + runs/ → exportacion de pesos, upload a MinIO      │
├─────────────────────────────────────────────────────────────┤
│                    5. INTEGRACION                             │
│  → Backend consume modelos para inferencia y embeddings       │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 Flujo detallado

```
Imagenes de danos viales (dataset)
    |
    v
Preparacion:
    ├── Anotacion con bounding boxes + clases
    ├── Augmentacion (Albumentations): flip, rotate, brightness, crop
    ├── Split train/val/test (70/20/10)
    └── Formato YOLO (images/ + labels/)
    |
    v
Entrenamiento:
    ├── Seleccion de arquitectura (YOLO11l, YOLO8x, etc.)
    ├── Configuracion de hiperparametros (lr, epochs, batch, imgsz)
    ├── Ejecucion en GPU (local, Colab, H100)
    ├── Monitoreo en tiempo real (TensorBoard / W&B)
    └── Checkpointing automatico (best.pt, last.pt)
    |
    v
Evaluacion:
    ├── Metricas: mAP@0.5, mAP@0.5:0.95, precision, recall, F1
    ├── Matriz de confusion por clase
    ├── Inferencia visual sobre test set
    ├── Comparacion con versiones anteriores
    └── Analisis de errores (falsos positivos/negativos)
    |
    v
Versionado:
    ├── Exportacion de best.pt
    ├── Upload a MinIO (scripts/upload_to_minio.py)
    ├── Registro de metricas y configuracion
    └── Tag en git si es release
    |
    v
Integracion con backend:
    ├── Actualizacion de ML_MODEL_PATH
    ├── Verificacion de inferencia en endpoint
    └── Recalibracion de umbrales si necesario
```

## 4. Mapa de archivos y directorios

### 4.1 Anonimizacion (`anonymization/`)

Sub-pipeline completo dedicado a la deteccion y difuminado de informacion personal en imagenes:

| Archivo | Descripcion |
|---------|-------------|
| `anonymization/train.py` | Script de entrenamiento del modelo de anonimizacion (deteccion de rostros y placas) |
| `anonymization/inference.py` | Script de inferencia: recibe imagen, detecta regiones sensibles, aplica blur |
| `anonymization/data.yaml` | Configuracion del dataset de anonimizacion: clases (face, license_plate), paths |
| `anonymization/scripts/` | Utilidades de preparacion: conversion de formatos, split de datos, validacion |
| `anonymization/notebooks/` | Notebooks de experimentacion y evaluacion del modelo de anonimizacion |
| `anonymization/docs/` | Guias tecnicas especificas del subflujo de anonimizacion |

### 4.2 Datasets (`datasets/`)

| Directorio | Descripcion |
|-----------|-------------|
| `datasets/` | Repositorio raiz de insumos y datos de entrenamiento |
| `datasets/pois_google/` | Datos de puntos de interes (POIs) extraidos de Google: escuelas, hospitales, gobierno. Usados para contexto geoespacial en priorizacion |

### 4.3 Entrenamiento (`train/` + `notebooks/`)

#### Scripts estructurados (`train/`)
Scripts de entrenamiento reproducible con configuracion parametrizada.

#### Notebooks de experimentacion (`notebooks/`)

| Notebook | Descripcion | Ambiente |
|----------|-------------|----------|
| `01_dataset_exploration.ipynb` | Analisis exploratorio del dataset: distribucion de clases, tamanos de imagen, balance, visualizacion de muestras | Local / Colab |
| `SIRCCD_Training_Colab.ipynb` | Entrenamiento base en Google Colab con GPU T4. Setup de drive, descarga de datos, entrenamiento, evaluacion | Colab |
| `SIRCCD_Training_v3_FromScratch.ipynb` | Entrenamiento desde cero con optimizaciones: learning rate scheduling, augmentacion agresiva, early stopping | Colab / Local |
| `SIRCCD_Training_v4_YOLO11l.ipynb` | Entrenamiento con arquitectura YOLO11 Large: mayor capacidad para clases dificiles | Colab |
| `SIRCCD_Training_v5_H100_Optimized.ipynb` | Optimizado para GPU NVIDIA H100: mixed precision, gradient accumulation, batch size grande | Cloud (H100) |
| `SIRCCD_Anonymization_Training.ipynb` | Entrenamiento del modelo de anonimizacion: deteccion de rostros y placas | Colab |

### 4.4 Inferencia y evaluacion (`inference/`)

Scripts y utilidades para evaluar modelos entrenados:
- Inferencia sobre imagenes individuales y lotes
- Generacion de visualizaciones con bounding boxes
- Calculo de metricas sobre test set
- Comparacion entre versiones de modelos

### 4.5 Embeddings (`embeddings/`)

Utilidades de extraccion de vectores visuales:
- Extraccion con ResNet50 (2048 dimensiones)
- Extraccion con CLIP (512 dimensiones)
- Evaluacion comparativa de calidad de embeddings
- Herramientas de benchmarking

### 4.6 Deduplicacion experimental (`deduplication/`)

Soporte experimental de deduplicacion desde el lado ML:
- Prototipos de pipeline de deduplicacion
- Evaluacion de diferentes estrategias de fusion
- Calibracion de umbrales

### 4.7 Artefactos y configuracion

| Directorio | Descripcion |
|-----------|-------------|
| `models/` | Modelos entrenados exportados: `best.pt` (mejores pesos), `last.pt` (ultimos pesos) |
| `runs/` | Salidas de ejecucion de entrenamientos: logs, metricas, checkpoints, graficas |
| `configs/` | Configuraciones de entrenamiento: hiperparametros, data.yaml, model configs |

### 4.8 Scripts de utileria (`scripts/`)

| Archivo | Descripcion |
|---------|-------------|
| `scripts/verify_environment.py` | Verifica que el entorno de ML este correctamente configurado: CUDA, PyTorch, dependencias |
| `scripts/download_from_minio.py` | Descarga artefactos (datasets, modelos) desde MinIO al entorno local |
| `scripts/upload_to_minio.py` | Sube artefactos (modelos entrenados, resultados) a MinIO |
| `scripts/utils/` | Helpers compartidos: formateo, logging, IO |

### 4.9 Documentacion interna ML (`docs/`)

Guias operativas especificas del modulo ML:

| Archivo | Descripcion |
|---------|-------------|
| `docs/M-01_ENVIRONMENT_SETUP.md` | Guia completa de setup de entorno: Python, CUDA, PyTorch, dependencias |
| `docs/GUIA_*` | Guias paso a paso para entrenamiento en Google Colab |
| `docs/CHECKLIST_COLAB.md` | Checklist pre-entrenamiento en Colab: verificacion de GPU, datos, configuracion |
| `docs/V3_TRAINING_OPTIMIZATION.md` | Documentacion de optimizaciones aplicadas en v3: LR scheduling, augmentacion, regularizacion |
| `docs/CLOUD_TRAINING.md` | Guia de entrenamiento en la nube: setup, costos, recomendaciones |
| `docs/PYTHON_314_COMPATIBILITY_ISSUE.md` | Problemas de compatibilidad con Python 3.14: dependencias afectadas, workarounds |

## 5. Modelos de clasificacion

### 5.1 Clasificacion de danos viales (YOLO)

**Arquitectura**: YOLO11l (Large) - seleccionada por balance entre precision y velocidad.

**Clases detectadas**:
- `pothole` - Bache
- `crack` - Grieta
- `subsidence` - Hundimiento
- `patch` - Parche deteriorado
- `other` - Otro tipo de dano

**Salida por deteccion**:
```python
{
    "class": "pothole",
    "confidence": 0.92,
    "bbox": [x1, y1, x2, y2],  # Bounding box
    "severity": 0.78            # Score de severidad estimado
}
```

### 5.2 Modelo de anonimizacion

**Arquitectura**: YOLO (variante ligera)

**Clases detectadas**:
- `face` - Rostro humano
- `license_plate` - Placa vehicular

**Post-procesamiento**: Gaussian blur sobre regiones detectadas.

### 5.3 Modelos de embeddings

**ResNet50** (para deduplicacion):
- Dimension: 2048
- Pre-entrenado en ImageNet
- Feature extraction de la penultima capa

**CLIP** (alternativa):
- Dimension: 512
- Pre-entrenado multimodal (imagen + texto)
- Mejor generalizacion semantica

## 6. Metricas de evaluacion

| Metrica | Descripcion | Objetivo |
|---------|-------------|----------|
| mAP@0.5 | Mean Average Precision a IoU 0.5 | > 0.80 |
| mAP@0.5:0.95 | mAP promediado en IoU 0.5 a 0.95 | > 0.60 |
| Precision | Correctness de detecciones positivas | > 0.85 |
| Recall | Cobertura de danos reales detectados | > 0.80 |
| F1 Score | Media armonica de precision y recall | > 0.82 |
| Inference time | Tiempo de inferencia por imagen | < 100ms (GPU) |

## 7. Configuracion del entorno

### 7.1 Dependencias (`requirements-training.txt`)

```
torch>=2.1.0
torchvision>=0.16.0
ultralytics>=8.0.0
faiss-cpu>=1.7.4
jupyter>=1.0.0
tensorboard>=2.14.0
wandb>=0.16.0
albumentations>=1.3.0
geopandas>=0.14.0
opencv-python>=4.8.0
Pillow>=10.0.0
scikit-image>=0.21.0
minio>=7.2.0
matplotlib>=3.8.0
numpy>=1.24.0
pandas>=2.0.0
```

### 7.2 Variables de entorno (`.env.template`)

```env
# MinIO para artefactos
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sirccd-ml

# W&B (opcional)
WANDB_API_KEY=your-key
WANDB_PROJECT=sirccd

# Entrenamiento
CUDA_VISIBLE_DEVICES=0
```

### 7.3 Compatibilidad de Python

**Versiones recomendadas**: Python 3.10, 3.11 o 3.12.

**Python 3.14**: NO compatible. Documentado en `docs/PYTHON_314_COMPATIBILITY_ISSUE.md`. Varias dependencias de ML (torch, ultralytics) aun no soportan esta version.

## 8. Ejecucion

### 8.1 Setup del entorno

```powershell
cd ml
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-training.txt
python scripts/verify_environment.py    # Verificar instalacion
```

### 8.2 Entrenamiento local

```powershell
cd ml
python train/train.py --config configs/yolo11l.yaml
```

### 8.3 Entrenamiento en Colab

1. Abrir notebook correspondiente en Google Colab
2. Seguir `docs/CHECKLIST_COLAB.md` para verificacion pre-entrenamiento
3. Ejecutar celdas secuencialmente
4. Descargar artefactos al finalizar

### 8.4 Inferencia

```powershell
cd ml
python inference/predict.py --image path/to/image.jpg --model models/best.pt
```

### 8.5 Gestion de artefactos con MinIO

```powershell
# Descargar modelo entrenado
python scripts/download_from_minio.py --bucket sirccd-ml --key models/best.pt --output models/

# Subir modelo nuevo
python scripts/upload_to_minio.py --bucket sirccd-ml --file models/best.pt --key models/best_v2.pt
```

## 9. Flujo operativo recomendado

1. **Validar entorno**: ejecutar `scripts/verify_environment.py` para confirmar GPU, dependencias y conectividad.
2. **Preparar datos**: asegurar dataset anotado, split correcto y augmentacion configurada.
3. **Entrenar**: ejecutar entrenamiento (local o Colab) con monitoreo activo en TensorBoard/W&B.
4. **Evaluar**: revisar metricas (mAP, precision, recall), comparar con version anterior.
5. **Versionar**: exportar `best.pt`, registrar metricas, subir a MinIO.
6. **Integrar**: actualizar `ML_MODEL_PATH` en backend, verificar inferencia end-to-end.
7. **Recalibrar**: si cambian metricas de deduplicacion, ajustar umbrales.

## 10. Integraciones

### 10.1 Con backend

| Artefacto | Destino | Uso |
|-----------|---------|-----|
| `best.pt` (YOLO) | `backend/models/` o MinIO | Clasificacion de danos en ml_service.py |
| `anonymizer.pt` | `backend/models/` o MinIO | Anonimizacion en anonymizer.py |
| Configuracion de inferencia | Variables de entorno backend | Umbrales, rutas de modelos |
| Embeddings (ResNet/CLIP) | deduplication_service.py | Extraccion de vectores para FAISS |

### 10.2 Con MinIO

- **Descarga**: datasets, modelos pre-entrenados, checkpoints de versiones anteriores.
- **Subida**: modelos entrenados, resultados de evaluacion, logs de entrenamiento.
