# 🚀 Guía Rápida: Entrenar en Google Colab

## Opción 1: Usar Notebook Pre-configurado (RECOMENDADO)

### Paso 1: Subir Notebook a Colab

1. Abre [Google Colab](https://colab.research.google.com)
2. File > Upload notebook
3. Sube `ml/notebooks/SIRCCD_Training_Colab.ipynb`

### Paso 2: Configurar GPU

1. Runtime > Change runtime type
2. Hardware accelerator: **GPU**
3. GPU type: **T4** (gratis) o **A100** (Colab Pro)
4. Save

### Paso 3: Configurar Credenciales MinIO

En la celda de configuración de MinIO, reemplaza:

```python
os.environ['MINIO_ENDPOINT'] = 'TU_IP:9000'        # Ej: 192.168.1.100:9000
os.environ['MINIO_ACCESS_KEY'] = 'TU_ACCESS_KEY'   # Tu access key
os.environ['MINIO_SECRET_KEY'] = 'TU_SECRET_KEY'   # Tu secret key
```

💡 **Tip**: Si tu servidor MinIO está en tu red local, necesitarás:
- Usar un túnel (ngrok, localtunnel)
- O subir el dataset directamente a Google Drive

### Paso 4: Ejecutar

1. Runtime > Run all (Ctrl+F9)
2. Conecta Google Drive cuando te pida
3. Espera 6-8 horas (100 epochs)
4. Descarga modelo desde Google Drive

### Paso 5: Descargar Modelo

El modelo estará en:
```
Google Drive/SIRCCD_Models/baseline-yolov8n_YYYYMMDD_HHMMSS/
├── weights/
│   ├── best.pt       ← Mejor modelo
│   └── last.pt       ← Último epoch
├── results.csv       ← Métricas
├── *.png            ← Gráficos
└── training_summary.json
```

---

## Opción 2: Subir Dataset a Google Drive

Si MinIO no es accesible desde Colab:

### 1. Descargar Dataset Localmente

En tu PC:

```bash
cd C:\Users\wilki\sirccd-monorepo\sirccd-monorepo

# Activar entorno
.\.venv\Scripts\Activate.ps1

# Descargar dataset
python ml/scripts/download_from_minio.py --output ml/datasets/sirccd-download
```

### 2. Subir a Google Drive

1. Crea carpeta `SIRCCD_Dataset` en Google Drive
2. Sube las carpetas `images/` y `labels/`
3. La estructura debe ser:
   ```
   Google Drive/
   └── SIRCCD_Dataset/
       ├── images/
       │   ├── img_001.jpg
       │   ├── img_002.jpg
       │   └── ...
       ├── labels/
       │   ├── img_001.txt
       │   ├── img_002.txt
       │   └── ...
       └── data.yaml
   ```

### 3. Modificar Notebook de Colab

En lugar de descargar desde MinIO, usa:

```python
# Montar Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Dataset ya está en Drive
dataset_path = '/content/drive/MyDrive/SIRCCD_Dataset'

# Entrenar directamente
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
results = model.train(
    data=f'{dataset_path}/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device=0
)
```

---

## Opción 3: Usar Kaggle (30h/semana gratis)

### 1. Crear Dataset en Kaggle

1. Ve a [kaggle.com/datasets](https://www.kaggle.com/datasets)
2. New Dataset > Upload files
3. Sube `images/` y `labels/` (puede tardar)
4. Crea `data.yaml`:
   ```yaml
   path: /kaggle/input/sirccd-dataset
   train: images
   val: images
   names:
     0: residuo
     1: contenedor
     2: vehiculo
   nc: 3
   ```

### 2. Crear Notebook en Kaggle

1. Notebooks > New Notebook
2. Settings > Accelerator > **GPU T4 x2**
3. Add Data > Tu dataset SIRCCD

### 3. Código de Entrenamiento

```python
# Instalar Ultralytics
!pip install -q ultralytics

# Entrenar
from ultralytics import YOLO

model = YOLO('yolov8n.pt')
results = model.train(
    data='/kaggle/input/sirccd-dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device=0,
    project='/kaggle/working/runs',
    name='baseline'
)

# Archivos en /kaggle/working/ se pueden descargar desde la UI
```

### 4. Descargar Resultados

1. Click en "Output" en el panel derecho
2. Download `runs/` folder

---

## Opción 4: Lambda Labs (Pago - $4-5 por entrenamiento)

### 1. Crear Cuenta

1. [lambdalabs.com/cloud](https://lambdalabs.com/cloud)
2. Agregar forma de pago
3. Launch instance:
   - GPU: **RTX 6000 Ada** ($0.50/hora)
   - OS: Ubuntu 22.04 + PyTorch

### 2. SSH a Instancia

```bash
ssh ubuntu@<instance-ip>
```

### 3. Setup en Instancia

```bash
# Instalar Ultralytics
pip install ultralytics minio python-dotenv

# Descargar dataset (desde tu PC, copia el script)
python download_from_minio.py \
  --endpoint TU_IP:9000 \
  --access-key TU_KEY \
  --secret-key TU_SECRET \
  --output ~/datasets/sirccd

# Entrenar
yolo train \
  data=~/datasets/sirccd/data.yaml \
  model=yolov8n.pt \
  epochs=100 \
  batch=16 \
  device=0 \
  amp=True \
  cache=True
```

### 4. Descargar Modelo

Desde tu PC:

```bash
# Copiar modelo entrenado
scp -r ubuntu@<instance-ip>:~/runs/detect/train ./models/lambda-baseline

# O subirlo a MinIO desde la instancia
python upload_to_minio.py \
  --model runs/detect/train/weights/best.pt \
  --name lambda-baseline-v1
```

### 5. ⚠️ IMPORTANTE: Terminar Instancia

En Lambda Labs dashboard:
1. Instances > Tu instancia
2. **Terminate** (no solo stop)
3. Confirma que ya no estás siendo cobrado

---

## Comparación de Opciones

| Opción | Costo | Dificultad | Velocidad | Recomendado Para |
|--------|-------|-----------|-----------|------------------|
| **Colab Free** | $0 | ⭐ Fácil | ⭐⭐ Media | Prototipos, aprender |
| **Colab Pro** | $12/mes | ⭐ Fácil | ⭐⭐⭐⭐ Rápida (A100) | Experimentos frecuentes |
| **Kaggle** | $0 | ⭐⭐ Fácil | ⭐⭐⭐ Buena | Hasta 30h/semana |
| **Lambda Labs** | $4-5 | ⭐⭐⭐ Media | ⭐⭐⭐⭐⭐ Muy rápida | Producción |
| **RunPod Spot** | $3.50 | ⭐⭐⭐ Media | ⭐⭐⭐⭐ Rápida | Costo-beneficio |

---

## Troubleshooting

### "Cannot connect to MinIO"

Si Colab no puede conectar a tu MinIO local:

1. **Opción A**: Usa ngrok
   ```bash
   # En tu PC con MinIO
   ngrok tcp 9000
   # Copia la URL forwarding (ej: 0.tcp.ngrok.io:12345)
   # Úsala como MINIO_ENDPOINT en Colab
   ```

2. **Opción B**: Sube dataset a Google Drive (ver Opción 2)

### "Out of Memory" en GPU

Reduce batch size:
```python
batch=8  # En vez de 16
```

### Sesión de Colab se Desconecta

```python
# Al inicio del notebook
from google.colab import output
output.enable_keepalive()
```

### Dataset es muy grande

1. Usa solo un subset para pruebas rápidas
2. O entrena por más tiempo en GPU más potente (Lambda Labs)

---

## 🎯 Recomendación Final

**Para comenzar**: Usa **Google Colab Free** con dataset en Google Drive
- Valida que todo funciona
- Sin costo
- Aprende el proceso

**Para producción**: Usa **Lambda Labs**
- ~8 horas = $4
- GPU RTX 6000 Ada
- Resultados en menos tiempo

**Para experimentos**: Usa **Kaggle**
- 30 horas/semana gratis
- GPU P100 decente
- Repetir múltiples veces

---

**Siguiente**: Ver `CLOUD_TRAINING.md` para más opciones y detalles
