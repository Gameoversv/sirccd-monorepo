# Resumen de Conversión de Datasets

## Tarea: D-01 - Organizar y Convertir Datasets a YOLO

**Fecha:** 2024
**Estado:** ✅ COMPLETADO

---

## 📊 Resultados

### Datasets Procesados

| Dataset | Imágenes | Splits | Formato Original | Conversión |
|---------|----------|--------|------------------|------------|
| **RDD2022** | 38,385 | train/val/test | YOLO ✅ | Remapeo de clases |
| **RDD2020** | 26,660 | train/val/test | YOLO ✅ | Remapeo de clases |
| **N-RDD2024** | 21,426 | train/valid/test | YOLO ✅ | Remapeo de clases |
| **TOTAL** | **86,471** | - | - | **100% procesado** |

### Estadísticas Globales

```
Total de imágenes:      86,471
Total de anotaciones:   138,608
Promedio anotaciones/imagen: 1.60

Distribución por Split:
  - train:    59,260 (68.5%)
  - val:      12,960 (15.0%)
  - test:     14,251 (16.5%)

Distribución por Clase:
  - bache:    46,184 (33.3%)
  - grieta:   79,336 (57.2%)
  - senal:    13,088 (9.4%)
  - socavon:  0 (0.0%)
  - alcantarilla: 0 (0.0%)
  - alumbrado: 0 (0.0%)
```

---

## 🗂️ Estructura Generada

```
ml/datasets/
├── processed/
│   └── combined/
│       ├── images/
│       │   ├── train/         # 59,260 imágenes
│       │   ├── val/           # 12,960 imágenes
│       │   └── test/          # 14,251 imágenes
│       ├── labels/
│       │   ├── train/         # 59,260 archivos .txt
│       │   ├── val/           # 12,960 archivos .txt
│       │   └── test/          # 14,251 archivos .txt
│       └── data.yaml          # Config para YOLO training
├── metadata/
│   ├── class_mapping.json     # Mapeo de clases original → SIRCCD
│   └── dataset_stats.json     # Estadísticas detalladas
└── raw/                       # Datasets originales (gitignored)
```

---

## 🔄 Mapeo de Clases

### RDD2022 / RDD2020

| Clase Original | Descripción | Clase SIRCCD | ID |
|----------------|-------------|--------------|-----|
| D00 | Longitudinal crack | grieta | 2 |
| D10 | Transverse crack | grieta | 2 |
| D20 | Alligator crack | bache | 0 |
| D40 | Pothole | bache | 0 |

### N-RDD2024

| Clase Original | Clase SIRCCD | ID |
|----------------|--------------|-----|
| crack | grieta | 2 |
| pothole | bache | 0 |
| patch | grieta | 2 |

---

## 📝 Nomenclatura de Archivos

Las imágenes y labels fueron renombrados con prefijos para identificar el dataset de origen:

```
rdd2022_India_000051.jpg      # RDD2022
rdd2022_India_000051.txt

rdd2020_Norway_004127.jpg     # RDD2020
rdd2020_Norway_004127.txt

nrdd_IMG_20230815_121045.jpg  # N-RDD2024
nrdd_IMG_20230815_121045.txt
```

---

## 🎯 Clases SIRCCD Definidas

| ID | Clase | Descripción | Presente en Datasets |
|----|-------|-------------|---------------------|
| 0 | bache | Baches y deterioros severos | ✅ 46,184 |
| 1 | socavon | Socavones (hundimientos grandes) | ❌ 0 |
| 2 | grieta | Grietas longitudinales/transversales | ✅ 79,336 |
| 3 | alcantarilla | Tapas de alcantarilla dañadas | ❌ 0 |
| 4 | senal | Señalización deteriorada | ✅ 13,088 |
| 5 | alumbrado | Alumbrado público dañado | ❌ 0 |

**Nota:** Las clases 1, 3, y 5 no están presentes en los datasets actuales. Requerirán:
- Recolección de datos locales (SIRCCD app)
- Data augmentation
- Datasets adicionales

---

## 🔧 Archivos de Configuración

### data.yaml (YOLOv8 Training Config)

```yaml
path: C:\Users\wilki\sirccd-monorepo\sirccd-monorepo\ml\datasets\processed\combined
train: images/train
val: images/val
test: images/test
nc: 6
names:
  0: bache
  1: socavon
  2: grieta
  3: alcantarilla
  4: senal
  5: alumbrado
```

### class_mapping.json

Contiene el mapeo completo de:
- Clases originales de cada dataset
- Clases SIRCCD de destino
- IDs numéricos para training

---

## ✅ Validaciones Realizadas

1. **Integridad de archivos:**
   - Cada imagen tiene su archivo .txt correspondiente
   - Todas las anotaciones tienen coordenadas válidas (0-1)
   
2. **Formato YOLO:**
   - class_id x_center y_center width height
   - Valores normalizados entre 0 y 1
   
3. **Splits balanceados:**
   - train: 68.5%
   - val: 15.0%
   - test: 16.5%

---

## 📦 Control de Versiones (Git)

### Archivos Versionados (~50KB)
- `organize_datasets.py`
- `copy_datasets.ps1`
- `*.md` (documentación)
- `data.yaml`
- `class_mapping.json`
- `dataset_stats.json`

### Archivos Ignorados (13.9GB)
- `raw/**` (datasets originales)
- `processed/**` (datasets convertidos)

---

## 🚀 Próximos Pasos

1. **Entrenar modelo baseline:**
   ```bash
   yolo detect train data=ml/datasets/processed/combined/data.yaml model=yolov8n.pt epochs=100
   ```

2. **Evaluar rendimiento:**
   ```bash
   yolo detect val data=ml/datasets/processed/combined/data.yaml model=runs/detect/train/weights/best.pt
   ```

3. **Completar datasets pendientes:**
   - Convertir Pothole-600 (máscaras → bboxes)
   - Localizar y procesar CRACK500
   - Procesar CFD

4. **Recolectar datos locales:**
   - Usar SIRCCD app para capturar clases faltantes
   - Enfocarse en: socavon, alcantarilla, alumbrado

---

**Generado por:** `organize_datasets.py`  
**Ubicación:** `ml/datasets/CONVERSION_SUMMARY.md`
Recolectar datos locales para clases faltantes:**
   - Usar SIRCCD app para capturar: socavon, alcantarilla, alumbrado
   - Anotar y agregar a processed/combined/