# Machine Learning

[← Volver al índice](../README.md)

## Resumen

El módulo `ml/` (raíz del repo) cubre dos capacidades distintas del sistema:

1. **Detección de daños viales** (baches/grietas) — en fase de entrenamiento/experimentación offline, vía notebooks de Google Colab. **No se sirve en producción todavía**: la detección real en producción usa la API externa de Roboflow (ver `backend/services/ml_service.py`).
2. **Anonimización de imágenes** (blur de rostros/placas) — sí se ejecuta en producción, integrada directamente en el backend (`backend/services/anonymizer.py`, que importa YOLO desde `ultralytics`).

## Estado de desacoplamiento

`ml/` no es un servicio desplegado. Sus artefactos (pesos de modelo, resultados de entrenamiento) se generan en Colab y se intercambian manualmente vía Google Drive o MinIO (`ml/scripts/upload_to_minio.py`, `download_from_minio.py`) — no hay integración de código directa entre `ml/` (entrenamiento de detección) y `backend/` más allá de ese intercambio de archivos. La única integración de código real es el pipeline de anonimización.

## Framework y stack

Ultralytics (YOLO), PyTorch/torchvision, Albumentations (aumentaciones), FAISS, Weights & Biases (tracking de experimentos), geopandas — ver `ml/requirements-training.txt`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `ml/anonymization/` | Pipeline activo de anonimización: `train.py`, `inference.py`, `data.yaml`, scripts propios de dataset (WIDERFace, placas), documentación en `ml/anonymization/docs/` |
| `ml/models/baseline/` | Métricas/configuración de una corrida base de entrenamiento (YOLOv8m, mAP50 ~0.698–0.795 según el documento de referencia) — sin pesos `.pt` versionados en git |
| `ml/notebooks/` | 6 notebooks de Colab, incluyendo una cadena versionada de entrenamiento (`v3_FromScratch`, `v4_YOLO11l`, `v5_H100_Optimized`) sin indicación explícita de cuál es la vigente |
| `ml/scripts/` | `download_from_minio.py`, `upload_to_minio.py`, `verify_environment.py` |
| `ml/docs/` | 9 documentos existentes (guías de Colab, diagnóstico de modelo, optimización de entrenamiento) — **no se duplican aquí**, ver índice abajo |
| `ml/deduplication/`, `embeddings/`, `inference/`, `train/`, `utils/` | Carpetas planificadas, actualmente vacías (solo `.gitkeep`) |

## Documentación de entrenamiento existente

La documentación detallada de entrenamiento (guías de Colab, diagnóstico de modelo, optimización) ya existe y está relativamente actualizada (últimos commits entre 2026-02-17 y 2026-03-06) — se referencia en vez de duplicarse:

- `ml/docs/GUIA_INICIO_RAPIDO_COLAB.md`, `GUIA_RAPIDA_COLAB.md`, `CHECKLIST_COLAB.md` — guías operativas de Colab.
- `ml/docs/GUIA_MEJORAS_MODELO.md` — diagnóstico de modelo (recall, deduplicación de dataset).
- `ml/docs/V3_TRAINING_OPTIMIZATION.md` — recomendación de configuración YOLO26l para entrenamiento en A100.
- `ml/docs/M-01_ENVIRONMENT_SETUP.md`, `PYTHON_314_COMPATIBILITY_ISSUE.md`, `GUIA_CONTINUAR_ENTRENAMIENTO.md`, `CLOUD_TRAINING.md` — setup de entorno y continuidad de entrenamiento.
- `ml/anonymization/docs/ANONYMIZATION_TRAINING_PLAN.md` — plan de entrenamiento del modelo de anonimización.

## Limitaciones y pendientes

- No hay versionado formal de modelos (sin registro tipo MLflow/DVC) — el "modelo vigente" se infiere de cuál notebook o carpeta es la más reciente, no de un sistema de versionado explícito.
- No se pudieron verificar métricas de evaluación más recientes que las documentadas en `ml/docs/GUIA_MEJORAS_MODELO.md`; cualquier métrica no registrada en el repositorio no se afirma en esta documentación.
- Sin pipeline de CI para `ml/` (ver [infrastructure/CI_CD.md](../infrastructure/CI_CD.md)).
- Notebooks `v3`/`v4`/`v5` sin indicación de cuál es la versión de referencia actual — marcado como pendiente de validación manual en [REPOSITORY_AUDIT.md](../REPOSITORY_AUDIT.md#6-código-potencialmente-obsoleto).
