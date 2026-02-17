# 📋 Checklist: Iniciar Entrenamiento en Colab

## Estado Actual

✅ Dataset preparado localmente (57,976 imágenes en MinIO)  
✅ Certificación de privacidad completada (D-08)  
✅ Scripts de exportación creados  
✅ Notebook de Colab listo  
⏳ **SIGUIENTE**: Exportar dataset y subir a Drive

---

## Pasos para Iniciar

### 1️⃣ Iniciar Docker Desktop (2 min)

```powershell
# Abrir Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Esperar a que inicie (30-60 segundos)
Start-Sleep -Seconds 60

# Verificar que está corriendo
docker ps
```

**Si no tienes Docker Desktop instalado**:
1. Descarga: https://www.docker.com/products/docker-desktop
2. Instala y reinicia tu PC
3. Vuelve a este paso

---

### 2️⃣ Iniciar MinIO (1 min)

```powershell
cd C:\Users\wilki\sirccd-monorepo\sirccd-monorepo

# Iniciar contenedor MinIO
docker-compose -f docker-compose.minio.yml up -d

# Verificar que está corriendo
docker ps | Select-String "minio"
```

**Salida esperada**:
```
CONTAINER ID   IMAGE
xxx            minio/minio:latest    RUNNING
```

---

### 3️⃣ Exportar Dataset a ZIP (20-40 min)

```powershell
# Ejecutar script de exportación
.venv\Scripts\python.exe ml\datasets\scripts\export_for_colab.py
```

**Progreso esperado**:
```
✅ Conectado a MinIO (1 buckets)
📊 Escaneando bucket 'sirccd-datasets/v1.0.0'...
   Total de archivos: 115,952
📦 Creando ZIP para Google Colab...
Empaquetando: 100%|████████████| 115952/115952 [20:35<00:00, 93.71it/s]

✅ ZIP creado exitosamente
📊 Estadísticas:
   Archivo: ml\datasets\exports\sirccd_dataset_v1.0.0.zip
   Tamaño: 15.47 GB
   Total de archivos: 115,952
```

**Tiempo estimado**: 20-40 minutos (depende de disco SSD/HDD)

---

### 4️⃣ Subir a Google Drive (30-60 min)

1. **Abrir Google Drive**:
   ```
   https://drive.google.com
   ```

2. **Crear carpeta**:
   - Click "Nuevo" > "Nueva carpeta"
   - Nombre: `SIRCCD_Dataset`

3. **Subir ZIP**:
   - Entrar a carpeta `SIRCCD_Dataset`
   - Click "Nuevo" > "Subir archivo"
   - Seleccionar: `ml\datasets\exports\sirccd_dataset_v1.0.0.zip`
   - Esperar a que termine (~30-60 min)

**Nota**: Si tienes Google Drive Desktop instalado:
```powershell
# Copiar directamente a carpeta sincronizada
Copy-Item "ml\datasets\exports\sirccd_dataset_v1.0.0.zip" `
          "C:\Users\wilki\Google Drive\SIRCCD_Dataset\"
```

---

### 5️⃣ Abrir Google Colab (5 min)

1. **Ir a Colab**:
   ```
   https://colab.research.google.com
   ```

2. **Subir notebook**:
   - Click "Archivo" > "Subir notebook"
   - Seleccionar: `ml\notebooks\SIRCCD_Training_Colab.ipynb`

3. **Configurar GPU**:
   - Click "Entorno de ejecución" > "Cambiar tipo de entorno de ejecución"
   - Acelerador: **GPU**
   - Tipo de GPU: **T4**
   - Click "Guardar"

4. **Verificar GPU**:
   - Ejecutar primera celda: `!nvidia-smi`
   - Debe mostrar Tesla T4 con 15 GB VRAM

---

### 6️⃣ Ejecutar Entrenamiento (6-8 horas)

**Seguir notebook paso a paso**:

1. ✅ Verificar GPU
2. ✅ Instalar dependencias
3. ✅ Montar Google Drive
4. ✅ Descargar y extraer dataset (~15 min)
5. ✅ Crear data.yaml
6. 🚀 **Iniciar entrenamiento** (6-8 horas)
7. ✅ Evaluar modelo
8. ✅ Guardar resultados en Drive

**Mantener sesión activa**:
```python
from google.colab import output
output.enable_keepalive()
```

---

## Comandos Rápidos

### PowerShell (Local)

```powershell
# Iniciar todo desde cero
cd C:\Users\wilki\sirccd-monorepo\sirccd-monorepo

# 1. Docker + MinIO
docker-compose -f docker-compose.minio.yml up -d

# 2. Exportar dataset
.venv\Scripts\python.exe ml\datasets\scripts\export_for_colab.py

# 3. Abrir carpeta de exports
explorer ml\datasets\exports
```

### Verificaciones

```powershell
# ¿Docker corriendo?
docker ps

# ¿MinIO respondiendo?
curl http://localhost:9001

# ¿ZIP creado?
Test-Path ml\datasets\exports\sirccd_dataset_v1.0.0.zip

# Tamaño del ZIP
(Get-Item ml\datasets\exports\sirccd_dataset_v1.0.0.zip).Length / 1GB
```

---

## Troubleshooting Común

### ❌ Docker no inicia

**Síntoma**: `error during connect: Get "http://...dockerDesktopLinuxEngine...`

**Solución**:
1. Abrir Docker Desktop manualmente
2. Esperar a que el ícono de ballena se ponga verde
3. Reintentar comando

### ❌ "No space left on device"

**Síntoma**: Error al crear ZIP

**Solución**:
```powershell
# Verificar espacio disponible
Get-PSDrive C | Select-Object Used,Free

# Necesitas al menos 20 GB libres
# Liberar espacio:
# - Eliminar archivos temporales
# - Vaciar papelera de reciclaje
# - Desinstalar programas no usados
```

### ❌ MinIO no responde

**Síntoma**: `Error conectando a MinIO`

**Solución**:
```powershell
# Reiniciar contenedor
docker-compose -f docker-compose.minio.yml restart

# Verificar logs
docker-compose -f docker-compose.minio.yml logs
```

### ❌ Upload a Drive muy lento

**Síntoma**: Subida de ZIP tarda más de 2 horas

**Solución**:
1. Usa Google Drive Desktop (más rápido)
2. O divide el dataset:
   ```powershell
   # Solo entrenamiento (reduce 30% el tamaño)
   .venv\Scripts\python.exe ml\datasets\scripts\export_for_colab.py --only-train
   ```

---

## Timeline Estimado

| Paso | Acción | Tiempo |
|------|--------|---------|
| 1 | Iniciar Docker | 2 min |
| 2 | Iniciar MinIO | 1 min |
| 3 | Exportar dataset | 20-40 min |
| 4 | Subir a Drive | 30-60 min |
| 5 | Setup Colab | 5 min |
| 6 | Descargar dataset en Colab | 10-15 min |
| 7 | **Entrenamiento** | 6-8 horas |
| 8 | Guardar resultados | 5-10 min |
| **TOTAL** | **~8-10 horas** | |

---

## Recursos

- **Guía detallada**: `ml/docs/GUIA_INICIO_RAPIDO_COLAB.md`
- **Notebook**: `ml/notebooks/SIRCCD_Training_Colab.ipynb`
- **Script de exportación**: `ml/datasets/scripts/export_for_colab.py`

---

## Estado de Progreso

**Completado** ✅:
- [x] D-01 a D-07: Preparación de dataset
- [x] D-08: Certificación de privacidad
- [x] Scripts de exportación
- [x] Notebook de entrenamiento

**En Progreso** 🔄:
- [ ] Exportar dataset a ZIP
- [ ] Subir a Google Drive
- [ ] Entrenar modelo baseline

**Siguiente** ⏭️:
- [ ] M-01: Baseline model training
- [ ] M-02: Model evaluation
- [ ] M-03: Fine-tuning

---

**¿Listo para empezar?** 🚀

Ejecuta el primer comando:
```powershell
cd C:\Users\wilki\sirccd-monorepo\sirccd-monorepo
docker-compose -f docker-compose.minio.yml up -d
```
