# Limpieza y Balanceo de Datasets - D-02

**Fecha:** 2026-01-15  
**Estado:** ✅ Completado

---

## 📋 Resumen Ejecutivo

### Validación de Integridad ✅

**Resultado:** Todas las imágenes son válidas

| Split | Total | Válidas | Corruptas | Sin label |
|-------|-------|---------|-----------|-----------|
| Train | 59,500 | 59,500 (100%) | 0 | 0 |
| Val | 13,140 | 13,140 (100%) | 0 | 0 |
| Test | 14,431 | 14,431 (100%) | 0 | 0 |
| **TOTAL** | **87,071** | **87,071 (100%)** | **0** | **0** |

**Tiempo de procesamiento:** ~23 minutos  
**Velocidad promedio:** ~63 imágenes/segundo  
**Datasets incluidos:** RDD2022, RDD2020, N-RDD2024, Pothole-600

---

## 📊 Análisis de Distribución de Clases

### Train (59,500 imágenes)

| Clase | ID | Anotaciones | Imágenes | % Imágenes |
|-------|----|-----------|----|-----------|
| **bache** | 0 | 33,278 | 21,116 | 35.5% |
| **grieta** | 2 | 56,132 | 25,463 | 42.8% |
| **señal** | 4 | 9,256 | 5,198 | 8.7% |
| *Otras* | - | - | 7,723 | 13.0% |

### Val (13,140 imágenes)

| Clase | Anotaciones | Imágenes | % |
|-------|------------|----------|---|
| bache | 7,081 | 4,586 | 34.9% |
| grieta | 12,004 | 5,451 | 41.5% |
| señal | 1,930 | 1,088 | 8.3% |

### Test (14,431 imágenes)

| Clase | Anotaciones | Imágenes | % |
|-------|------------|----------|---|
| bache | 6,444 | 4,036 | 28.0% |
| grieta | 11,200 | 5,088 | 35.3% |
| señal | 1,902 | 1,062 | 7.4% |

**Distribución Total (clases relevantes):**
- **bache**: 29,738 imágenes (45.2%)
- **grieta**: 36,002 imágenes (54.8%)
- **Ratio bache:grieta**: 1:1.21 ✅
- **Señal**: 7,348 imágenes (excluida del proyecto SIRCCD)

---

## 🔍 Detección de Duplicados

**Estado:** ✅ Completado

**Método:** Average Hash (perceptual hashing)
- Resize a 8×8 pixels
- Conversión a escala de grises
- Comparación de valores promedio

**Resultados:**
- **Grupos de duplicados:** 1,699
- **Reporte:** `metadata/duplicates_report.json` (182,445 líneas)
- **Patrón común:** Imágenes compartidas entre RDD2020 y RDD2022 (ej: `rdd2020_Japan_009940` = `rdd2022_Japan_009940`)
- **Decisión:** Mantener duplicados (provienen de datasets oficiales, eliminación podría afectar validación)

---

## ⚖️ Estrategia de Balanceo

### Decisión Final: ✅ NO BALANCEAR

**Justificación:**

1. **Alcance del proyecto SIRCCD redefinido:**
   - Clase `señal` (4) **excluida** del proyecto
   - Solo se detectan: `bache` (0) y `grieta` (2)
   
2. **Distribución bache/grieta:**
   - Bache: 29,738 imágenes (45.2%)
   - Grieta: 36,002 imágenes (54.8%)
   - **Ratio: 1:1.21** ✅ **EXCELENTE BALANCE**
   
3. **Pothole-600 integrado:**
   - +600 imágenes de baches agregadas
   - Mejora ratio de 1:1.22 a 1:1.21
   - Contribución: train +240, val +180, test +180

4. **Ventajas de mantener distribución actual:**
   - Ratio casi perfecto (< 25% de diferencia)
   - No se pierden datos
   - No se generan duplicados artificiales
   - Refleja distribución real de daños viales
   
**Conclusión:** El dataset está **naturalmente balanceado** entre las clases de interés (bache/grieta). No se requiere undersampling ni oversampling.

---

## 📁 Estructura Final

```
ml/datasets/
├── processed/
│   └── combined/          # Dataset completo (87,071 imgs)
│       ├── images/
│       │   ├── train/     # 59,500 imgs
│       │   ├── val/       # 13,140 imgs
│       │   └── test/      # 14,431 imgs
│       └── labels/
└── metadata/
    ├── cleaning_report.json       # Validación de integridad
    ├── duplicates_report.json     # 1,699 grupos duplicados
    └── CLEANING_REPORT.md         # Este documento
```

---

## ✅ Checklist de Tareas D-02

- [x] Validar integridad de imágenes (100% válidas, 0 corruptas)
- [x] Analizar distribución de clases
- [x] Detectar y reportar duplicados (1,699 grupos)
- [x] Procesar Pothole-600 (+600 baches)
- [x] Re-analizar balance final (1:1.21 ratio)
- [x] Decisión de balanceo (NO requerido)
- [x] Documentar resultados finales

---

## 🚀 Próximos Pasos (D-03: Training Pipeline)

1. **Crear `data.yaml`** para YOLOv8:
   ```yaml
   train: ml/datasets/processed/combined/images/train
   val: ml/datasets/processed/combined/images/val
   test: ml/datasets/processed/combined/images/test
   
   nc: 2  # Solo bache y grieta
   names: ['bache', 'grieta']
   ```

2. **Entrenar modelo baseline:**
   ```bash
   yolo detect train data=data.yaml model=yolov8n.pt epochs=50
   ```

3. **Evaluar métricas** en test split

4. **Iterar** con modelos más grandes (yolov8s, yolov8m) si es necesario

---

**Generado por:** `clean_and_balance.py`  
**Última actualización:** 2026-01-15  
**Script:** `ml/datasets/clean_and_balance.py`
