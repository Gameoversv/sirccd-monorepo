# D-07: Ingesta de Dataset a MinIO

## Objetivo

Almacenar el dataset procesado en MinIO (S3-compatible) con metadatos organizados, versionamiento y estructura clara para acceso reproducible.

---

## 1. Configuración de MinIO

### Levantar contenedor MinIO

```bash
# Desde la raíz del proyecto
docker-compose -f docker-compose.minio.yml up -d
```

### Acceso

- **API:** http://localhost:9000
- **Consola Web:** http://localhost:9001
- **Usuario:** `sirccd_admin`
- **Contraseña:** `sirccd_password_2026`

---

## 2. Estructura del Bucket

```
sirccd-datasets/
└── v1.0.0/
    ├── metadata.json
    ├── train/
    │   ├── images/
    │   │   ├── rdd2022_*.jpg
    │   │   ├── rdd2020_*.jpg
    │   │   └── ...
    │   └── labels/
    │       ├── rdd2022_*.txt
    │       └── ...
    ├── val/
    │   ├── images/
    │   └── labels/
    └── test/
        ├── images/
        └── labels/
```

---

## 3. Metadatos del Dataset

Cada archivo subido incluye metadatos personalizados:

| Metadato | Descripción | Ejemplo |
|----------|-------------|---------|
| `dataset-version` | Versión del dataset | `v1.0.0` |
| `split` | Train, val o test | `train` |
| `type` | Imagen o label | `image` |
| `file-hash` | SHA256 del archivo | `a3b5c7...` |
| `uploaded-at` | Timestamp de subida | `2026-02-02T14:30:00` |

### Archivo metadata.json

```json
{
  "name": "SIRCCD Road Damage Dataset",
  "version": "v1.0.0",
  "created_at": "2026-02-02T14:30:00",
  "classes": ["bache", "grieta"],
  "splits": ["train", "val", "test"],
  "source_datasets": ["RDD2022", "RDD2020", "N-RDD2024", "Pothole-600"],
  "seed": 42,
  "total_images": 58209
}
```

---

## 4. Proceso de Ingesta

### Paso 1: Instalar dependencias

```bash
pip install minio
```

### Paso 2: Ejecutar script de ingesta

```bash
# Desde el directorio raíz del monorepo
python ml/datasets/scripts/upload_to_minio.py
```

### Salida esperada

```
📦 INGESTA DE DATASET A MinIO (D-07)
🔌 Conectando a MinIO...
✅ Bucket 'sirccd-datasets' creado
📄 Subiendo metadatos del dataset...
✅ Metadatos subidos: v1.0.0/metadata.json

📤 Subiendo split: train
  Imágenes: 1000
  Imágenes: 2000
  ...
  ✅ train: 40745 imágenes, 40745 labels

📤 Subiendo split: val
  ✅ val: 11641 imágenes, 11641 labels

📤 Subiendo split: test
  ✅ test: 5823 imágenes, 5823 labels

✅ INGESTA COMPLETADA
Bucket: sirccd-datasets
Versión: v1.0.0
Total imágenes: 58209
Total labels: 58209
```

---

## 5. Versionamiento

### Estrategia de Versiones

| Versión | Descripción |
|---------|-------------|
| `v1.0.0` | Dataset inicial con RDD2022, RDD2020, N-RDD2024, Pothole-600 |
| `v1.1.0` | Agregar nuevos datasets o correcciones menores |
| `v2.0.0` | Cambios estructurales (nuevas clases, formato diferente) |

### Subir nueva versión

1. Actualizar `DATASET_VERSION` en `ml/datasets/scripts/upload_to_minio.py`
2. Ejecutar script de ingesta
3. La nueva versión coexiste con las anteriores (no se sobreescribe)

---

## 6. Descarga y Uso

### Descargar un split completo

```python
from minio import Minio

client = Minio(
    "localhost:9000",
    access_key="sirccd_admin",
    secret_key="sirccd_password_2026",
    secure=False
)

# Descargar todas las imágenes de train
objects = client.list_objects("sirccd-datasets", prefix="v1.0.0/train/images/", recursive=True)
for obj in objects:
    client.fget_object("sirccd-datasets", obj.object_name, f"downloaded/{obj.object_name}")
```

### Verificar integridad con hash

```python
import hashlib

def verify_file(file_path, expected_hash):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest() == expected_hash

# Obtener metadatos del objeto
stat = client.stat_object("sirccd-datasets", "v1.0.0/train/images/rdd2022_001.jpg")
expected_hash = stat.metadata.get("X-Amz-Meta-File-Hash")
verify_file("local_file.jpg", expected_hash)
```

---

## 7. Ventajas del Sistema

✅ **Versionamiento:** Múltiples versiones coexisten sin conflictos  
✅ **Metadatos:** Trazabilidad completa de cada archivo  
✅ **Reproducibilidad:** Hash SHA256 garantiza integridad  
✅ **S3-compatible:** Fácil migración a AWS S3, GCP Storage, etc.  
✅ **Centralizado:** Acceso compartido para equipo de desarrollo  

---

## 8. Seguridad y Acceso

### Crear políticas de acceso (opcional)

```bash
# En MinIO Console (http://localhost:9001)
# 1. Crear política de solo lectura para usuarios externos
# 2. Crear usuarios con permisos específicos
# 3. Configurar buckets públicos/privados según necesidad
```

---

**Documento creado:** Febrero 2026  
**Proyecto:** SIRCCD - Sistema Inteligente de Reporte y Clasificación de Daños Viales
