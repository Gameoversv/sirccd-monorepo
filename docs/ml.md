# Modulo ML

## 1) Proposito del modulo

El modulo ML concentra todo el ciclo de vida de datos y modelos para:

1. deteccion de dano vial,
2. anonimizado de imagenes,
3. soporte de embeddings para deduplicacion.

## 2) Como se implemento

Se separaron las responsabilidades por dominio tecnico:

- datos y preparacion en `datasets/`,
- entrenamiento y experimentacion en `train/` y `notebooks/`,
- artefactos en `models/` y `runs/`,
- anonimizado en `anonymization/`,
- soporte de dedup/embeddings en `deduplication/` y `embeddings/`.

La estructura esta preparada para flujo reproducible de entrenamiento y para publicar artefactos consumidos por backend.

## 3) Donde esta cada cosa

### 3.1 Anonimizado

- `anonymization/train.py`: entrenamiento del modelo de anonimizado.
- `anonymization/inference.py`: inferencia de anonimizado.
- `anonymization/data.yaml`: configuracion de datos para anonimizado.
- `anonymization/scripts/`: utilidades de preparacion/soporte.
- `anonymization/notebooks/`: notebooks del subflujo de anonimizado.
- `anonymization/docs/`: documentacion tecnica de anonimizado.

### 3.2 Datasets

- `datasets/`: repositorio de insumos y salidas de datos.
- `datasets/pois_google/`: datos de POIs para contexto geoespacial.

### 3.3 Entrenamiento y experimentacion

- `train/`: scripts de entrenamiento estructurado.
- `notebooks/01_dataset_exploration.ipynb`: exploracion inicial de datos.
- `notebooks/SIRCCD_Training_Colab.ipynb`: entrenamiento base en Colab.
- `notebooks/SIRCCD_Training_v3_FromScratch.ipynb`: entrenamiento desde cero.
- `notebooks/SIRCCD_Training_v4_YOLO11l.ipynb`: variante YOLO11l.
- `notebooks/SIRCCD_Training_v5_H100_Optimized.ipynb`: optimizacion para H100.
- `notebooks/SIRCCD_Anonymization_Training.ipynb`: entrenamiento de anonimizado.

### 3.4 Inferencia y soporte de similitud

- `inference/`: pruebas/utilidades de inferencia.
- `embeddings/`: pruebas y utilidades de embeddings.
- `deduplication/`: soporte experimental de deduplicacion en ML.

### 3.5 Artefactos y configuracion

- `models/`: modelos entrenados exportados.
- `runs/`: salidas de ejecucion de entrenamientos.
- `configs/`: configuraciones de entrenamiento/ejecucion.
- `requirements-training.txt`: dependencias del modulo ML.

### 3.6 Scripts de utileria

- `scripts/verify_environment.py`: verificacion de entorno.
- `scripts/download_from_minio.py`: descarga de artefactos desde MinIO.
- `scripts/upload_to_minio.py`: subida de artefactos a MinIO.
- `scripts/utils/`: helpers de soporte.

### 3.7 Documentacion interna ML

En `ml/docs/` se mantienen guias operativas especificas:

- setup y entorno (`M-01_ENVIRONMENT_SETUP.md`),
- entrenamiento en colab (`GUIA_*`, `CHECKLIST_COLAB.md`),
- optimizacion (`V3_TRAINING_OPTIMIZATION.md`),
- nube (`CLOUD_TRAINING.md`),
- compatibilidad Python (`PYTHON_314_COMPATIBILITY_ISSUE.md`).

## 4) Flujo operativo recomendado

1. validar entorno de entrenamiento,
2. preparar datos,
3. entrenar y registrar metrica,
4. evaluar resultados,
5. versionar/publicar artefactos,
6. integrar artefactos con backend.

## 5) Setup basico

```powershell
cd ml
pip install -r requirements-training.txt
```

Para sesiones largas, usar Colab o GPU dedicada.

## 6) Integracion con backend

Backend consume desde ML:

1. pesos/modelos,
2. configuraciones de inferencia,
3. resultados de evaluacion para calibracion.
