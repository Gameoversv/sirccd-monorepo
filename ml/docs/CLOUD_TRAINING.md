# 🌩️ Entrenamiento en la Nube - Guía Completa

Guía para entrenar modelos YOLOv8 en servicios en la nube con acceso a GPU.

## 📋 Tabla de Contenidos

- [Opciones Gratuitas](#opciones-gratuitas)
- [Opciones de Pago](#opciones-de-pago)
- [Configuración por Plataforma](#configuración-por-plataforma)
- [Comparación de Servicios](#comparación-de-servicios)
- [Mejores Prácticas](#mejores-prácticas)

---

## 🆓 Opciones Gratuitas

### 1. Google Colab (RECOMENDADO para comenzar)

**🎯 Mejor para**: Experimentación rápida, prototipos, datasets pequeños-medianos

**Características**:
- ✅ GPU Tesla T4 gratis (15 GB VRAM)
- ✅ 12 GB RAM
- ✅ Hasta 12 horas de sesión continua
- ✅ Jupyter notebooks nativamente
- ✅ No requiere configuración
- ⚠️ Límites de tiempo y uso

**GPU Disponibles Gratis**:
- Tesla T4 (más común)
- Tesla K80 (ocasional)

**Costo**:
- **Free**: Acceso limitado a T4
- **Colab Pro**: $12/mes - T4 garantizada, sesiones más largas
- **Colab Pro+**: $50/mes - A100 (40 GB), prioridad máxima

**Setup rápido**:

```python
# 1. Crear notebook en: https://colab.research.google.com

# 2. Verificar GPU
!nvidia-smi

# 3. Instalar dependencias
!pip install ultralytics minio python-dotenv

# 4. Descargar dataset desde MinIO
from minio import Minio
import os
from dotenv import load_dotenv

# Configurar credenciales MinIO
os.environ['MINIO_ENDPOINT'] = 'tu-servidor:9000'
os.environ['MINIO_ACCESS_KEY'] = 'tu-access-key'
os.environ['MINIO_SECRET_KEY'] = 'tu-secret-key'

# Descargar dataset
minio_client = Minio(
    os.environ['MINIO_ENDPOINT'],
    access_key=os.environ['MINIO_ACCESS_KEY'],
    secret_key=os.environ['MINIO_SECRET_KEY'],
    secure=False
)

# Descargar imágenes y anotaciones
!mkdir -p /content/datasets/sirccd
# ... código para descargar desde MinIO

# 5. Entrenar YOLOv8
from ultralytics import YOLO

model = YOLO('yolov8n.pt')  # nano model
results = model.train(
    data='/content/datasets/sirccd/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device=0,  # GPU
    project='/content/runs/detect',
    name='baseline_colab'
)

# 6. Subir modelo entrenado a MinIO o Google Drive
```

**Ventajas**:
- ✅ Configuración instantánea (0 minutos)
- ✅ Integración con Google Drive
- ✅ Ideal para aprendizaje y desarrollo
- ✅ Compartir notebooks fácilmente

**Desventajas**:
- ⚠️ Sesiones se desconectan después de inactividad
- ⚠️ Límites de uso diario/semanal
- ⚠️ Datos se borran al cerrar sesión (usar Drive/MinIO)
- ⚠️ No persistente

**Trucos**:
```python
# Mantener sesión activa
from google.colab import output
output.enable_keepalive()

# Montar Google Drive para persistencia
from google.colab import drive
drive.mount('/content/drive')

# Guardar checkpoints regularmente
# En YOLO, usar save_period=10 para guardar cada 10 epochs
```

---

### 2. Kaggle Notebooks

**🎯 Mejor para**: Datasets públicos, competiciones, hasta 30 horas por semana

**Características**:
- ✅ GPU Tesla P100 (16 GB VRAM) o T4 gratis
- ✅ 13 GB RAM
- ✅ 30 horas/semana de GPU
- ✅ Datasets públicos integrados
- ✅ Más estable que Colab free

**GPU Disponibles Gratis**:
- Tesla P100 (16 GB) - más potente que T4
- Tesla T4 (15 GB)

**Costo**:
- **100% Gratis** - No hay plan de pago

**Setup**:
```python
# 1. Crear notebook en https://www.kaggle.com/code

# 2. Habilitar GPU en Settings > Accelerator > GPU T4 x2

# 3. Subir dataset
# - Crear dataset en Kaggle
# - Subir imágenes y anotaciones YOLO
# - Agregar dataset al notebook en "Add Data"

# 4. Entrenar
from ultralytics import YOLO
import os

model = YOLO('yolov8n.pt')
results = model.train(
    data='/kaggle/input/sirccd-dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device=0,
    project='/kaggle/working/runs',
    name='baseline_kaggle'
)

# 5. Descargar resultados
# Los archivos en /kaggle/working/ se pueden descargar desde la UI
```

**Ventajas**:
- ✅ P100 > T4 en rendimiento
- ✅ 30 horas/semana confiables
- ✅ Datasets públicos enormes
- ✅ Comunidad activa
- ✅ Más estable que Colab

**Desventajas**:
- ⚠️ Límite semanal de 30 horas GPU
- ⚠️ Menos flexible que Colab
- ⚠️ Datasets deben ser públicos o privados en Kaggle

---

### 3. Paperspace Gradient Free Tier

**⚠️ DESCONTINUADO**: Paperspace eliminó su tier gratuito en 2024.

Alternativa: Usar su plan de pago (ver sección de pago).

---

## 💰 Opciones de Pago

### 1. Google Cloud Platform (GCP)

**🎯 Mejor para**: Producción, escalabilidad, integración empresarial

**GPUs Disponibles**:
- NVIDIA T4: ~$0.35/hora
- NVIDIA V100: ~$2.48/hora
- NVIDIA A100 (40GB): ~$3.67/hora
- NVIDIA A100 (80GB): ~$4.44/hora
- NVIDIA H100: ~$6-8/hora (más reciente)

**Vertex AI Training**:
```bash
# 1. Instalar gcloud CLI
# https://cloud.google.com/sdk/docs/install

# 2. Crear bucket de Cloud Storage
gsutil mb gs://sirccd-ml-training

# 3. Subir dataset
gsutil -m cp -r datasets/ gs://sirccd-ml-training/

# 4. Crear job de entrenamiento
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=yolov8-baseline \
  --worker-pool-spec=machine-type=n1-standard-8,replica-count=1,accelerator-type=NVIDIA_TESLA_T4,accelerator-count=1,container-image-uri=ultralytics/ultralytics:latest \
  --args="yolo,train,data=/gcs/sirccd-ml-training/data.yaml,epochs=100,imgsz=640"
```

**Costos Estimados** (YOLOv8n, 100 epochs, 57K imágenes):
- Con T4: ~8-10 horas = $2.80 - $3.50
- Con V100: ~4-5 horas = $9.92 - $12.40
- Con A100: ~2-3 horas = $7.34 - $11.01

**Ventajas**:
- ✅ Escalabilidad infinita
- ✅ Integración con otros servicios Google
- ✅ Vertex AI para MLOps completo
- ✅ Preemptible VMs (70% descuento)
- ✅ $300 créditos gratis para nuevos usuarios

**Desventajas**:
- ⚠️ Curva de aprendizaje
- ⚠️ Costos pueden escalar rápido
- ⚠️ Configuración compleja

---

### 2. AWS (Amazon Web Services)

**🎯 Mejor para**: Empresas ya en AWS, entrenamiento distribuido

**GPUs Disponibles** (EC2):
- g4dn.xlarge (T4): ~$0.526/hora
- p3.2xlarge (V100): ~$3.06/hora
- p4d.24xlarge (A100): ~$32.77/hora
- p5.48xlarge (H100): ~$98/hora

**SageMaker Training**:
```python
# 1. Instalar AWS SDK
# pip install sagemaker boto3

# 2. Configurar SageMaker
import sagemaker
from sagemaker.pytorch import PyTorch

role = 'arn:aws:iam::YOUR_ACCOUNT:role/SageMakerRole'
sess = sagemaker.Session()

# 3. Crear training job
estimator = PyTorch(
    entry_point='train.py',  # Script de entrenamiento YOLOv8
    role=role,
    instance_count=1,
    instance_type='ml.g4dn.xlarge',  # T4 GPU
    framework_version='2.0',
    py_version='py310',
    hyperparameters={
        'epochs': 100,
        'batch-size': 16,
        'img-size': 640
    }
)

estimator.fit({'training': 's3://sirccd-datasets/yolo/'})
```

**Costos Estimados** (YOLOv8n, 100 epochs):
- Con g4dn.xlarge (T4): ~$4.21 - $5.26
- Con p3.2xlarge (V100): ~$12.24 - $15.30

**Ventajas**:
- ✅ SageMaker simplifica MLOps
- ✅ Spot instances (hasta 90% descuento)
- ✅ Integración S3, Lambda, etc.
- ✅ Infraestructura robusta

**Desventajas**:
- ⚠️ Costos complejos de calcular
- ⚠️ SageMaker añade overhead
- ⚠️ Configuración IAM complicada

---

### 3. Azure Machine Learning

**🎯 Mejor para**: Empresas Microsoft, integración Azure

**GPUs Disponibles**:
- NC6s v3 (V100): ~$3.06/hora
- NC A100 v4: ~$3.67/hora
- ND96asr A100 v4: ~$32.77/hora

**Azure ML Training**:
```python
# pip install azureml-sdk

from azureml.core import Workspace, Experiment, ScriptRunConfig
from azureml.core.compute import AmlCompute, ComputeTarget

# 1. Conectar workspace
ws = Workspace.from_config()

# 2. Crear compute cluster
compute_config = AmlCompute.provisioning_configuration(
    vm_size='Standard_NC6s_v3',  # V100
    max_nodes=1
)
compute_target = ComputeTarget.create(ws, 'gpu-cluster', compute_config)

# 3. Configurar training
config = ScriptRunConfig(
    source_directory='./scripts',
    script='train_yolo.py',
    compute_target=compute_target,
    arguments=['--epochs', 100, '--batch', 16]
)

# 4. Ejecutar
experiment = Experiment(ws, 'yolov8-baseline')
run = experiment.submit(config)
```

**Ventajas**:
- ✅ Integración Office 365, Active Directory
- ✅ Azure ML Studio (UI visual)
- ✅ Responsible AI tools

**Desventajas**:
- ⚠️ Menos popular que AWS/GCP para ML
- ⚠️ Documentación menos extensa

---

### 4. Lambda Labs

**🎯 Mejor para**: Máximo poder GPU por menor precio

**GPUs Disponibles**:
- RTX 6000 Ada: ~$0.50/hora ⭐ MEJOR RELACIÓN CALIDAD-PRECIO
- A100 (40GB): ~$1.10/hora
- A100 (80GB): ~$1.29/hora
- H100: ~$1.99/hora

**Setup**:
```bash
# 1. Crear cuenta en https://lambdalabs.com

# 2. Lanzar instancia GPU
# - Seleccionar RTX 6000 Ada o A100
# - Ubuntu 22.04 + PyTorch pre-instalado

# 3. SSH a instancia
ssh ubuntu@<instance-ip>

# 4. Instalar dependencias
pip install ultralytics minio python-dotenv

# 5. Descargar dataset desde MinIO
# (usar script similar a Colab)

# 6. Entrenar
yolo train data=data.yaml model=yolov8n.pt epochs=100 batch=16 device=0

# 7. Terminar instancia cuando termine
# ⚠️ IMPORTANTE: Apagar instancia para no seguir pagando
```

**Costos Estimados** (YOLOv8n, 100 epochs):
- Con RTX 6000 Ada: ~$4.00 - $5.00 ⭐
- Con A100 (40GB): ~$8.80 - $11.00

**Ventajas**:
- ✅ **Precios más bajos** del mercado
- ✅ GPUs más recientes (RTX 6000 Ada, H100)
- ✅ Setup simple (PyTorch pre-instalado)
- ✅ Sin costos ocultos
- ✅ Soporte excelente

**Desventajas**:
- ⚠️ Disponibilidad limitada (GPUs se agotan)
- ⚠️ Menos servicios adicionales que AWS/GCP
- ⚠️ No hay autoescalado

---

### 5. RunPod

**🎯 Mejor para**: Flexibilidad, precios competitivos, spot instances

**GPUs Disponibles**:
- RTX 4090: ~$0.44/hora (Spot) / $0.79/hora (On-Demand)
- A40: ~$0.49/hora (Spot) / $0.79/hora (On-Demand)
- A100 (80GB): ~$1.69/hora (Spot) / $2.89/hora (On-Demand)

**Spot vs On-Demand**:
- **Spot**: 40-70% más barato, puede interrumpirse
- **On-Demand**: Garantizado, más caro

**Setup con RunPod**:
```bash
# 1. Crear cuenta en https://runpod.io

# 2. Crear pod
# - Template: PyTorch 2.0
# - GPU: RTX 4090 o A40 (Spot)
# - Storage: 50 GB

# 3. Conectar por SSH o Web Terminal

# 4. Clonar código y entrenar
git clone <tu-repo>
cd ml/
pip install -r requirements-training.txt

python scripts/train_baseline.py

# 5. Guardar resultados en volume persistente
# /workspace/ persiste entre sesiones
cp -r runs/ /workspace/models/
```

**Costos Estimados** (YOLOv8n, 100 epochs):
- Con RTX 4090 (Spot): ~$3.52 - $4.40 ⭐ ECONÓMICO
- Con A100 80GB (Spot): ~$13.52 - $16.90

**Ventajas**:
- ✅ Spot instances mucho más baratas
- ✅ Storage persistente
- ✅ Jupyter Lab incluido
- ✅ Fácil de usar

**Desventajas**:
- ⚠️ Spot puede interrumpirse
- ⚠️ Configuración red más compleja

---

### 6. Vast.ai

**🎯 Mejor para**: Precios ultra-bajos, GPUs diverse

**GPUs Disponibles** (marketplace de GPU):
- RTX 3090: ~$0.20-0.35/hora
- RTX 4090: ~$0.35-0.50/hora
- A100: ~$0.80-1.20/hora

**Modelo**: Marketplace de GPUs (alquiler P2P)

**Ventajas**:
- ✅ **Precios más bajos posibles**
- ✅ Variedad enorme de GPUs
- ✅ Sin compromiso

**Desventajas**:
- ⚠️ Calidad variable (latencia, uptime)
- ⚠️ Menos confiable
- ⚠️ Setup más manual

---

## 📊 Comparación de Servicios

### Por Precio (YOLOv8n, 100 epochs, ~8 horas)

| Servicio | GPU | Costo Estimado | Disponibilidad |
|----------|-----|----------------|----------------|
| **Google Colab Free** | T4 | $0 | Limitado |
| **Kaggle** | P100 | $0 | 30h/semana |
| **Vast.ai** | RTX 3090 | $1.60 - $2.80 | Variable |
| **RunPod Spot** | RTX 4090 | $3.52 - $4.40 | Alta |
| **Lambda Labs** | RTX 6000 Ada | $4.00 - $5.00 | Media |
| **GCP Preemptible** | T4 | $0.84 - $1.05 | Alta |
| **AWS Spot** | T4 | $1.58 - $2.00 | Alta |
| **RunPod On-Demand** | A40 | $6.32 - $7.90 | Garantizada |
| **GCP** | T4 | $2.80 - $3.50 | Garantizada |
| **Lambda Labs** | A100 40GB | $8.80 - $11.00 | Media |

### Por Facilidad de Uso

1. ⭐⭐⭐⭐⭐ **Google Colab** - Un click y listo
2. ⭐⭐⭐⭐⭐ **Kaggle** - Similar a Colab
3. ⭐⭐⭐⭐ **Lambda Labs** - Simple setup
4. ⭐⭐⭐⭐ **RunPod** - Pod en 2 minutos
5. ⭐⭐⭐ **AWS SageMaker** - Requiere configuración
6. ⭐⭐⭐ **GCP Vertex AI** - Requiere configuración
7. ⭐⭐ **Vast.ai** - Setup manual

### Por Confiabilidad

1. ⭐⭐⭐⭐⭐ **AWS On-Demand** - SLA 99.99%
2. ⭐⭐⭐⭐⭐ **GCP On-Demand** - SLA 99.99%
3. ⭐⭐⭐⭐⭐ **Azure On-Demand** - SLA 99.99%
4. ⭐⭐⭐⭐ **Lambda Labs** - Alta disponibilidad
5. ⭐⭐⭐⭐ **RunPod On-Demand** - Muy confiable
6. ⭐⭐⭐ **Google Colab Free** - Desconexiones
7. ⭐⭐⭐ **RunPod Spot** - Puede interrumpirse
8. ⭐⭐ **Vast.ai** - Variable

---

## 🎯 Recomendaciones por Caso de Uso

### Estudiante / Aprendizaje
**Recomendado**: Google Colab Free o Kaggle
- Costo: $0
- Bueno para datasets pequeños y medianos
- Experimenta sin riesgo financiero

### Proyecto Personal / Startup
**Recomendado**: RunPod Spot o Lambda Labs
- Costo: $3-5 por entrenamiento
- Buen balance precio/rendimiento
- Fácil de usar

### Empresa Pequeña
**Recomendado**: Lambda Labs o RunPod On-Demand
- Costo: $5-10 por entrenamiento
- Confiable y predecible
- Sin infraestructura compleja

### Empresa Mediana/Grande
**Recomendado**: GCP Vertex AI o AWS SageMaker
- Costo: $10-20 por entrenamiento (pero escalable)
- Integración con infraestructura existente
- MLOps completo

### Investigación (múltiples experimentos)
**Recomendado**: Kaggle + Lambda Labs
- Kaggle para prototipos (gratis 30h/semana)
- Lambda Labs para entrenamientos largos
- Combina gratis + económico

---

## 🛠️ Mejores Prácticas

### 1. Optimizar Costos

```python
# ✅ Usar mixed precision training (2x más rápido)
model.train(
    data='data.yaml',
    epochs=100,
    amp=True,  # Automatic Mixed Precision
    device=0
)

# ✅ Usar batch size óptimo (usa toda la VRAM)
# T4 (15 GB): batch=16 para YOLOv8n
# A100 (40 GB): batch=32-64

# ✅ Usar model caching
model.train(
    data='data.yaml',
    cache=True,  # Cache imágenes en RAM
    epochs=100
)

# ✅ Early stopping
model.train(
    data='data.yaml',
    epochs=300,
    patience=50,  # Para si no mejora en 50 epochs
)
```

### 2. Monitorear Costos

```bash
# GCP: Ver costos en tiempo real
gcloud billing accounts list
gcloud billing accounts get-iam-policy ACCOUNT_ID

# AWS: CloudWatch + Cost Explorer

# Lambda/RunPod: Dashboard muestra costo acumulado
```

### 3. Usar Checkpoints

```python
# Guardar checkpoints cada N epochs
model.train(
    data='data.yaml',
    epochs=100,
    save_period=10,  # Guarda cada 10 epochs
    project='runs/detect',
    name='baseline'
)

# Resumir desde checkpoint
model = YOLO('runs/detect/baseline/weights/last.pt')
model.train(resume=True)
```

### 4. Subir/Descargar Datasets Eficientemente

```python
# Usar MinIO desde cualquier cloud
from minio import Minio
import os

def download_dataset_from_minio(local_path='./datasets'):
    """Descarga dataset desde MinIO a cloud GPU"""
    client = Minio(
        os.getenv('MINIO_ENDPOINT'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )
    
    # Descargar solo imágenes necesarias
    objects = client.list_objects('sirccd-datasets', 
                                   prefix='v1.0.0/images/',
                                   recursive=True)
    
    for obj in tqdm(objects):
        client.fget_object('sirccd-datasets', 
                          obj.object_name, 
                          f"{local_path}/{obj.object_name}")

# En Colab/Kaggle/etc
download_dataset_from_minio('/content/datasets')
```

### 5. Automatizar con Scripts

```bash
# Script para entrenar en cualquier cloud
# train_cloud.sh

#!/bin/bash
set -e

# 1. Descargar dataset
python scripts/download_from_minio.py

# 2. Verificar GPU
nvidia-smi

# 3. Entrenar
python -c "
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
model.train(
    data='datasets/sirccd/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    amp=True,
    cache=True,
    device=0
)
"

# 4. Subir resultados a MinIO
python scripts/upload_to_minio.py runs/detect/train/

# 5. Notificar por email/Slack
curl -X POST <webhook-url> -d "Entrenamiento completado!"
```

### 6. Evitar Costos Inesperados

⚠️ **CHECKLIST ANTES DE ENTRENAR**:

- [ ] Verifica que instancia se apague automáticamente
- [ ] Configura presupuesto máximo (budget alerts)
- [ ] Usa spot/preemptible cuando sea posible
- [ ] Monitorea GPU usage (no dejar idle)
- [ ] Configura timeout máximo
- [ ] Borra recursos después de usar

```python
# Ejemplo: Auto-shutdown en Colab si toma > 12 horas
import signal
import sys

def timeout_handler(signum, frame):
    print("⏰ Timeout alcanzado. Guardando y saliendo...")
    # Guardar modelo
    model.save('backup.pt')
    sys.exit(0)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(12 * 3600)  # 12 horas
```

---

## 📝 Checklist Rápido

### Para Google Colab:
1. Ir a https://colab.research.google.com
2. Nuevo notebook
3. Runtime > Change runtime type > GPU > T4
4. Copiar código de setup arriba
5. Entrenar

### Para Lambda Labs:
1. Crear cuenta en https://lambdalabs.com
2. Agregar forma de pago
3. Launch instance > RTX 6000 Ada
4. SSH y entrenar
5. **IMPORTANTE**: Terminate instance

### Para AWS/GCP/Azure:
1. Crear cuenta (obtener $300 créditos gratis)
2. Configurar IAM/roles
3. Seguir guías de setup arriba
4. Configurar billing alerts
5. Entrenar y monitorear costos

---

## 🔗 Referencias

- [Google Colab](https://colab.research.google.com)
- [Kaggle](https://www.kaggle.com)
- [Lambda Labs](https://lambdalabs.com)
- [RunPod](https://runpod.io)
- [Vast.ai](https://vast.ai)
- [AWS SageMaker](https://aws.amazon.com/sagemaker/)
- [GCP Vertex AI](https://cloud.google.com/vertex-ai)
- [Azure ML](https://azure.microsoft.com/en-us/services/machine-learning/)

- [Ultralytics YOLOv8 Docs](https://docs.ultralytics.com)
- [PyTorch Cloud Training](https://pytorch.org/tutorials/beginner/aws_distributed_training_tutorial.html)

---

**Última actualización**: 17 de febrero de 2026  
**Para**: Proyecto SIRCCD ML Training
