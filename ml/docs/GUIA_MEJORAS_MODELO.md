# 📈 Guía de Mejoras del Modelo SIRCCD

## Estado Actual (v1)

| Métrica | Valor |
|---------|-------|
| **Modelo** | YOLOv8m (25.9M params) |
| **Epochs** | 97 (de 100 planificados) |
| **mAP50** | 0.795 |
| **mAP50-95** | 0.539 |
| **Precision** | 0.810 |
| **Recall** | 0.743 |
| **Dataset** | 57,976 imágenes |
| **Clases** | 2 (bache, grieta) |

## 📊 Diagnóstico del Modelo v1

### ✅ Lo que funciona bien:
- Precision alta (0.810) → pocas falsas alarmas
- Mejora continua hasta epoch 97 → **NO hubo plateau**
- mAP50 de 0.795 es sólido para un baseline

### ⚠️ Áreas de mejora:
- **Recall (0.743)** → Se pierden ~25% de daños reales
- **mAP50-95 (0.539)** → Bounding boxes no son muy precisos
- 1,699 grupos de duplicados → posible **data leakage** entre train/val/test
- ~29,000 imágenes perdidas durante el pipeline

---

## 🚀 Estrategias de Mejora (Ordenadas por Impacto)

### 1. 🧹 Deduplicación (ALTA PRIORIDAD)

**Problema**: Hay ~1,699 grupos de imágenes duplicadas entre RDD2020 y RDD2022. Si un duplicado aparece en train y en val/test, las métricas están **infladas**.

**Solución**: El notebook `SIRCCD_Training_v2.ipynb` incluye deduplicación automática.

**Impacto esperado**: Las métricas podrían BAJAR ligeramente (porque eliminamos el leakage), pero serán más **fiables**. El modelo real será mejor.

---

### 2. ⚙️ Fine-tuning con Mejores Hiperparámetros

**Cambios clave en v2:**

```yaml
# v1 (baseline)              → v2 (mejorado)
optimizer: auto (MuSGD)       → AdamW        # Mejor convergencia
lr0: 0.01                     → 0.001        # LR bajo para fine-tuning
cos_lr: false                 → true         # Cosine annealing
close_mosaic: 10              → 20           # Más epochs sin mosaic
mixup: 0.0                    → 0.15         # Regularización
copy_paste: 0.0               → 0.1          # Más variedad
scale: 0.5                    → 0.9          # Multi-scale agresivo  
label_smoothing: 0.0          → 0.1          # Suavizar clasificación
multi_scale: 0.0              → 0.5          # Resolución variable
```

**¿Por qué funciona?**
- AdamW + cosine LR → convergencia más suave en fine-tuning
- MixUp + copy_paste → regularización, evita overfitting
- Scale 0.9 + multi_scale → detectar daños de distintos tamaños
- Label smoothing → el modelo no se "sobreconfía"
- Close mosaic 20 → 20 epochs finales sin mosaic para refinar

---

### 3. 🔍 Modelo Más Grande

Si el hardware lo permite:

| Modelo | Params | mAP50 esperado | VRAM necesaria |
|--------|--------|----------------|----------------|
| **YOLOv8m** (actual) | 25.9M | 0.795 | ~8 GB |
| **YOLOv8l** | 43.7M | ~0.82-0.84 | ~12 GB |
| **YOLOv8x** | 68.2M | ~0.84-0.86 | ~16 GB |
| **YOLO11m** | ~22M | ~0.82+ | ~8 GB |

**Cómo usar YOLOv8l:**
```python
model = YOLO('yolov8l.pt')  # En vez de cargar best.pt
```

---

### 4. 🔬 Resolución Más Alta

Aumentar de 640 a 1280 puede mejorar la detección de daños pequeños.

```python
model.train(
    imgsz=1280,   # 4x más píxeles
    batch=4,       # Reducir batch por VRAM
    # ... resto de parámetros
)
```

**Impacto**: +2-5% mAP50, especialmente para grietas finas. Requiere A100.

---

### 5. 📦 Más Datos (ALTO IMPACTO)

**Datasets pendientes de integrar:**

| Dataset | Imágenes | Tipo | Estado |
|---------|----------|------|--------|
| CRACK500 | 500 | Grietas | Pendiente |
| CFD | ~118 | Daños varios | Pendiente |
| SUT-Crack | ~800 | Grietas | Pendiente |

**Imágenes perdidas del pipeline:**
- ~7,348 imágenes eran solo señal (eliminadas correctamente)
- ~21,747 imágenes filtradas durante stratified split (potencialmente recuperables)

---

### 6. 🧪 Test-Time Augmentation (TTA)

No requiere reentrenar. Mejora la inferencia:

```python
results = model.predict(source='imagen.jpg', augment=True)
```

**Impacto**: +1-3% mAP50 en inferencia, pero ~3x más lento.

---

### 7. 🤝 Ensemble de Modelos

Combinar predicciones de múltiples modelos:

```python
# Usar Weighted Boxes Fusion
from ensemble_boxes import weighted_boxes_fusion

models = [
    YOLO('v1_best.pt'),
    YOLO('v2_best.pt'),
    YOLO('yolov8l_best.pt'),
]
```

**Impacto**: +2-5% mAP50, pero más lento y complejo.

---

## 📋 Plan de Ejecución Recomendado

### Fase 1: Quick Wins (1-2 horas en Colab)
1. ✅ Deduplicar dataset (eliminar data leakage)
2. ✅ Fine-tune v2 con hiperparámetros mejorados
3. ✅ Evaluar en test con TTA

### Fase 2: Escalar (3-4 horas en Colab)
4. Probar YOLOv8l o YOLO11
5. Probar imgsz=1280

### Fase 3: Más Datos (requiere trabajo previo)
6. Integrar CRACK500, CFD, SUT-Crack
7. Recuperar imágenes filtradas del pipeline
8. Recolectar datos locales (República Dominicana)

---

## 🎯 Metas Realistas

| Fase | mAP50 esperado | mAP50-95 esperado |
|------|----------------|-------------------|
| **v1 (actual)** | 0.795 | 0.539 |
| **v2 (fine-tune)** | 0.81 - 0.83 | 0.56 - 0.59 |
| **v2 + modelo grande** | 0.83 - 0.86 | 0.59 - 0.63 |
| **v2 + más datos** | 0.86 - 0.90 | 0.63 - 0.68 |

> **Nota**: Después de eliminar duplicados, las métricas "reales" podrían ser ligeramente  
> menores que las reportadas en v1, pero serán más confiables.

---

## 📂 Archivos Relacionados

- **Notebook v2**: `ml/notebooks/SIRCCD_Training_v2.ipynb`
- **Notebook v1**: `ml/notebooks/SIRCCD_Training_Colab.ipynb`
- **Resume training**: `ml/notebooks/SIRCCD_Resume_Training.ipynb`
- **Guía Colab**: `ml/docs/GUIA_INICIO_RAPIDO_COLAB.md`
