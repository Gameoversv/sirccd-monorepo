# 🚀 Guía Rápida: Entrenamiento en Google Colab

## Resumen

Esta guía te lleva paso a paso para entrenar el modelo YOLOv8 de SIRCCD en Google Colab usando GPU gratuita.

**Tiempo total estimado**: 7-9 horas
- Preparación: 30-60 min
- Entrenamiento: 6-8 horas

**Requisitos**:
- Cuenta de Google (Gmail)
- Google Drive con ~16 GB libres
- Conexión estable a internet

---

## Paso 1: Preparar Dataset (Local) ⏱️ 10-30 min

### 1.1 Iniciar MinIO

```powershell
# En tu PC local
cd C:\Users\wilki\sirccd-monorepo\sirccd-monorepo

# Iniciar MinIO
docker-compose -f docker-compose.minio.yml up -d

# Verificar que está corriendo
docker ps | Select-String "minio"
```

### 1.2 Exportar Dataset a ZIP

```powershell
# Crear ZIP optimizado para Colab
.venv\Scripts\python.exe ml\datasets\scripts\export_for_colab.py
```

**Salida esperada**:
```
✅ ZIP creado exitosamente
📊 Estadísticas:
   Archivo: ml/datasets/exports/sirccd_dataset_v1.0.0.zip
   Tamaño: ~15.5 GB
   Total de archivos: 115,952
```

**Ubicación del ZIP**: `ml/datasets/exports/sirccd_dataset_v1.0.0.zip`

---

## Paso 2: Subir a Google Drive ⏱️ 30-60 min

### 2.1 Abrir Google Drive

1. Ve a [drive.google.com](https://drive.google.com)
2. Inicia sesión con tu cuenta

### 2.2 Crear Carpeta

1. Click en **Nuevo** > **Nueva carpeta**
2. Nombre: `SIRCCD_Dataset`
3. Click **Crear**

### 2.3 Subir ZIP

1. Entra a la carpeta `SIRCCD_Dataset`
2. Click **Nuevo** > **Subir archivo**
3. Selecciona: `ml/datasets/exports/sirccd_dataset_v1.0.0.zip`
4. Espera a que termine la subida (~30-60 min)

**Ruta final en Drive**:
```
MyDrive/
└── SIRCCD_Dataset/
    └── sirccd_dataset_v1.0.0.zip  (15.5 GB)
```

---

## Paso 3: Preparar Notebook en Colab ⏱️ 5 min

### 3.1 Subir Notebook

1. Ve a [colab.research.google.com](https://colab.research.google.com)
2. Click **Archivo** > **Subir notebook**
3. Selecciona: `ml/notebooks/SIRCCD_Training_Colab.ipynb`

### 3.2 Configurar GPU

1. Click **Entorno de ejecución** > **Cambiar tipo de entorno de ejecución**
2. **Acelerador de hardware**: GPU
3. **Tipo de GPU**: T4 (recomendado)
4. Click **Guardar**

### 3.3 Verificar GPU

Ejecuta la primera celda:
```python
!nvidia-smi
```

**Salida esperada**:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 525.XX.XX    Driver Version: 525.XX.XX    CUDA Version: 12.X   |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  Tesla T4            Off  | 00000000:00:04.0 Off |                    0 |
| N/A   XX°C    P0    XX W /  70W |      0MiB / 15360MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

---

## Paso 4: Ejecutar Entrenamiento ⏱️ 6-8 horas

### 4.1 Instalar Dependencias

Ejecuta celda 2:
```python
!pip install -q ultralytics Pillow tqdm
```

### 4.2 Montar Google Drive

Ejecuta celda 3:
```python
from google.colab import drive
drive.mount('/content/drive')
```

- Click en el enlace que aparece
- Autoriza acceso a Drive
- Copia el código
- Pégalo y presiona Enter

### 4.3 Descargar y Extraer Dataset

Ejecuta celda 4-5:
```python
# Verificar dataset
DRIVE_DATASET_PATH = '/content/drive/MyDrive/SIRCCD_Dataset/sirccd_dataset_v1.0.0.zip'

# Extraer
import zipfile
with zipfile.ZipFile(DRIVE_DATASET_PATH, 'r') as zip_ref:
    zip_ref.extractall('/content/')
```

**Tiempo**: 10-15 minutos  
**Espacio usado en Colab**: ~16 GB

### 4.4 Iniciar Entrenamiento

Ejecuta celda 6:
```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')
results = model.train(
    data='/content/sirccd_dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device=0
)
```

**Tiempo**: 6-8 horas  
**Progreso**: Se mostrará en tiempo real

---

## Paso 5: Guardar Resultados ⏱️ 5-10 min

### 5.1 Guardar Modelo en Drive

Ejecuta última celda:
```python
import shutil
from datetime import datetime

drive_folder = '/content/drive/MyDrive/SIRCCD_Models'
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

shutil.copytree(
    'sirccd-training/baseline-yolov8n',
    f'{drive_folder}/yolov8n_{timestamp}'
)
```

### 5.2 Descargar Localmente

1. Ve a Drive en tu navegador
2. Entra a `MyDrive/SIRCCD_Models/`
3. Click derecho en la carpeta del modelo
4. **Descargar**

**Contenido**:
```
yolov8n_20260217_143022/
├── weights/
│   ├── best.pt          # Mejor modelo (usar este)
│   └── last.pt          # Último epoch
├── results.csv          # Métricas por epoch
├── confusion_matrix.png # Matriz de confusión
├── PR_curve.png        # Precision-Recall
├── F1_curve.png        # F1 Score
└── training_summary.json
```

---

## Paso 6: Evaluar Modelo

### 6.1 En Colab

```python
# Cargar mejor modelo
best_model = YOLO('sirccd-training/baseline-yolov8n/weights/best.pt')

# Evaluar en test set
metrics = best_model.val(data='/content/sirccd_dataset/data.yaml', split='test')

print(f"mAP50: {metrics.box.map50:.4f}")
print(f"mAP50-95: {metrics.box.map:.4f}")
```

### 6.2 En Local

```powershell
# Copiar modelo descargado
cp ~/Downloads/yolov8n_20260217_143022/weights/best.pt ml/models/

# Evaluar
cd ml
.venv\Scripts\python.exe -c "
from ultralytics import YOLO
model = YOLO('models/best.pt')
metrics = model.val(data='datasets/processed/split/data.yaml')
print(f'mAP50: {metrics.box.map50:.4f}')
"
```

---

## Troubleshooting

### ❌ "Dataset no encontrado"

**Problema**: ZIP no está en la ruta correcta de Drive

**Solución**:
1. Verifica que el ZIP esté en: `MyDrive/SIRCCD_Dataset/`
2. Nombre exacto: `sirccd_dataset_v1.0.0.zip`
3. Re-monta Drive en Colab: `drive.mount('/content/drive', force_remount=True)`

### ❌ "Out of memory"

**Problema**: GPU sin memoria suficiente

**Solución**:
1. Reduce `batch_size`:
   ```python
   batch=8  # en lugar de 16
   ```
2. Reduce `imgsz`:
   ```python
   imgsz=512  # en lugar de 640
   ```

### ❌ "Runtime disconnected"

**Problema**: Sesión de Colab desconectada (4-12 horas de límite)

**Solución**:
1. **Antes de entrenar**, ejecuta:
   ```python
   from google.colab import output
   output.enable_keepalive()
   ```
2. Si se desconecta:
   - El entrenamiento se detuvo
   - Checkpoints guardados cada 10 epochs
   - Reanudar desde último checkpoint:
     ```python
     model = YOLO('sirccd-training/baseline-yolov8n/weights/last.pt')
     model.train(resume=True)
     ```

### ❌ "Zip file is too large"

**Problema**: Drive no permite archivos >15 GB en web

**Solución**:
1. **Opción A**: Usa Google Drive Desktop
   - Instala [Google Drive for Desktop](https://www.google.com/drive/download/)
   - Arrastra el ZIP a la carpeta sincronizada
   
2. **Opción B**: Divide el dataset
   ```powershell
   # Solo train (70% del dataset)
   .venv\Scripts\python.exe ml\datasets\scripts\export_for_colab.py --split train
   ```

---

## Consejos de Optimización

### 🚀 Velocidad

1. **AMP (Automatic Mixed Precision)**:
   ```python
   amp=True  # Ya incluido, 2x más rápido
   ```

2. **Cache en RAM**:
   ```python
   cache=True  # Cachea imágenes (requiere 10+ GB RAM)
   ```

3. **Múltiples workers**:
   ```python
   workers=4  # Para carga de datos
   ```

### 🎯 Precisión

1. **Más epochs**:
   ```python
   epochs=300  # Mejor convergencia
   patience=100  # Early stopping más tolerante
   ```

2. **Modelo más grande**:
   ```python
   model = YOLO('yolov8s.pt')  # Small (mejor que nano)
   model = YOLO('yolov8m.pt')  # Medium (requiere más GPU)
   ```

3. **Data augmentation**:
   ```python
   mosaic=1.0,      # Mosaic augmentation
   mixup=0.1,       # Mixup augmentation
   degrees=10.0,    # Rotación
   flipl r=0.5      # Flip horizontal
   ```

---

## Métricas Esperadas (baseline)

**YOLOv8n (nano) - 100 epochs**:
- mAP50: ~0.75-0.85
- mAP50-95: ~0.45-0.55
- Precision: ~0.80-0.85
- Recall: ~0.75-0.80
- Inference: ~10 ms/imagen (T4 GPU)

**YOLOv8s (small) - 100 epochs**:
- mAP50: ~0.80-0.90
- mAP50-95: ~0.50-0.60
- Precision: ~0.85-0.90
- Recall: ~0.80-0.85
- Inference: ~15 ms/imagen (T4 GPU)

---

## Próximos Pasos

1. ✅ Entrenar modelo baseline
2. 📊 Analizar resultados
3. 🔧 Fine-tuning con hiperparámetros
4. 🚀 Exportar a ONNX para producción
5. 🌐 Integrar con backend SIRCCD

---

## Recursos Adicionales

- **Documentación Ultralytics**: https://docs.ultralytics.com
- **Google Colab FAQ**: https://research.google.com/colaboratory/faq.html
- **YOLO Tutorial**: https://github.com/ultralytics/ultralytics

Para dudas o problemas, consulta `ml/docs/CLOUD_TRAINING.md` en el repositorio.
