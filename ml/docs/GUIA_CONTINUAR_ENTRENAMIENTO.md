# 🔄 Guía: Continuar Entrenamiento en Google Colab

## 📋 Situación

Has entrenado un modelo YOLOv8 hasta **epoch 40** y guardaste el checkpoint en Google Drive. Ahora quieres **continuar hasta epoch 100** en una nueva sesión de Colab.

## ✅ Requisitos Previos

Antes de continuar, verifica que tienes:

1. **Modelo guardado en Drive:**
   ```
   MyDrive/
     └── SIRCCD_Models/
         └── train/
             └── weights/
                 ├── best.pt    (~6 MB)
                 └── last.pt    (~6 MB)
   ```

2. **Dataset en Drive:**
   ```
   MyDrive/
     └── SIRCCD_Dataset/
         └── sirccd_dataset_v1.0.0.zip    (~7 GB)
   ```

3. **Espacio disponible en Drive:**
   - Mínimo: ~20 GB (dataset + modelos + resultados)
   - Recomendado: 30 GB

## 🚀 Pasos para Continuar

### Opción 1: Usar Notebook Preparado (RECOMENDADO)

1. **Abrir Google Colab:**
   - Ve a: https://colab.research.google.com

2. **Subir notebook:**
   - Archivo → Subir notebook
   - Selecciona: `ml/notebooks/SIRCCD_Training_v3_FromScratch.ipynb`

3. **Configurar GPU:**
   - Runtime → Change runtime type
   - Hardware accelerator: **GPU**
   - GPU type: **T4** (gratis) o **A100** (Colab Pro)

4. **Ejecutar celdas:**
   - Runtime → Run all
   - O ejecuta celda por celda con `Shift + Enter`

5. **Esperar ~4-6 horas:**
   - El entrenamiento continuará desde epoch 41 → 100
   - Guarda automáticamente en Drive cada 10 epochs

### Opción 2: Código Manual

Si prefieres código directo, copia y pega esto en Colab:

```python
# 1. Setup
!pip install ultralytics -q
from google.colab import drive
drive.mount('/content/drive')

# 2. Extraer dataset (si no está ya extraído)
import zipfile
DATASET_PATH = '/content/drive/MyDrive/SIRCCD_Dataset/sirccd_dataset_v1.0.0.zip'

if not os.path.exists('/content/sirccd_dataset'):
    with zipfile.ZipFile(DATASET_PATH, 'r') as zip_ref:
        zip_ref.extractall('/content/')

# 3. Cargar modelo guardado
from ultralytics import YOLO
model = YOLO('/content/drive/MyDrive/SIRCCD_Models/train/weights/last.pt')

# 4. Continuar entrenamiento
results = model.train(
    data='/content/sirccd_dataset/data.yaml',
    epochs=100,      # Total deseado
    resume=True,     # ⚠️ CRÍTICO: Continúa desde epoch actual
    project='/content/drive/MyDrive/SIRCCD_Models',
    name='train',
    exist_ok=True,
    device=0,
    amp=True,
    cache=True,
    save_period=10
)

# 5. Evaluar
metrics = model.val()
print(f"mAP50: {metrics.box.map50:.4f}")
```

## 🔑 Parámetros Clave

### resume=True vs resume=False

**CON `resume=True`** (CORRECTO para continuar):
```python
model = YOLO('last.pt')
model.train(epochs=100, resume=True)
# → Continúa: epoch 41, 42, 43... → 100
# → Mantiene historial completo
# → Learning rate continúa su schedule
```

**SIN `resume=True`** (INCORRECTO):
```python
model = YOLO('last.pt')
model.train(epochs=100, resume=False)
# → Reinicia: epoch 1, 2, 3... → 100
# → Usa pesos cargados pero cuenta desde 0
# → Learning rate reinicia desde inicial
```

### last.pt vs best.pt

| Archivo | Cuándo Usar | Resultado |
|---------|-------------|-----------|
| `last.pt` | Continuar entrenamiento lineal | Sigue desde epoch 40 → 100 |
| `best.pt` | Fine-tuning desde mejor modelo | Parte del mejor mAP, reinicia epochs |

**Recomendación:** Usa `last.pt` para continuar entrenamiento normal.

## 📊 Qué Esperar

### Métricas Iniciales (Epoch 40)
```
mAP50:     0.6977
mAP50-95:  0.4050
Precision: 0.7091
Recall:    0.6539
```

### Mejora Esperada (Epoch 100)
```
mAP50:     0.75-0.80  (+7-14%)
mAP50-95:  0.45-0.50  (+10-23%)
Precision: 0.73-0.78  (+3-10%)
Recall:    0.68-0.72  (+4-7%)
```

### Tiempo de Entrenamiento

| GPU | Tiempo Epoch | Total (60 epochs) |
|-----|--------------|-------------------|
| T4 (Colab gratis) | 3-4 min | 3-4 horas |
| V100 (Colab Pro) | 2-3 min | 2-3 horas |
| A100 (Colab Pro+) | 1-2 min | 1-2 horas |

## ⚠️ Problemas Comunes

### 1. "Runtime disconnected"

**Causa:** Sesión de Colab expiró (idle >90 min o >12 horas total)

**Solución:**
- El entrenamiento guarda checkpoints cada 10 epochs
- Vuelve a ejecutar el notebook
- Cargará automáticamente el último `last.pt`
- Continúa desde donde quedó

**Prevención:**
```python
# Agregar al inicio del notebook
from google.colab import output
output.enable_custom_widget_manager()

# Mantener conexión
import IPython
js_code = """
setInterval(() => {
  document.querySelector("colab-toolbar-button#connect").click();
}, 60000);
"""
IPython.display.display(IPython.display.Javascript(js_code))
```

### 2. "CUDA out of memory"

**Causa:** Batch size muy grande para GPU

**Solución:**
```python
# Reducir batch size
model.train(
    batch=8,      # En lugar de 16
    cache=False,  # No cachear en RAM
)
```

### 3. "Model file not found"

**Causa:** Ruta incorrecta al modelo en Drive

**Solución:**
```python
# Verificar ruta exacta
!ls -lh /content/drive/MyDrive/SIRCCD_Models/train/weights/

# Probar rutas alternativas
model = YOLO('/content/drive/MyDrive/SIRCCD_Models/train/weights/last.pt')
# O
model = YOLO('/content/drive/My Drive/SIRCCD_Models/train/weights/last.pt')
```

### 4. "Performance degradation"

**Causa:** Learning rate muy bajo en epochs avanzados

**Síntoma:** mAP se estanca o baja ligeramente

**Solución:**
```python
# Opción A: Dejar continuar (puede recuperarse)
# La curva de learning rate tiene warmups

# Opción B: Reiniciar learning rate (fine-tuning)
model.train(
    epochs=150,       # Extender más
    resume=True,
    optimizer='SGD',
    lr0=0.001,        # Learning rate bajo pero no mínimo
    warmup_epochs=5   # Warmup suave
)
```

## 📈 Monitoreo Durante Entrenamiento

### En Consola de Colab
```
Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
41/100     3.2G      1.389      1.267      1.401        156        640
```

- **GPU_mem:** Uso de VRAM (debe estar <15GB en T4)
- **box_loss:** Pérdida localización (debe bajar)
- **cls_loss:** Pérdida clasificación (debe bajar)
- **Instances:** Objetos en batch

### TensorBoard (Opcional)
```python
# Cargar logs en TensorBoard
%load_ext tensorboard
%tensorboard --logdir /content/drive/MyDrive/SIRCCD_Models/train
```

## 🎯 Siguientes Pasos Después de 100 Epochs

### 1. Evaluar en Test Set
```python
# Cargar mejor modelo
model = YOLO('/content/drive/MyDrive/SIRCCD_Models/train/weights/best.pt')

# Evaluar en test (imágenes nunca vistas)
test_metrics = model.val(
    data='/content/sirccd_dataset/data.yaml',
    split='test'
)

print(f"Test mAP50: {test_metrics.box.map50:.4f}")
```

### 2. Probar Modelo Más Grande

Si mAP50 < 0.80, prueba modelos más grandes:

```python
# YOLOv8s (small) - +30% parámetros
model = YOLO('yolov8s.pt')
model.train(
    data='/content/sirccd_dataset/data.yaml',
    epochs=100,
    batch=12,  # Reducir por más parámetros
)

# YOLOv8m (medium) - +100% parámetros
model = YOLO('yolov8m.pt')
model.train(
    data='/content/sirccd_dataset/data.yaml',
    epochs=100,
    batch=8,   # Reducir más
)
```

### 3. Exportar para Producción
```python
# Cargar mejor modelo
model = YOLO('best.pt')

# Exportar a ONNX (multi-plataforma)
model.export(format='onnx', imgsz=640)

# Exportar a TensorRT (NVIDIA GPUs)
model.export(format='engine', imgsz=640, half=True)

# Exportar a CoreML (iOS/macOS)
model.export(format='coreml', imgsz=640)
```

## 📝 Checklist Completo

Antes de cerrar Colab, verifica:

- [ ] Entrenamiento completó 100 epochs
- [ ] Métricas finales guardadas
- [ ] `best.pt` y `last.pt` en Drive
- [ ] `results.png` generado
- [ ] `confusion_matrix.png` generado
- [ ] Evaluación en test ejecutada
- [ ] Modelo exportado a ONNX (opcional)

## 💾 Backup Recomendado

```bash
# En tu PC, descargar modelos desde Drive
# Estructura recomendada:
ml/
  └── models/
      └── v1.0.0/
          ├── best.pt
          ├── last.pt
          ├── best.onnx
          ├── results.png
          └── training_summary.json
```

## 📚 Referencias

- [Ultralytics YOLOv8 Docs](https://docs.ultralytics.com/)
- [Google Colab FAQ](https://research.google.com/colaboratory/faq.html)
- [SIRCCD Training Guide](./GUIA_INICIO_RAPIDO_COLAB.md)

---

**Última actualización:** 2026-02-18  
**Autor:** SIRCCD Team
