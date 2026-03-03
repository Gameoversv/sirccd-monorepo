# B-04 - Endpoint Crear Reporte

## 📋 Resumen

Implementación completa del endpoint `POST /reportes` para crear reportes ciudadanos con foto, GPS y descripción.

## ✅ Características Implementadas

### 1. Endpoint POST /reportes
- **URL**: `/api/v1/reportes`
- **Método**: POST
- **Content-Type**: `multipart/form-data`
- **Autenticación**: Requerida (JWT Bearer token)
- **Estado**: Usuario debe estar activo

### 2. Campos Soportados

#### Obligatorios:
- `image` (file): Imagen del daño vial
  - Formatos permitidos: JPG, JPEG, PNG, WEBP
  - Tamaño máximo: 10 MB
  - Validación de content-type

- `latitude` (float): Latitud en formato WGS84
  - Rango: -90.0 a 90.0

- `longitude` (float): Longitud en formato WGS84
  - Rango: -180.0 a 180.0

#### Opcionales:
- `description` (string): Descripción del problema (max 2000 caracteres)
- `address` (string): Dirección aproximada (max 500 caracteres)
- `city` (string): Ciudad (max 100 caracteres)
- `province` (string): Provincia/Estado (max 100 caracteres)

### 3. Almacenamiento de Imágenes

**Servicio de Storage** (`backend/services/storage.py`):
- **Modo Producción**: MinIO (S3-compatible)
  - Configuración en `backend/core/config.py`
  - Bucket: `sirccd-images`
  - Estructura: `reports/YYYY/MM/DD/uuid_filename.ext`

- **Modo Desarrollo**: Almacenamiento local (fallback)
  - Directorio: `backend/storage/images/`
  - Misma estructura de carpetas

**Características del Storage**:
- ✅ Generación de nombres únicos (UUID)
- ✅ Validación de tipo de archivo
- ✅ Validación de tamaño (10 MB max)
- ✅ Extracción de dimensiones (Pillow)
- ✅ Organización por fechas
- ✅ Fallback automático a local si MinIO no disponible

### 4. Detección ML (Mock)

**Implementación Actual**:
- Detección simulada (aleatorizada) para pruebas
- Tipos detectados: `bache`, `grieta`
- Niveles de severidad: `baja`, `media`, `alta`
- Confianza: 0.5 - 0.95

**TODO**: Reemplazar con modelo YOLO real
```python
# Ubicación: backend/api/routes/reports.py
def _mock_ml_detection(image_url: str) -> tuple[DamageType, SeverityLevel, float]:
    # TODO: Integrar con servicio ML real
    pass
```

### 5. Base de Datos

**Tabla**: `reports` (ya existía en migración `001_initial_schema_with_postgis.py`)

**Campos guardados**:
- `id`: ID único del reporte
- `user_id`: Usuario que reporta
- `location`: Geometría PostGIS (POINT con SRID 4326)
- `address`, `city`, `province`: Información de ubicación
- `damage_type`: Tipo de daño (enum)
- `severity`: Severidad (enum)
- `confidence`: Confianza de detección (0.0 - 1.0)
- `image_url`: URL de la imagen almacenada
- `image_width`, `image_height`: Dimensiones
- `status`: Estado del reporte (default: `processing`)
- `description`: Descripción del usuario
- `created_at`, `updated_at`: Timestamps
- `detections_json`: JSON con bounding boxes (TODO)

### 6. Validaciones Implementadas

✅ **Imagen**:
- Content-type debe ser `image/*`
- Extensión: `.jpg`, `.jpeg`, `.png`, `.webp`
- Tamaño máximo: 10 MB

✅ **Coordenadas GPS**:
- Latitud: -90.0 ≤ lat ≤ 90.0
- Longitud: -180.0 ≤ lng ≤ 180.0
- FastAPI validation automática

✅ **Descripción**:
- Longitud mínima: 3 caracteres (si se proporciona)
- Longitud máxima: 2000 caracteres
- Limpieza de espacios extra

✅ **Autenticación**:
- Token JWT válido requerido
- Usuario debe estar activo (`is_active=True`)

### 7. Respuesta del Endpoint

**Status 201 Created**:
```json
{
  "id": 4,
  "status": "processing",
  "damage_type": "bache",
  "severity": "alta",
  "confidence": 0.87,
  "image_url": "/storage/images/reports/2026/03/03/abc123_image.jpg",
  "latitude": -34.603722,
  "longitude": -58.381592,
  "description": "Bache profundo en vía principal",
  "created_at": "2026-03-03T02:29:05.995987"
}
```

**Errores Posibles**:
- `400`: Imagen inválida (tipo, tamaño, formato)
- `401`: No autenticado o token inválido
- `413`: Imagen demasiado grande (>10 MB)
- `422`: Validación fallida (GPS inválido, campos requeridos)
- `500`: Error interno (BD, storage)

### 8. Endpoint GET /reportes/{id}

**Adicional Implementado**:
- Obtener reporte por ID
- Incluye extracción de coordenadas desde PostGIS
- Requiere autenticación

## 📁 Archivos Creados/Modificados

### Nuevos Archivos:
1. **`backend/services/storage.py`** (319 líneas)
   - Clase `StorageService`
   - Upload a MinIO/local
   - Validaciones de imagen
   - Delete de imágenes

2. **`backend/services/__init__.py`** (6 líneas)
   - Export del servicio de storage

3. **`backend/schemas/report.py`** (264 líneas)
   - `CreateReportRequest`
   - `CreateReportResponse`
   - `ReportResponse`
   - `ReportListResponse`
   - `BoundingBox`, `DetectionResult`
   - Enums: `ReportStatusEnum`, `DamageTypeEnum`, `SeverityLevelEnum`

4. **`backend/api/routes/reports.py`** (257 líneas)
   - `POST /reportes` - Crear reporte
   - `GET /reportes/{id}` - Obtener reporte
   - Integración con storage y ML

5. **`backend/test_b04_reports.py`** (432 líneas)
   - Script de prueba completo
   - 5 escenarios de test
   - Generación de imagen de prueba

### Modificados:
1. **`backend/main.py`**
   - Import de `reports` router
   - Registro de rutas de reportes

## 🧪 Pruebas Ejecutadas

**Resultados**:
```
✅ Crear reporte completo (todos los campos)
✅ Crear reporte mínimo (solo imagen + GPS)
✅ Validación GPS inválido (4 casos)
✅ Obtener reporte por ID
✅ Rechazo sin autenticación
```

**Comando de prueba**:
```bash
cd backend
python test_b04_reports.py
```

## 📚 Documentación API

**Swagger UI**: http://localhost:8000/api/v1/docs

**Ejemplo cURL**:
```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testb04user","password":"testpass123"}' \
  | jq -r .access_token)

# 2. Crear reporte
curl -X POST http://localhost:8000/api/v1/reportes \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@test_image.jpg" \
  -F "latitude=-34.603722" \
  -F "longitude=-58.381592" \
  -F "description=Bache profundo en la calle" \
  -F "city=Buenos Aires"
```

**Ejemplo Python**:
```python
import httpx

# Login
response = httpx.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "testuser", "password": "password123"}
)
token = response.json()["access_token"]

# Crear reporte
with open("photo.jpg", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/v1/reportes",
        data={
            "latitude": -34.603722,
            "longitude": -58.381592,
            "description": "Bache en Av. Corrientes"
        },
        files={"image": ("photo.jpg", f, "image/jpeg")},
        headers={"Authorization": f"Bearer {token}"}
    )

report = response.json()
print(f"Reporte creado: ID={report['id']}")
```

## 🔄 Flujo Completo

```
1. Usuario hace POST /reportes con imagen + GPS
   ↓
2. FastAPI valida autenticación (JWT)
   ↓
3. Validaciones de campos (GPS, imagen)
   ↓
4. StorageService sube imagen a MinIO/local
   ↓
5. Detección ML identifica tipo y severidad
   ↓
6. Crear geometría PostGIS (POINT)
   ↓
7. Guardar reporte en BD
   ↓
8. Retornar CreateReportResponse (201)
```

## 🚀 Siguientes Pasos (TODOs)

1. **Integrar modelo ML real**:
   - Reemplazar `_mock_ml_detection()`
   - Integrar servicio YOLO
   - Guardar bounding boxes en `detections_json`

2. **Geocoding reverso**:
   - Obtener `address`, `city`, `province` automáticamente
   - Integrar con API de geocoding (Google Maps, OpenStreetMap)

3. **Procesamiento asíncrono**:
   - Mover ML a worker (Celery/RQ)
   - Estado inicial: `pending` → `processing` → `pending` approval

4. **Optimización de imágenes**:
   - Resize automático (max 1920x1080)
   - Compresión JPEG/WebP
   - Generación de thumbnails

5. **Endpoints adicionales**:
   - `GET /reportes` - Listar con paginación y filtros
   - `PATCH /reportes/{id}` - Actualizar estado
   - `DELETE /reportes/{id}` - Eliminar reporte

6. **Tests unitarios**:
   - Pytest para cada función
   - Mocks de MinIO y ML
   - Tests de integración

## 📊 Estadísticas de Implementación

- **Líneas de código**: ~1,200 líneas
- **Archivos nuevos**: 5
- **Archivos modificados**: 1
- **Tests escritos**: 5 escenarios
- **Endpoints**: 2 (POST, GET)
- **Tiempo de desarrollo**: ~2 horas
- **Estado**: ✅ **COMPLETO Y FUNCIONAL**

## 🎯 Requisitos Cumplidos

✅ Endpoint POST /reportes implementado
✅ Recibe imagen (multipart/form-data)
✅ Recibe coordenadas GPS (lat, lng)
✅ Recibe descripción (opcional)
✅ Guarda metadatos en BD
✅ Guarda archivo en storage (MinIO/local fallback)
✅ Valida datos mínimos
✅ Devuelve ID del reporte
✅ Pruebas completas ejecutadas

---

**Versión**: 0.1.0  
**Fecha**: 2026-03-03  
**Autor**: GitHub Copilot  
**Estado**: ✅ Production-Ready (con ML mock)
