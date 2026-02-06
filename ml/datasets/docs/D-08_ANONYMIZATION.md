# D-08: Anonimización y Protección de Privacidad

## Objetivo

Eliminar información sensible del dataset para proteger la privacidad de individuos y cumplir con regulaciones de protección de datos (GDPR, CCPA, etc.).

## Metadatos EXIF Sensibles

### Información Eliminada

#### GPS y Ubicación
- **GPSLatitude**: Coordenadas exactas de captura
- **GPSLongitude**: Coordenadas exactas de captura  
- **GPSAltitude**: Elevación
- **GPSTimeStamp**: Marca temporal con ubicación
- **GPSDateStamp**: Fecha con ubicación

**Riesgo**: Permite identificar ubicaciones específicas de residencias, establecimientos privados o rutas frecuentes.

#### Información de Usuario
- **UserComment**: Comentarios personales
- **MakerNote**: Notas del fabricante (puede contener datos sensibles)
- **CameraOwnerName**: Nombre del propietario de la cámara
- **Artist**: Autor/fotógrafo
- **Copyright**: Información de derechos de autor

**Riesgo**: Revela identidad del capturador de imágenes.

#### Información de Dispositivo
- **Software**: Aplicación de procesamiento
- **HostComputer**: Computadora de procesamiento
- **Make/Model**: Marca y modelo del dispositivo

**Riesgo**: Permite rastreo de dispositivo específico y potencial identificación.

## Detección de Elementos Sensibles

### 1. Rostros Humanos

**Método**: Haar Cascade Classifier (OpenCV)
```python
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
faces = face_cascade.detectMultiScale(gray, 1.1, 4)
```

**Configuración**:
- Scale factor: 1.1
- Min neighbors: 4
- Blur: Gaussian (51x51, sigma=30)

**Alternativas**:
- MTCNN (Multi-task Cascaded Convolutional Networks)
- RetinaFace
- YOLOv8-face

### 2. Placas Vehiculares

**Método**: YOLOv8 entrenado para detección de placas (futuro)

**Configuración**:
- Modelo: YOLOv8n-plate (por implementar)
- Confidence: 0.5
- Blur: Gaussian (51x51, sigma=30)

**Dataset de entrenamiento sugerido**:
- CCPD (Chinese City Parking Dataset)
- OpenALPR dataset
- Custom dataset México

## Implementación

### Uso Básico

```bash
# Análisis sin modificar archivos
python scripts/anonymize_dataset.py --check-only

# Anonimización completa (eliminar todo EXIF)
python scripts/anonymize_dataset.py

# Mantener EXIF básico (fecha, dimensiones)
python scripts/anonymize_dataset.py --keep-basic-exif

# Con detección de rostros
python scripts/anonymize_dataset.py --detect-faces

# Con detección de placas (requiere modelo)
python scripts/anonymize_dataset.py --detect-plates
```

### Proceso de Anonimización

```
1. Cargar imagen
   ↓
2. Extraer EXIF
   ↓
3. ¿Tiene EXIF sensible?
   ├─ Sí → Eliminar EXIF
   └─ No → Continuar
   ↓
4. ¿Detectar rostros/placas?
   ├─ Sí → Detectar regiones
   │       └─ ¿Encontrados?
   │          └─ Sí → Difuminar regiones
   └─ No → Continuar
   ↓
5. Guardar imagen anonimizada
   ↓
6. Copiar label correspondiente
```

## Estructura de Salida

```
ml/datasets/processed/anonymized/
├── data.yaml                    # Configuración YOLO
├── images/
│   ├── train/                   # Imágenes train anonimizadas
│   ├── val/                     # Imágenes val anonimizadas
│   └── test/                    # Imágenes test anonimizadas
└── labels/
    ├── train/                   # Labels sin modificar
    ├── val/
    └── test/

ml/datasets/metadata/
└── anonymization_report.json    # Reporte detallado
```

## Reporte de Anonimización

### Estructura JSON

```json
{
  "timestamp": "2026-02-02T12:00:00",
  "configuration": {
    "remove_all_exif": true,
    "face_detection": false,
    "plate_detection": false
  },
  "splits": {
    "train": {
      "total": 40543,
      "processed": 40543,
      "exif_removed": 40543,
      "exif_sensitive_found": 1234,
      "faces_found": 5,
      "plates_found": 0,
      "blurred": 5,
      "errors": []
    },
    "val": {...},
    "test": {...}
  },
  "summary": {
    "total_images": 57976,
    "processed": 57976,
    "exif_removed": 57976,
    "sensitive_found": 3456,
    "faces_detected": 12,
    "plates_detected": 0,
    "images_blurred": 12
  }
}
```

### Métricas Clave

- **total_images**: Total de imágenes procesadas
- **exif_removed**: Imágenes con EXIF eliminado
- **sensitive_found**: Imágenes con EXIF sensible detectado
- **faces_detected**: Total de rostros encontrados
- **plates_detected**: Total de placas encontradas
- **images_blurred**: Imágenes con difuminado aplicado

## Técnicas de Difuminado

### Gaussian Blur

```python
blurred = cv2.GaussianBlur(roi, (51, 51), 30)
```

**Parámetros**:
- Kernel: 51x51 (suficientemente grande para rostros/placas)
- Sigma: 30 (desviación estándar alta para difuminado fuerte)

**Ventajas**:
- Rápido
- Irreversible sin información original
- No afecta detección de baches/grietas

### Alternativas Consideradas

#### Pixelación
```python
pixelated = cv2.resize(roi, (10, 10), interpolation=cv2.INTER_LINEAR)
pixelated = cv2.resize(pixelated, (w, h), interpolation=cv2.INTER_NEAREST)
```

**Desventaja**: Puede ser reversible con super-resolución.

#### Ennegrecimiento
```python
img[y:y+h, x:x+w] = 0
```

**Desventaja**: Puede afectar contexto visual.

## Validación de Anonimización

### 1. Verificar EXIF Eliminado

```python
from PIL import Image
import piexif

img = Image.open('anonymized/train/image_001.jpg')
assert 'exif' not in img.info  # ✓ Sin EXIF
```

### 2. Verificar Difuminado

```python
import cv2

original = cv2.imread('original/train/image_001.jpg')
anonymized = cv2.imread('anonymized/train/image_001.jpg')

# Si hay rostros detectados, las regiones deben ser diferentes
diff = cv2.absdiff(original, anonymized)
assert diff.sum() > 0  # ✓ Imagen modificada
```

### 3. Verificar Labels Preservados

```python
with open('anonymized/labels/train/image_001.txt') as f:
    labels = f.readlines()

assert len(labels) > 0  # ✓ Labels copiados
```

## Consideraciones de Privacidad

### Dataset Original

❌ **NO compartir públicamente**
- Contiene metadatos GPS
- Puede contener información de usuario
- Ubicaciones exactas de captura

### Dataset Anonimizado

✅ **Seguro para compartir**
- Sin metadatos sensibles
- Rostros/placas difuminados
- Solo información de baches/grietas

### Recomendaciones GDPR/CCPA

1. **Minimización de datos**: Solo conservar información necesaria para detección de daños
2. **Derecho al olvido**: Poder eliminar imágenes específicas si se solicita
3. **Consentimiento**: Idealmente, tener consentimiento para captura (vía pública = dominio público)
4. **Seguridad**: Almacenar dataset original en ubicación segura con acceso restringido
5. **Documentación**: Mantener registro de proceso de anonimización

## Dependencias

### Requeridas

```txt
Pillow>=10.0.0          # Manipulación de imágenes
piexif>=1.1.3           # Lectura/escritura EXIF
tqdm>=4.65.0            # Barras de progreso
```

### Opcionales

```txt
opencv-python>=4.8.0    # Detección de rostros/placas
```

## Limitaciones Conocidas

1. **Detección de rostros**: Haar Cascade puede fallar con:
   - Rostros de perfil
   - Rostros parcialmente ocultos
   - Iluminación extrema
   
2. **Detección de placas**: Requiere modelo entrenado específicamente para:
   - Placas mexicanas
   - Diferentes ángulos
   - Condiciones de iluminación

3. **Performance**: Procesamiento secuencial puede ser lento
   - **Solución**: Implementar procesamiento paralelo con multiprocessing

## Mejoras Futuras

### M-01: Detección de Rostros Mejorada
- [ ] Implementar MTCNN o RetinaFace
- [ ] Detectar rostros en múltiples orientaciones
- [ ] Validar detecciones con segundo modelo

### M-02: Detección de Placas
- [ ] Entrenar YOLOv8 para placas mexicanas
- [ ] Recolectar dataset de placas
- [ ] Validar con OCR (sin guardar texto)

### M-03: Procesamiento Paralelo
- [ ] Implementar multiprocessing.Pool
- [ ] Procesar por lotes
- [ ] Optimizar uso de memoria

### M-04: Cifrado Opcional
- [ ] Cifrar dataset con AES-256
- [ ] Gestionar claves de manera segura
- [ ] Permitir acceso controlado

## Referencias

- [GDPR - Regulation (EU) 2016/679](https://gdpr.eu/)
- [CCPA - California Consumer Privacy Act](https://oag.ca.gov/privacy/ccpa)
- [OpenCV Face Detection](https://docs.opencv.org/4.x/db/d28/tutorial_cascade_classifier.html)
- [Piexif Documentation](https://piexif.readthedocs.io/)
- [MTCNN Paper](https://arxiv.org/abs/1604.02878)

## Uso en Entrenamiento

Una vez anonimizado el dataset:

```python
from ultralytics import YOLO

# Usar dataset anonimizado
model = YOLO('yolov8n.yaml')
model.train(
    data='ml/datasets/processed/anonymized/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16
)
```

**Ventaja**: Modelo entrenado con dataset ético y seguro para producción.
