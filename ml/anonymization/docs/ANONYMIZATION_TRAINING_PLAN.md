# Plan de Entrenamiento — Modelo de Anonimización (Rostros + Placas)

**Fecha**: 6 de marzo de 2026  
**Modelo base**: YOLO11s Detect  
**Tarea**: Detección de objetos (bounding boxes) para blur  
**Clases**: 2 (`face`, `license_plate`)

---

## 1. Estrategia General

### ¿Por qué Detección y no Segmentación?

El objetivo es aplicar **Gaussian blur** sobre cada bounding box detectada.  
No necesitamos contornos exactos — una caja con 20% de margen cubre la región
sin dejar expuesta información sensible. La tarea `Detect` es más rápida de
entrenar, requiere menos anotación y tiene mejor throughput en inferencia.

### ¿Por qué YOLO11s?

| Variante | Params | mAP@0.5 | Velocidad | Uso recomendado |
|----------|--------|---------|-----------|-----------------|
| YOLO11n  | 2.6M   | ★★★    | ★★★★★     | Edge / móvil    |
| **YOLO11s** | **9.4M** | **★★★★** | **★★★★** | **Balance óptimo** |
| YOLO11m  | 20.1M  | ★★★★★  | ★★★       | Máximo recall    |

- **YOLO11s** da buen recall en objetos pequeños (placas lejanas) sin necesitar
  GPU excesiva para entrenar.
- Si tras evaluar el baseline el recall de placas es bajo, escalar a YOLO11m.

### Enfoque: Un solo modelo, 2 clases

Para el prototipo usamos **un solo detector con 2 clases**: `face` (0) y
`license_plate` (1). Esto simplifica el pipeline de inferencia y despliegue.

---

## 2. Datasets

### Rostros — WIDER FACE

| Campo | Valor |
|-------|-------|
| Imágenes | 32,203 |
| Bounding boxes | 393,703 |
| Split | 40% train / 10% val / 50% test |
| Diversidad | Escala, pose, oclusión, iluminación, eventos |
| Formato original | `.txt` con `x1 y1 w h blur expression illumination invalid occlusion pose` |
| Fuente | http://shuoyang1213.me/WIDERFACE/ |

**Conversión necesaria**: WIDER FACE viene en formato propio → convertir a YOLO
(`class cx cy w h` normalizado).

### Placas — CCPD + RodoSol-ALPR

| Dataset | Imágenes | Origen | Notas |
|---------|----------|--------|-------|
| **CCPD** | ~250,000 | China | Gran volumen, coordenadas en nombre de archivo |
| **RodoSol-ALPR** | 20,000 | Brasil | Peajes reales, iluminación variada |
| **AOLP** (opcional) | 1,874 | Taiwán | Refuerzo: acceso, enforcement, patrullaje |

**Conversión necesaria**: Cada dataset tiene formato propio → convertir todo a
YOLO con clase `1` (`license_plate`).

### Estrategia de muestreo

Para no desbalancear el entrenamiento (250k placas vs 13k rostros train):

- **Rostros**: Usar 100% del train+val de WIDER FACE (~14,500 imágenes)
- **Placas CCPD**: Submuestrear a **15,000 imágenes** (aleatorio, seed 42)
- **RodoSol-ALPR**: Submuestrear a **5,000 imágenes**

**Total aproximado**: ~34,500 imágenes de entrenamiento.

### Split final

| Split | Proporción | Imágenes estimadas |
|-------|-----------|-------------------|
| Train | 80% | ~31,200 |
| Val   | 15% | ~5,850 |
| Test  | 5%  | ~1,950 |

---

## 3. Estructura de Carpetas

```
ml/anonymization/
├── data.yaml                        # Configuración del dataset
├── datasets/
│   ├── raw/                         # Descargas originales (no versionadas)
│   │   ├── wider_face/
│   │   │   ├── WIDER_train/
│   │   │   ├── WIDER_val/
│   │   │   └── wider_face_split/    # Anotaciones .mat o .txt
│   │   ├── ccpd/
│   │   │   └── ccpd_base/
│   │   └── rodosol_alpr/
│   ├── processed/                   # Dataset unificado en formato YOLO
│   │   ├── images/
│   │   │   ├── train/
│   │   │   ├── val/
│   │   │   └── test/
│   │   └── labels/
│   │       ├── train/
│   │       ├── val/
│   │       └── test/
│   └── metadata/
│       ├── preparation_report.json
│       └── class_distribution.json
├── scripts/
│   ├── 01_download_datasets.py      # Descarga y extracción
│   ├── 02_convert_wider_face.py     # WIDER FACE → YOLO format
│   ├── 03_convert_plates.py         # CCPD/RodoSol → YOLO format
│   ├── 04_merge_and_split.py        # Unificar + split estratificado
│   └── 05_validate_dataset.py       # Validación de integridad
├── train.py                         # Script de entrenamiento YOLO11
├── inference.py                     # Script de inferencia + blur
└── runs/                            # Resultados de entrenamiento
    ├── detect/
    │   └── anonymizer_v1/
    │       ├── weights/
    │       │   ├── best.pt
    │       │   └── last.pt
    │       └── results.csv
    └── ...
```

---

## 4. Configuración de Entrenamiento

### `data.yaml`

```yaml
path: ./ml/anonymization/datasets/processed
train: images/train
val: images/val
test: images/test

nc: 2
names:
  0: face
  1: license_plate
```

### Hiperparámetros

```yaml
# Baseline YOLO11s
model: yolo11s.pt           # Pretrained COCO weights (transfer learning)
epochs: 150                  # 100 mínimo, 150 recomendado
imgsz: 640                   # Default; subir a 1280 si GPU lo permite
batch: 16                    # Ajustar según VRAM (8 para GPU <8GB)
patience: 30                 # Early stopping
optimizer: AdamW
lr0: 0.001
lrf: 0.01                   # LR final = lr0 * lrf
weight_decay: 0.0005
warmup_epochs: 5
cos_lr: true                # Cosine annealing

# Augmentations (Ultralytics built-in)
hsv_h: 0.015                # Variación de hue
hsv_s: 0.7                  # Variación de saturación
hsv_v: 0.4                  # Variación de brillo
degrees: 5.0                # Rotación leve (no voltear placas demasiado)
translate: 0.1
scale: 0.5                  # Escala agresiva para objetos pequeños
shear: 2.0
flipud: 0.0                 # NO voltear verticalmente (caras invertidas)
fliplr: 0.5                 # Sí voltear horizontalmente
mosaic: 1.0                 # Mosaic augmentation ON
mixup: 0.1                  # Poco mixup
copy_paste: 0.1             # Copy-paste augmentation

# Project
project: ml/anonymization/runs
name: anonymizer_v1
exist_ok: true
```

### Notas sobre augmentations

- **`flipud: 0.0`**: No voltear verticalmente — las caras boca abajo no ocurren
  en escenas urbanas y confunden al detector.
- **`scale: 0.5`**: Agresivo para que el modelo aprenda a detectar placas
  pequeñas (lejanas).
- **`mosaic: 1.0`**: Mosaic mezcla 4 imágenes — excelente para diversificar
  contextos y tamaños de objetos.
- **`degrees: 5.0`**: Rotación sutil — caras y placas no suelen estar muy
  inclinadas.

---

## 5. Métricas de Evaluación

### Métricas objetivo (baseline aceptable)

| Métrica | Face | License Plate | Promedio |
|---------|------|---------------|----------|
| **mAP@0.5** | ≥ 0.85 | ≥ 0.80 | ≥ 0.82 |
| **Precision** | ≥ 0.80 | ≥ 0.75 | ≥ 0.77 |
| **Recall** | ≥ 0.90 | ≥ 0.85 | ≥ 0.87 |

**Prioridad: RECALL sobre PRECISION.** Para anonimización, es peor no detectar
un rostro (violación de privacidad) que generar un falso positivo (blur en una
región sin información sensible). Se usa **confidence threshold bajo** (0.25) en
producción para maximizar recall.

### Curvas a monitorear

- **P-R curve** por clase
- **F1-confidence curve** — buscar el threshold óptimo
- **Loss curves**: `box_loss`, `cls_loss`, `dfl_loss`

---

## 6. Pipeline de Inferencia (Producción)

```
Imagen entrada
    │
    ▼
YOLO11s Detect (conf=0.25, iou=0.45)
    │
    ▼
Filtrar detecciones: face, license_plate
    │
    ▼
Expandir cada bbox +20% (margen de seguridad)
    │
    ▼
Aplicar GaussianBlur(kernel=51, sigma=30) en cada ROI
    │
    ▼
Imagen anonimizada
```

### Integración con backend

El `backend/services/anonymizer.py` actual usa Haar Cascade. Se reemplazará por:

1. Cargar modelo YOLO11 (`best.pt`) en `__init__`
2. En `anonymize()`, correr inferencia YOLO11 en vez de Haar Cascade
3. Mantener la misma interfaz pública (`anonymize(image_bytes) → (bytes, stats)`)
4. Fallback: si YOLO11 no está disponible, usar Haar Cascade como respaldo

---

## 7. Entrenamiento en Google Colab

Para entrenar con GPU gratuita (T4):

```python
# Instalar Ultralytics
!pip install ultralytics>=8.3.0

# Montar Google Drive (para guardar pesos)
from google.colab import drive
drive.mount('/content/drive')

# Subir dataset a Colab (o montar desde Drive)
# ...

# Entrenar
from ultralytics import YOLO
model = YOLO('yolo11s.pt')
results = model.train(
    data='/content/anonymization/data.yaml',
    epochs=150,
    imgsz=640,
    batch=16,
    project='/content/drive/MyDrive/sirccd/anonymization/runs',
    name='anonymizer_v1',
)
```

**Tiempo estimado en T4**: ~4-6 horas con 39k imágenes, 150 épocas, batch 16.

---

## 8. Checklist de Ejecución

- [ ] Descargar WIDER FACE (train + val + anotaciones)
- [ ] Descargar CCPD (ccpd_base)
- [ ] Descargar RodoSol-ALPR
- [ ] Ejecutar `02_convert_wider_face.py`
- [ ] Ejecutar `03_convert_plates.py`
- [ ] Ejecutar `04_merge_and_split.py`
- [ ] Ejecutar `05_validate_dataset.py`
- [ ] Verificar distribución de clases y tamaños de bbox
- [ ] Entrenar baseline YOLO11s (150 épocas)
- [ ] Evaluar mAP@0.5 por clase
- [ ] Si recall < objetivo → probar YOLO11m o imgsz=1280
- [ ] Exportar `best.pt` a `ml/models/anonymizer/`
- [ ] Actualizar `backend/services/anonymizer.py` con YOLO11
- [ ] Test de integración end-to-end

---

## 9. Fine-tuning Futuro (Datos Locales)

Después del baseline, recolectar **200-500 imágenes propias** del entorno real
(calles de Santiago, RD) para fine-tuning:

1. Capturar imágenes con celulares/dashcams en distintas condiciones
2. Anotar con Roboflow o CVAT (gratis para proyectos académicos)
3. Fine-tune el modelo `best.pt` por 30-50 épocas adicionales
4. Evaluar mejora en recall de placas dominicanas

---

**Autor**: Wilson Wilki  
**Versión**: 1.0
