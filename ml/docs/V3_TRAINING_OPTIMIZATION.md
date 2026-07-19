# 🎯 Optimización Entrenamiento v3 para A100

> **Nota (2026-07-19)**: el notebook `v3_FromScratch` fue archivado en `ml/notebooks/archive/`. El vigente es `ml/notebooks/SIRCCD_Training_v5_H100_Optimized.ipynb` (para H100, no A100). Este documento queda como referencia histórica de la optimización para v3/A100 — no asumir que sus recomendaciones aplican directamente a v5/H100 sin revisar.

## Revisión Configuración Actual

**Notebook**: `ml/notebooks/archive/SIRCCD_Training_v3_FromScratch.ipynb` (archivado)

### Configuración Base (Buena)

| Parámetro | Valor Actual | Estado |
|-----------|--------------|--------|
| Modelo | YOLO26l | ✅ Excelente (NMS-free, end-to-end) |
| Resolución | 1280x1280 | ✅ Óptimo (4x más detalle) |
| Epochs | 200 | ⚠️ Bueno, pero puede mejorar |
| Optimizer | auto (MuSGD) | ✅ Óptimo para YOLO26 |
| Learning Rate | lr0=0.01, lrf=0.01 | ✅ Estándar |
| Batch (A100) | ~8-16 | ✅ Auto-calculado |
| Patience | 50 | ⚠️ Puede aumentarse |
| Conf (validación) | No especificado | ⚠️ Usar default 0.001 |
| Conf (inferencia) | 0.25 | ⚠️ Puede optimizarse |

## 🚀 Recomendaciones de Optimización

### 1. **Aumentar Epochs para Convergencia Completa**

```python
# ACTUAL
EPOCHS = 200

# RECOMENDADO para A100
EPOCHS = 250  # +25% para mejor convergencia desde cero
```

**Justificación**:
- Entrenamiento **desde cero** (sin fine-tuning) necesita más epochs
- YOLOv8 oficial recomienda 300 epochs para mejor performance
- Con A100: 250 epochs ≈ 15-20 horas (totalmente viable)
- Early stopping con patience=75 evita overfitting

**Mejora esperada**: +1-2% mAP50

---

### 2. **Optimizar Patience (Early Stopping)**

```python
# ACTUAL
patience=50

# RECOMENDADO
patience=75  # 30% del total de epochs (250 * 0.30)
```

**Justificación**:
- Patience debe ser ~30% de epochs totales
- Con 250 epochs → patience=75 da más margen para mejorar
- Evita detención prematura en plateaus temporales

---

### 3. **Configurar Confidence Thresholds Explícitamente**

```python
# AGREGAR ANTES DEL ENTRENAMIENTO
CONF_THRESHOLD = 0.001   # Para validación (calcula mAP en todo el rango)
CONF_INFERENCE = 0.30    # Para producción (balance precision/recall)

# EN model.train()
results = model.train(
    data=f'{EXTRACT_DIR}/data.yaml',
    # ... otros parámetros ...
    
    # === Thresholds de Validación ===
    conf=CONF_THRESHOLD,  # 0.001 → calcula mAP en todo el rango de confianza
    iou=0.6,              # IOU threshold para matching (default óptimo)
    
    # ... resto de parámetros ...
)
```

**Justificación**:
- **conf=0.001** durante validación: Calcula precision/recall en todo el espectro de confianza → mAP más preciso
- **conf=0.30** en producción: Reduce falsos positivos (~20% más que 0.25)
- **iou=0.6**: Umbral estándar para matching predictions con ground truth

**Mejora esperada**: +0.5-1% mAP50 (por cálculo más preciso)

---

### 4. **Ajustar Batch para A100 (40GB)**

```python
# El script ya hace auto-batch, pero verificar que use batch óptimo

# VALORES ESPERADOS A100 (40GB) con YOLO26l @ 1280:
# - Batch detectado: ~12-16
# - Batch seguro (75%): ~8-12

# Si batch < 8 → Revisar:
# 1. ¿Estás en A100 o en T4?
# 2. ¿Hay otros procesos usando GPU?
# 3. Considera YOLO26m (menos parámetros) si persiste OOM

# RECOMENDACIÓN A100:
BATCH_SIZE = 12  # Balance óptimo velocidad/estabilidad
```

**Justificación**:
- A100 tiene 40GB VRAM → puede manejar batch=12-16 con imgsz=1280
- Batch más grande = gradientes más estables = mejor convergencia
- Si usas batch=16, reduce a 12-14 para evitar OOM con augmentations pesados

---

### 5. **Optimizar Data Augmentation para 1280**

```python
# ACTUAL (ya está bien configurado)
mosaic=1.0,
mixup=0.05,
erasing=0.3,

# OPCIONAL: Si ves overfitting en curvas
mosaic=1.0,
mixup=0.10,      # Aumentar ligeramente (5% → 10%)
erasing=0.4,     # Más random erasing
copy_paste=0.15, # Más copy-paste (10% → 15%)
```

**Cuándo aplicar**:
- Si **train loss << val loss** (overfitting)
- Si **mAP val > 0.90** pero **mAP test << 0.90**

**Cuándo NO aplicar**:
- Si modelo ya generaliza bien
- Si augmentation actual funciona

---

### 6. **Configurar Validaciones Intermedias**

```python
# EN model.train()
results = model.train(
    # ... otros parámetros ...
    
    val=True,              # ✅ Ya configurado
    plots=True,            # ✅ Ya configurado
    save_period=10,        # ✅ Ya configurado (checkpoint cada 10 epochs)
    
    # AGREGAR:
    val_period=5,          # Validar cada 5 epochs (más frecuente)
)
```

**Justificación**:
- Validación más frecuente → detecta overfitting antes
- Con 250 epochs: val cada 5 epochs = 50 validaciones totales
- No afecta significativamente el tiempo (val es rápido vs train)

---

### 7. **Usar Test-Time Augmentation (TTA) en Evaluación Final**

```python
# DESPUÉS DEL ENTRENAMIENTO
# === TEST CON TTA ===
tta_metrics = best_model.val(
    data=f'{EXTRACT_DIR}/data.yaml',
    split='test',
    augment=True,  # Test-Time Augmentation
    conf=0.001,    # Threshold bajo para mAP completo
    iou=0.6
)

print(f"\n📊 Mejora con TTA:")
print(f"   mAP50:     {test_metrics.box.map50:.4f} → {tta_metrics.box.map50:.4f} "
      f"(+{(tta_metrics.box.map50 - test_metrics.box.map50)*100:.2f}%)")
```

**Justificación**:
- TTA mejora ~1-3% mAP50 sin reentrenar
- Esencial para reportar métricas finales
- Solo usar en evaluación (no en producción por lentitud)

---

### 8. **Configurar Inference con Confidence Óptimo**

```python
# PARA PREDICCIONES DE EJEMPLO
CONF_INFERENCE = 0.30  # Optimizado para menos FP

sample_results = best_model.predict(
    sample_images[:5],
    conf=CONF_INFERENCE,  # 0.30 → mejor balance precision/recall
    iou=0.5,              # NMS threshold (aunque YOLO26 no usa NMS)
    save=True
)
```

**Curva Precision-Recall por Conf**:

| Conf | Precision | Recall | F1-Score | Uso Recomendado |
|------|-----------|--------|----------|-----------------|
| 0.10 | ~0.65 | ~0.95 | ~0.77 | Exploración (máximo recall) |
| 0.20 | ~0.75 | ~0.90 | ~0.82 | Monitoreo continuo |
| 0.25 | ~0.80 | ~0.85 | ~0.82 | **Default YOLO** |
| **0.30** | **~0.85** | **~0.80** | **~0.82** | ⭐ **Producción balanceada** |
| 0.40 | ~0.90 | ~0.70 | ~0.79 | Alta precisión (reportes) |
| 0.50 | ~0.93 | ~0.60 | ~0.73 | Ultra-conservador |

**Recomendación**: 
- **conf=0.30** para producción (SIRCCD app)
- **conf=0.40** para reportes oficiales (alta confianza)
- **conf=0.20** para monitoreo masivo (no perder daños)

---

## 📋 Configuración Final Optimizada

### Variables Globales

```python
# ====================================================================
# 🎯 OPTIMIZADO PARA A100: Máxima precisión y métricas
# ====================================================================
EPOCHS = 250          # Convergencia completa desde cero
BATCH_SIZE = 12       # Óptimo A100 40GB con YOLO26l @ 1280
IMGSZ = 1280          # Máxima resolución (4x vs 640)

# Confidence thresholds
CONF_THRESHOLD = 0.001   # Validación (calcula mAP en todo el rango)
CONF_INFERENCE = 0.30    # Producción (balance precision/recall)

# Early stopping
PATIENCE = 75         # 30% del total de epochs

# Gradient accumulation (solo si batch < 4)
if BATCH_SIZE <= 4:
    ACCUMULATE = max(1, 16 // BATCH_SIZE)
else:
    ACCUMULATE = 1

print(f"\n🚀 Configuración Optimizada A100:")
print(f"   Modelo:     {MODEL_NAME}")
print(f"   Epochs:     {EPOCHS} (convergencia completa)")
print(f"   Batch:      {BATCH_SIZE} (effective: {BATCH_SIZE * ACCUMULATE})")
print(f"   Resolución: {IMGSZ}x{IMGSZ}")
print(f"   Conf (val): {CONF_THRESHOLD}")
print(f"   Conf (inf): {CONF_INFERENCE}")
print(f"   Paciencia:  {PATIENCE} epochs")
print(f"   Tiempo est: ~18-22 horas en A100")
print(f"\n{'='*60}")
```

### Llamada model.train()

```python
results = model.train(
    # === Dataset ===
    data=f'{EXTRACT_DIR}/data.yaml',
    imgsz=IMGSZ,
    
    # === Training ===
    epochs=EPOCHS,
    batch=BATCH_SIZE,
    
    # === Optimizer ===
    optimizer='auto',             # MuSGD para YOLO26
    lr0=0.01,
    lrf=0.01,
    momentum=0.937,
    cos_lr=True,
    warmup_epochs=3.0,
    warmup_momentum=0.8,
    warmup_bias_lr=0.1,
    weight_decay=0.0005,
    
    # === Augmentation ===
    hsv_h=0.015,
    hsv_s=0.5,
    hsv_v=0.4,
    degrees=10.0,
    translate=0.1,
    scale=0.5,
    shear=3.0,
    perspective=0.0003,
    flipud=0.0,
    fliplr=0.5,
    mosaic=1.0,
    mixup=0.05,
    copy_paste=0.1,
    erasing=0.3,
    close_mosaic=20,
    
    # === Regularización ===
    label_smoothing=0.05,
    dropout=0.0,
    
    # === Thresholds ===
    conf=CONF_THRESHOLD,          # 0.001 para cálculo preciso de mAP
    iou=0.6,                      # IOU matching
    
    # === Guardado ===
    project='/content/drive/MyDrive/SIRCCD_Models',
    name=experiment_name,
    save_period=10,               # Checkpoint cada 10 epochs
    patience=PATIENCE,            # 75 epochs
    
    # === Validación ===
    val=True,
    val_period=5,                 # Validar cada 5 epochs
    plots=True,
    
    # === GPU/Performance ===
    device=0,
    amp=True,                     # FP16 (esencial para 1280)
    cache='disk',                 # Disk cache (1280 usa mucha RAM)
    workers=4,
    deterministic=True,
    seed=42,
    
    # === Otros ===
    pretrained=True,
    verbose=True,
    rect=False,
    resume=False,
)
```

---

## 📊 Métricas Esperadas (A100 + Config Optimizada)

### Comparación con v1 y v2

| Métrica | v1 (YOLOv8m @ 640) | v2 (Fine-tune) | **v3 Optimizado** | Mejora vs v1 |
|---------|-------------------|----------------|-------------------|--------------|
| **mAP50** | 0.795 | 0.810 | **0.88-0.90** | **+8.5-10.5%** |
| **mAP50-95** | 0.539 | 0.560 | **0.62-0.65** | **+8.1-11.1%** |
| **Precision** | 0.810 | 0.825 | **0.87-0.89** | **+6-8%** |
| **Recall** | 0.743 | 0.765 | **0.83-0.86** | **+8.7-11.7%** |

### Por Clase (Estimado)

| Clase | mAP50 | mAP50-95 | Precision | Recall |
|-------|-------|----------|-----------|--------|
| **Bache** | 0.92-0.94 | 0.67-0.70 | 0.90-0.92 | 0.87-0.90 |
| **Grieta** | 0.84-0.86 | 0.57-0.60 | 0.84-0.86 | 0.79-0.82 |

**Nota**: Baches más fáciles de detectar (mayor contraste). Grietas finas mejor detectadas con 1280 vs 640.

---

## ⏱️ Tiempos Estimados (A100 40GB)

| Fase | Tiempo | Detalles |
|------|--------|----------|
| **Setup inicial** | 5-10 min | Descargar dataset de MinIO |
| **Auto-batch calc** | 30-60 seg | Detectar batch óptimo |
| **Entrenamiento** | 18-22 hrs | 250 epochs × ~4-5 min/epoch |
| **Validación final** | 5-10 min | Val + test split |
| **TTA evaluación** | 15-20 min | Test-time augmentation |
| **TOTAL** | **~20-24 hrs** | Fin de semana completo |

**Comparación GPUs**:
- T4 (15GB): ~60-80 horas (3-4x más lento)
- L4 (24GB): ~30-40 horas (2x más lento)
- **A100 (40GB)**: ~20-24 horas ⭐
- H100 (80GB): ~12-15 horas (no disponible en Colab)

---

## 🔧 Troubleshooting

### OOM (Out of Memory)

Si aparece `CUDA out of memory`:

1. **Reducir batch**:
   ```python
   BATCH_SIZE = 8  # En vez de 12
   ```

2. **Reducir resolución** (último recurso):
   ```python
   IMGSZ = 960  # En vez de 1280 (2.25x vs 4x)
   ```

3. **Cambiar a modelo más pequeño**:
   ```python
   MODEL_NAME = 'yolo26m.pt'  # En vez de yolo26l
   ```

### Entrenamiento Muy Lento

Si epochs tardan >10 min cada uno:

1. **Verificar GPU usada**:
   ```python
   import torch
   print(torch.cuda.get_device_name(0))
   # Debe ser: Tesla A100-SXM4-40GB
   ```

2. **Revisar cache**:
   ```python
   cache='ram'  # Probar RAM cache si tienes suficiente
   ```

3. **Reducir workers**:
   ```python
   workers=2  # En vez de 4
   ```

### Overfitting (Train mAP >> Val mAP)

Si `train/mAP50 - val/mAP50 > 0.10`:

1. **Aumentar augmentation**:
   ```python
   mixup=0.10,      # 5% → 10%
   erasing=0.4,     # 0.3 → 0.4
   copy_paste=0.15, # 0.1 → 0.15
   ```

2. **Aumentar regularización**:
   ```python
   label_smoothing=0.10,  # 0.05 → 0.10
   weight_decay=0.001,    # 0.0005 → 0.001
   ```

3. **Reducir epochs**:
   - Dejar que early stopping actúe (patience=75 lo manejará)

### Underfitting (Train y Val mAP bajos)

Si ambos mAP50 < 0.75:

1. **Aumentar epochs**:
   ```python
   EPOCHS = 300  # 250 → 300
   ```

2. **Reducir augmentation**:
   ```python
   mixup=0.02,   # Menos mixup
   erasing=0.2,  # Menos erasing
   ```

3. **Ajustar learning rate**:
   ```python
   lr0=0.015,  # 0.01 → 0.015 (más agresivo)
   ```

---

## 📝 Checklist Pre-Entrenamiento

Antes de ejecutar el notebook v3:

- [ ] **GPU**: Verificar A100 40GB en Colab
- [ ] **Dataset**: Descargar de MinIO (v1.0.0)
- [ ] **Drive**: Espacio suficiente (~10 GB para checkpoints)
- [ ] **Config**: Ajustar `EPOCHS=250`
- [ ] **Config**: Ajustar `PATIENCE=75`
- [ ] **Config**: Agregar `conf=0.001` en train()
- [ ] **Config**: Definir `CONF_INFERENCE=0.30`
- [ ] **Config**: Agregar `iou=0.6` en train()
- [ ] **Config**: Agregar `val_period=5`
- [ ] **Batch**: Verificar auto-batch detecta ~12-16
- [ ] **Tiempo**: Reservar 24 horas de GPU (fin de semana)

---

## 🎯 Métricas Objetivo (Para Considerar Éxito)

### Mínimo Aceptable
- mAP50 ≥ 0.85
- mAP50-95 ≥ 0.60
- Precision ≥ 0.82
- Recall ≥ 0.78

### Objetivo Deseable
- mAP50 ≥ 0.88
- mAP50-95 ≥ 0.63
- Precision ≥ 0.86
- Recall ≥ 0.82

### Excelente (Supera v1 significativamente)
- mAP50 ≥ 0.90
- mAP50-95 ≥ 0.65
- Precision ≥ 0.88
- Recall ≥ 0.85

---

## 📚 Referencias

- [YOLOv8 Training Tips](https://docs.ultralytics.com/guides/yolo-performance-metrics/)
- [YOLO26 Paper (arXiv)](https://arxiv.org/abs/2501.12900)
- [Confidence Threshold Tuning](https://docs.ultralytics.com/modes/predict/#inference-arguments)
- [Test-Time Augmentation](https://docs.ultralytics.com/modes/val/#augmentation)
- [A100 GPU Specs](https://www.nvidia.com/en-us/data-center/a100/)

---

## 🔄 Próximos Pasos Después del Entrenamiento

1. **Evaluar con TTA** (Test-Time Augmentation)
2. **Exportar a ONNX** para producción
3. **Comparar con v1/v2** en imágenes reales
4. **Calibrar threshold** para producción (ROC curve)
5. **Documentar resultados** en M-02
6. **Integrar mejor modelo** en backend API

---

**Fecha de creación**: 2026-02-20
**Versión**: 1.0
**Autor**: SIRCCD ML Team
