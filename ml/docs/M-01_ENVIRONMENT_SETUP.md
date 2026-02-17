# M-01: Preparación de Entorno de Entrenamiento

## Objetivo

Configurar un entorno de desarrollo completo para entrenamiento de modelos de detección de daños viales, incluyendo todas las dependencias necesarias para PyTorch, YOLOv8, experimentación y visualización.

## Entorno Virtual

### Tipo de Entorno
**Python venv** (`.venv` en el directorio raíz del monorepo)

**Alternativa considerada**: Conda
- ❌ No elegido: Mayor overhead de gestión, duplicación de paquetes
- ✅ venv: Más ligero, integración directa con pip, mejor para CI/CD

### Creación del Entorno

```bash
# Desde el directorio raíz del monorepo
cd C:\Users\wilki\sirccd-monorepo\sirccd-monorepo

# Crear entorno virtual (ya creado)
python -m venv .venv

# Activar entorno (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activar entorno (Windows CMD)
.venv\Scripts\activate.bat

# Activar entorno (Linux/Mac)
source .venv/bin/activate
```

## Dependencias Instaladas

### 1. Deep Learning Framework

#### PyTorch (`torch>=2.1.0`)
- **Propósito**: Framework principal de deep learning
- **Componentes**:
  - `torch`: Core de PyTorch
  - `torchvision>=0.16.0`: Transformaciones y modelos de visión
  - `torchaudio>=2.1.0`: Procesamiento de audio (opcional)

**Verificación**:
```python
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda if torch.cuda.is_available() else 'N/A'}")
```

### 2. Object Detection

#### Ultralytics (`ultralytics>=8.0.0`)
- **Propósito**: YOLOv8 para detección de objetos
- **Características**:
  - Entrenamiento simplificado
  - Inferencia rápida
  - Export a múltiples formatos (ONNX, TensorRT, CoreML)
  - CLI integrada

**Verificación**:
```python
from ultralytics import YOLO
print(f"Ultralytics YOLOv8 disponible")
```

### 3. Data Augmentation

#### Albumentations (`albumentations>=1.3.0`)
- **Propósito**: Augmentación avanzada de imágenes
- **Técnicas soportadas**:
  - Transformaciones geométricas (flip, rotate, crop)
  - Transformaciones de color (brightness, contrast)
  - Efectos climáticos (rain, fog, sun flare)
  - Ruido y blur

**Verificación**:
```python
import albumentations as A
print(f"Albumentations version: {A.__version__}")
```

### 4. Jupyter Notebooks

#### Componentes
- `jupyter>=1.0.0`: Meta-paquete de Jupyter
- `notebook>=7.0.0`: Jupyter Notebook clásico
- `ipykernel>=6.25.0`: Kernel de Python para Jupyter
- `ipywidgets>=8.1.0`: Widgets interactivos

**Verificación**:
```bash
jupyter --version
jupyter notebook list
```

### 5. Experiment Tracking

#### TensorBoard (`tensorboard>=2.14.0`)
- **Propósito**: Visualización de métricas de entrenamiento
- **Características**:
  - Gráficas de loss y métricas
  - Visualización de embeddings
  - Histogramas de pesos

**Uso**:
```bash
# Iniciar TensorBoard
tensorboard --logdir=ml/runs
```

#### Weights & Biases (`wandb>=0.16.0`)
- **Propósito**: Tracking de experimentos en la nube
- **Características**:
  - Logging automático de hiperparámetros
  - Comparación de experimentos
  - Colaboración en equipo

**Configuración**:
```bash
wandb login
```

### 6. Vector Similarity Search

#### FAISS (`faiss-cpu>=1.7.4`)
- **Propósito**: Búsqueda eficiente de vectores similares
- **Uso**: Búsqueda de imágenes similares en el dataset

**Nota**: Para GPU, instalar `faiss-gpu` en su lugar.

#### Annoy (`annoy>=1.17.0`)
- **Propósito**: Approximate Nearest Neighbors
- **Ventaja**: Más ligero que FAISS, bueno para producción

### 7. Image Processing

- `opencv-python>=4.8.0`: Procesamiento de imágenes y video
- `Pillow>=10.0.0`: Lectura/escritura de imágenes
- `scikit-image>=0.21.0`: Algoritmos de procesamiento avanzado

### 8. Data Handling

- `pandas>=2.0.0`: Manipulación de datos tabulares
- `numpy>=1.24.0`: Operaciones numéricas
- `matplotlib>=3.7.0`: Visualización estática
- `seaborn>=0.12.0`: Visualización estadística

### 9. GIS y Geospatial

- `geopandas>=0.14.0`: Manipulación de datos geoespaciales
- `shapely>=2.0.0`: Geometrías y operaciones espaciales
- `geojson>=3.0.0`: Lectura/escritura de GeoJSON

### 10. Database

- `psycopg2-binary>=2.9.0`: Conector PostgreSQL/PostGIS

### 11. Utilities

- `tqdm>=4.65.0`: Barras de progreso
- `pyyaml>=6.0.0`: Lectura de configuraciones
- `python-dotenv>=1.0.0`: Variables de entorno
- `minio>=7.2.0`: Cliente MinIO
- `piexif>=1.1.3`: Manipulación de EXIF

## Configuración de Jupyter Kernel

### Instalar Kernel

```bash
# Activar entorno virtual
.venv\Scripts\Activate.ps1

# Instalar kernel de Jupyter
python -m ipykernel install --user --name=sirccd-ml --display-name="SIRCCD ML (Python 3.14)"
```

### Verificar Kernel

```bash
jupyter kernelspec list
```

**Salida esperada**:
```
Available kernels:
  sirccd-ml    C:\Users\wilki\AppData\Roaming\jupyter\kernels\sirccd-ml
  python3      C:\Users\wilki\AppData\Roaming\jupyter\kernels\python3
```

### Usar Kernel en Notebook

1. Abrir Jupyter Notebook:
   ```bash
   jupyter notebook
   ```

2. Al crear un nuevo notebook, seleccionar: **SIRCCD ML (Python 3.14)**

3. O cambiar kernel en notebook existente:
   - Kernel → Change kernel → SIRCCD ML (Python 3.14)

## Estructura de Directorios ML

```
ml/
├── datasets/                # Datasets procesados (ya configurado)
├── notebooks/              # Jupyter notebooks para experimentación
│   ├── 01_dataset_exploration.ipynb
│   ├── 02_baseline_training.ipynb
│   ├── 03_hyperparameter_tuning.ipynb
│   └── 04_model_evaluation.ipynb
├── models/                 # Modelos entrenados
│   ├── baseline/
│   ├── optimized/
│   └── production/
├── runs/                   # Logs de TensorBoard
│   ├── train/
│   ├── val/
│   └── test/
├── scripts/                # Scripts de entrenamiento
│   ├── train.py
│   ├── evaluate.py
│   ├── export.py
│   └── utils/
├── configs/                # Configuraciones de modelos
│   ├── yolov8n.yaml
│   ├── yolov8s.yaml
│   └── yolov8m.yaml
└── requirements-training.txt  # Dependencias de ML

```

## Verificación de Instalación

### Script de Verificación

```python
# ml/scripts/verify_environment.py

import sys
import importlib

def check_package(package_name, import_name=None):
    """Verifica si un paquete está instalado."""
    if import_name is None:
        import_name = package_name
    
    try:
        mod = importlib.import_module(import_name)
        version = getattr(mod, '__version__', 'unknown')
        print(f"✅ {package_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {package_name}: NOT INSTALLED")
        return False

print("=" * 60)
print("VERIFICACIÓN DE ENTORNO ML - SIRCCD")
print("=" * 60)

print(f"\nPython: {sys.version}")

print("\n📦 Dependencias Core:")
check_package("torch")
check_package("torchvision")
check_package("ultralytics")

print("\n🖼️ Procesamiento de Imágenes:")
check_package("cv2", "cv2")
check_package("PIL", "PIL")
check_package("albumentations")

print("\n📊 Data Science:")
check_package("numpy")
check_package("pandas")
check_package("matplotlib")

print("\n📓 Jupyter:")
check_package("jupyter")
check_package("notebook")
check_package("ipykernel")

print("\n📈 Experiment Tracking:")
check_package("tensorboard")
check_package("wandb")

print("\n🔍 Vector Search:")
check_package("faiss", "faiss")
check_package("annoy")

print("\n🗺️ GIS:")
check_package("geopandas")
check_package("shapely")

print("\n✅ Verificación completa")
```

**Ejecutar**:
```bash
python ml/scripts/verify_environment.py
```

## Variables de Entorno

### Crear archivo `.env`

```bash
# ml/.env

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=sirccd_admin
MINIO_SECRET_KEY=sirccd_password_2026
MINIO_BUCKET=sirccd-datasets

# Weights & Biases (opcional)
WANDB_API_KEY=your_wandb_api_key_here
WANDB_PROJECT=sirccd-road-damage

# Google Places API (ya configurado en datasets)
GOOGLE_PLACES_API_KEY=your_google_api_key_here

# PyTorch
TORCH_HOME=.cache/torch
CUDA_VISIBLE_DEVICES=0  # GPU a usar (si disponible)

# Reproducibilidad
PYTHONHASHSEED=42
```

### Cargar Variables

```python
from dotenv import load_dotenv
import os

load_dotenv('ml/.env')

minio_endpoint = os.getenv('MINIO_ENDPOINT')
wandb_project = os.getenv('WANDB_PROJECT')
```

## Configuración de GPU (Opcional)

### Verificar CUDA

```python
import torch

print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU device: {torch.cuda.get_device_name(0)}")
    print(f"GPU count: {torch.cuda.device_count()}")
```

### Instalar CUDA-enabled PyTorch

Si tienes GPU NVIDIA:

```bash
# Desinstalar CPU version
pip uninstall torch torchvision torchaudio

# Instalar CUDA 12.1 version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# O CUDA 11.8 version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Tests de Funcionalidad

### Test 1: Cargar Dataset desde MinIO

```python
from minio import Minio
import os
from dotenv import load_dotenv

load_dotenv()

client = Minio(
    os.getenv('MINIO_ENDPOINT'),
    access_key=os.getenv('MINIO_ACCESS_KEY'),
    secret_key=os.getenv('MINIO_SECRET_KEY'),
    secure=False
)

# Listar objetos
objects = client.list_objects('sirccd-datasets', prefix='v1.0.0/train/images/', max_keys=5)
for obj in objects:
    print(f"✅ {obj.object_name}")
```

### Test 2: Cargar Imagen y Aplicar Augmentation

```python
import cv2
import albumentations as A
from albumentations.pytorch import ToTensorV2

# Definir transformaciones
transform = A.Compose([
    A.HorizontalFlip(p=0.5),
    A.RandomBrightnessContrast(p=0.2),
    A.Blur(blur_limit=3, p=0.1),
    ToTensorV2()
], bbox_params=A.BboxParams(format='yolo'))

# Cargar imagen (placeholder)
# image = cv2.imread('path/to/image.jpg')
# transformed = transform(image=image, bboxes=bboxes)
print("✅ Augmentation configurado")
```

### Test 3: Crear Modelo YOLOv8

```python
from ultralytics import YOLO

# Cargar modelo pre-entrenado
model = YOLO('yolov8n.pt')

print(f"✅ Modelo YOLOv8n cargado")
print(f"   Parámetros: {sum(p.numel() for p in model.model.parameters()):,}")
```

## Próximos Pasos

### M-02: Entrenamiento Baseline
- [ ] Crear notebook de exploración de datos
- [ ] Entrenar YOLOv8n baseline (50 epochs)
- [ ] Evaluar en conjunto de validación
- [ ] Guardar métricas y checkpoints

### M-03: Optimización de Hiperparámetros
- [ ] Definir espacio de búsqueda
- [ ] Ejecutar grid search o random search
- [ ] Comparar configuraciones
- [ ] Seleccionar mejor modelo

### M-04: Evaluación Final
- [ ] Evaluar en conjunto de test
- [ ] Calcular métricas finales (mAP, precision, recall)
- [ ] Generar matriz de confusión
- [ ] Análisis de errores

## Referencias

- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [Ultralytics YOLOv8](https://docs.ultralytics.com/)
- [Albumentations Documentation](https://albumentations.ai/docs/)
- [Jupyter Documentation](https://jupyter.org/documentation)
- [TensorBoard Guide](https://www.tensorflow.org/tensorboard)
- [Weights & Biases Docs](https://docs.wandb.ai/)

## Notas

- **Python Version**: 3.14.0.alpha.7 (venv actual)
- **OS**: Windows
- **GPU**: Verificar disponibilidad con `torch.cuda.is_available()`
- **Dataset Version**: v1.0.0 (en MinIO)
- **Total de imágenes**: 57,976 (train: 40,543, val: 11,614, test: 5,819)
