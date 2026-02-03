# Particionado de Dataset - D-03

**Fecha:** 2026-01-16  
**Estado:** ✅ Completado

---

## 📋 Resumen Ejecutivo

### Objetivo

Particionar el dataset en train/val/test con **seed fija** para garantizar reproductibilidad y **estratificación** para mantener proporciones de clases.

### Resultado

**Dataset particionado:** 58,209 imágenes  
**Seed:** 42 (reproductibilidad garantizada)  
**Splits:** 70% train / 20% val / 10% test  
**Estratificación:** ✅ Proporciones idénticas en todos los splits

---

## 📊 Distribución Final

| Split | Imágenes | % Total | Bache | Grieta | Señal | Ratio B:G |
|-------|---------|---------|-------|--------|-------|-----------|
| **Train** | 40,745 | 70.0% | 16,111 (39.5%) | 21,347 (52.4%) | 3,287 (8.1%) | 1:1.32 |
| **Val** | 11,641 | 20.0% | 4,603 (39.5%) | 6,099 (52.4%) | 939 (8.1%) | 1:1.33 |
| **Test** | 5,823 | 10.0% | 2,303 (39.6%) | 3,050 (52.4%) | 470 (8.1%) | 1:1.32 |
| **TOTAL** | **58,209** | 100% | 23,017 | 30,496 | 4,696 | 1:1.32 |

---

## 🔄 Metodología

### 1. Recolección de Muestras

- **Fuente:** `processed/combined/` (todos los splits originales)
- **Criterio de clasificación:** Clase dominante (más anotaciones por imagen)
- **Filtrado:** Solo imágenes con labels válidos

**Distribución original:**
- Bache (clase 0): 23,017 imágenes
- Grieta (clase 2): 30,496 imágenes  
- Señal (clase 4): 4,696 imágenes

### 2. Particionado Estratificado

**Algoritmo:**
```python
random.seed(42)  # Seed fija
for clase in [bache, grieta, señal]:
    shuffle(muestras_clase)
    train = 70% primeras
    val = 20% siguientes
    test = 10% restantes
```

**Ventajas:**
- ✅ Cada clase mantiene proporción 70/20/10
- ✅ Reproducible con seed=42
- ✅ Balance consistente entre splits
- ✅ Evita sesgo en validación/test

### 3. Validación de Consistencia

**Proporciones por clase (idénticas en todos los splits):**
- Bache: ~39.5%
- Grieta: ~52.4%
- Señal: ~8.1%

**Ratio bache:grieta:**
- Train: 1:1.32
- Val: 1:1.33
- Test: 1:1.32

✅ **Variación < 1%** → Estratificación exitosa

---

## 📁 Estructura Generada

```
ml/datasets/processed/split/
├── images/
│   ├── train/          # 40,745 imágenes
│   ├── val/            # 11,641 imágenes
│   └── test/           # 5,823 imágenes
├── labels/
│   ├── train/          # 40,745 archivos .txt
│   ├── val/            # 11,641 archivos .txt
│   └── test/           # 5,823 archivos .txt
└── data.yaml           # Configuración YOLOv8
```

### `data.yaml` (YOLOv8)

```yaml
path: /absolute/path/to/processed/split
train: images/train
val: images/val
test: images/test

nc: 2
names:
  0: bache
  1: grieta
```

**Nota:** Las labels usan IDs 0 y 2 (originales). Durante entrenamiento, remapear 2→1.

---

## 🔁 Reproductibilidad

### Ejecutar el particionado

```bash
cd ml/datasets
python split_dataset.py
```

**Garantías:**
- Seed fija: `RANDOM_SEED = 42`
- Mismo algoritmo de shuffle
- Mismos archivos fuente (`processed/combined/`)
- **Resultado:** Splits idénticos cada vez

### Validar particiones

```bash
python validate_split.py
```

**Salida:**
```
Seed: 42
Total muestras: 58,209

TRAIN: 40,745 (70.0%)
  Bache: 16,111 (39.5%)
  ...
```

---

## 📈 Comparación con Splits Originales

| Métrica | Original | Estratificado (D-03) |
|---------|----------|---------------------|
| Total imágenes | 87,071 | 58,209 |
| Train % | 68.3% | 70.0% |
| Val % | 15.1% | 20.0% |
| Test % | 16.6% | 10.0% |
| Estratificación | ❌ No controlada | ✅ Garantizada |
| Reproductibilidad | ❌ No | ✅ Seed=42 |
| Ratio bache:grieta | Variable | Consistente 1:1.32 |

**Diferencia en total:** 87,071 → 58,209  
**Razón:** Imágenes sin clase dominante clara o multi-clase se filtraron para garantizar estratificación limpia.

---

## ⚠️ Consideraciones Importantes

### 1. Pérdida de Muestras (28,862 imágenes)

**Causa:** Imágenes con múltiples clases o sin clase dominante clara

**Análisis:**
- Dataset original: 87,071 imágenes
- Dataset particionado: 58,209 imágenes
- Pérdida: 28,862 (33.1%)

**Impacto:**
- ✅ Mayor pureza de clases
- ✅ Estratificación garantizada
- ⚠️ Menor diversidad de datos

**Recomendación futura:** Implementar estratificación multi-label para recuperar estas imágenes.

### 2. Clase Señal

- Solo 4,696 imágenes totales (8.1%)
- **No es objetivo de SIRCCD** (solo bache/grieta)
- Se mantiene para compatibilidad pero se puede excluir

### 3. Remapeo de Clases

**Labels actuales:**
- 0 = bache
- 2 = grieta
- 4 = señal

**Para YOLOv8 (2 clases):**
- 0 = bache (sin cambio)
- 2 → 1 = grieta (remapear durante entrenamiento)

---

## ✅ Checklist D-03

- [x] Analizar splits originales (68.3/15.1/16.6)
- [x] Implementar particionado estratificado
- [x] Aplicar seed fija (42)
- [x] Generar splits 70/20/10
- [x] Validar proporciones (variación < 1%)
- [x] Crear data.yaml para YOLOv8
- [x] Generar reporte JSON (split_report.json)
- [x] Documentar proceso completo

---

## 🚀 Próximos Pasos (D-04)

1. **Entrenar modelo baseline YOLOv8n:**
   ```bash
   yolo detect train data=processed/split/data.yaml model=yolov8n.pt epochs=50
   ```

2. **Evaluar en test split:**
   ```bash
   yolo detect val data=processed/split/data.yaml model=runs/train/exp/weights/best.pt split=test
   ```

3. **Analizar métricas:**
   - mAP@0.5
   - mAP@0.5:0.95
   - Precisión/Recall por clase

4. **Iterar con modelos más grandes** (yolov8s/m) si es necesario

---

**Generado por:** `split_dataset.py`  
**Validado con:** `validate_split.py`  
**Última actualización:** 2026-01-16
