# Servicio de Deduplicación B-07 - Guía Rápida

## Resumen

El servicio de deduplicación combina **similitud visual** (embeddings + FAISS) y **proximidad geográfica** (Haversine) para detectar reportes duplicados automáticamente.

## Instalación

### 1. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

**Nuevas dependencias**:
- `faiss-cpu==1.8.0` - Búsqueda de similitud
- `scikit-learn==1.5.2` - Utilidades ML

### 2. Configurar variables de entorno

Añadir a `.env`:

```bash
# Deduplication Service (B-07)
FAISS_INDEX_PATH=storage/faiss_index.bin
DEDUPLICATION_VISUAL_MODEL=resnet50
VISUAL_SIMILARITY_THRESHOLD=0.15
GEO_DISTANCE_THRESHOLD=50.0
DEDUP_TIME_WINDOW_DAYS=30
```

### 3. Iniciar servidor

```bash
python start.py
```

## Uso de la API

### 1. Verificar si un reporte es duplicado

```python
import requests

# Endpoint
url = "http://localhost:8000/api/v1/deduplication/check"

# Headers
headers = {
    "Authorization": "Bearer YOUR_TOKEN"
}

# Datos del formulario
files = {
    "image": open("pothole.jpg", "rb")
}

data = {
    "latitude": 19.4515,
    "longitude": -70.6974,
    "damage_type": "bache"
}

# Hacer petición
response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()

print(f"¿Es duplicado? {result['is_duplicate']}")
if result['is_duplicate']:
    print(f"Reporte original: {result['original_report_id']}")
    print(f"Distancia visual: {result['metadata']['visual_distance']:.4f}")
    print(f"Distancia geográfica: {result['metadata']['geo_distance']:.1f}m")
```

### 2. Buscar reportes similares

```python
url = "http://localhost:8000/api/v1/deduplication/similar"

data = {
    "latitude": 19.4515,
    "longitude": -70.6974,
    "damage_type": "bache",
    "top_k": 10
}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()

print(f"Encontrados {result['count']} reportes similares:")
for report in result['results']:
    print(f"  ID {report['report_id']}: "
          f"visual={report['visual_distance']:.4f}, "
          f"geo={report['geo_distance']:.1f}m")
```

### 3. Obtener estadísticas

```python
url = "http://localhost:8000/api/v1/deduplication/stats"

response = requests.get(url, headers=headers)
stats = response.json()

print(f"Reportes indexados: {stats['index_size']}")
print(f"Umbral visual: {stats['visual_threshold']}")
print(f"Umbral geográfico: {stats['geo_threshold']}m")
```

### 4. Reconstruir índice (admin)

```python
url = "http://localhost:8000/api/v1/deduplication/index/rebuild"

data = {
    "batch_size": 100
}

response = requests.post(url, headers=headers, data=data)
result = response.json()

print(f"Éxito: {result['success']}")
print(f"Reportes indexados: {result['statistics']['index_size']}")
```

## Testing

### Ejecutar tests

```bash
cd backend
python test_b07_deduplication.py
```

**Tests incluidos**:
1. ✅ Visual Embedder (ResNet50)
2. ✅ FAISS Index (añadir, buscar, persistir)
3. ✅ Haversine Distance (cálculos geográficos)
4. ✅ Similitud de embeddings (idénticas vs diferentes)

### Salida esperada

```
============================================================
TESTS DEL SERVICIO DE DEDUPLICACIÓN B-07
============================================================

TEST 1: Visual Embedder
✓ Modelo cargado: ResNet50
✓ Dimensión de embeddings: 2048
✓ Dispositivo: cpu
✓ Embedding generado: shape=(2048,)
✓ Norma L2: 1.000000 (debe estar ~1.0)
✅ TEST 1 PASADO

TEST 2: FAISS Index
✓ Índice FAISS creado: dim=128, tipo=L2
✓ Añadidos 100 embeddings al índice
✓ Búsqueda k=3 completada
✅ TEST 2 PASADO

TEST 3: Haversine Distance
Mismo punto: ✓ OK
~100m al norte: ✓ OK
~1km al este: ✓ OK
✅ TEST 3 PASADO

TEST 4: Similitud de Embeddings
Distancia L2 (idénticas): 0.000000
Distancia L2 (diferentes): 1.234567
✅ TEST 4 PASADO

🎉 TODOS LOS TESTS PASADOS 🎉
```

## Arquitectura

```
Nueva imagen + GPS
       ↓
┌──────────────────────┐
│  Visual Embedder     │
│  (ResNet50)          │
│  Input: Image        │
│  Output: 2048-dim    │
└──────────────────────┘
       ↓
┌──────────────────────┐
│  FAISS Index         │
│  (IndexFlatL2)       │
│  Search top-K        │
│  visual neighbors    │
└──────────────────────┘
       ↓
┌──────────────────────┐
│  Filter candidates   │
│  - Same damage type  │
│  - Time window       │
└──────────────────────┘
       ↓
┌──────────────────────┐
│  Geographic Filter   │
│  (Haversine)         │
│  Calculate distance  │
└──────────────────────┘
       ↓
┌──────────────────────┐
│  Decision Logic      │
│  visual_dist < 0.15  │
│  AND                 │
│  geo_dist < 50m      │
└──────────────────────┘
       ↓
    DUPLICATE?
```

## Ajuste de Parámetros

### Umbrales recomendados por escenario

| Escenario | Visual | Geo | Descripción |
|-----------|--------|-----|-------------|
| Muy estricto | 0.08 | 20m | Solo casi idénticas |
| Moderado (default) | 0.15 | 50m | Balance precision/recall |
| Permisivo | 0.25 | 100m | Diferentes ángulos/luz |

### Modificar umbrales en tiempo real

```python
# En el request
data = {
    "latitude": 19.4515,
    "longitude": -70.6974,
    "damage_type": "bache",
    "visual_threshold": 0.20,  # Más permisivo
    "geo_threshold": 100.0     # Más permisivo
}
```

## Performance

### Tiempos típicos (CPU Intel i7)

| Operación | Tiempo |
|-----------|--------|
| Generar embedding | ~50ms |
| Búsqueda FAISS (k=20) | ~5ms |
| Calcular Haversine | <1ms |
| **Total verificación** | **~60ms** |

### Escalabilidad

| Reportes indexados | Tiempo de búsqueda | Memoria |
|--------------------|-------------------|---------|
| 1,000 | ~5ms | 10 MB |
| 10,000 | ~8ms | 100 MB |
| 100,000 | ~12ms | 1 GB |

## Archivos Creados

```
backend/
├── services/
│   └── deduplication_service.py          ← Servicio principal
├── api/routes/
│   └── deduplication.py                  ← Endpoints REST
├── schemas/
│   └── deduplication.py                  ← Modelos Pydantic
├── docs/
│   ├── B-07_IMPLEMENTATION.md            ← Documentación técnica
│   └── B-07_QUICKSTART.md                ← Esta guía
├── test_b07_deduplication.py             ← Tests unitarios
├── requirements.txt                       ← + faiss-cpu, scikit-learn
├── core/config.py                         ← + configuración B-07
└── main.py                                ← + registro de rutas
```

## Siguiente Paso: Integración

### 1. Modificar endpoint de creación de reportes

```python
# En api/routes/reports.py

@router.post("")
async def create_report(...):
    # ... validaciones ...
    
    # NUEVO: Verificar duplicado
    from services.deduplication_service import get_deduplication_service
    dedup_service = get_deduplication_service(db)
    
    is_duplicate, original_report, metadata = dedup_service.is_duplicate(
        image=img,
        latitude=latitude,
        longitude=longitude,
        damage_type=detected_damage_type
    )
    
    if is_duplicate:
        return JSONResponse(
            status_code=409,  # Conflict
            content={
                "error": "duplicate_report",
                "message": "Este daño ya fue reportado",
                "original_report_id": original_report.id,
                "metadata": metadata
            }
        )
    
    # ... crear reporte normalmente ...
    
    # Añadir al índice
    dedup_service.add_report_to_index(new_report, img)
```

### 2. Inicialización del índice al startup

```python
# En main.py

@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    dedup_service = get_deduplication_service(db)
    
    # Si el índice no existe, reconstruir
    if not Path(settings.FAISS_INDEX_PATH).exists():
        logger.info("Índice FAISS no encontrado, reconstruyendo...")
        dedup_service.rebuild_index()
    else:
        logger.info(f"Índice FAISS cargado: {dedup_service.get_statistics()}")
```

## Troubleshooting

### Error: "No module named 'faiss'"

```bash
pip install faiss-cpu==1.8.0
```

### Error: "torch not found"

```bash
pip install torch torchvision
```

### Índice corrupto

```bash
# Eliminar índice y reconstruir
rm storage/faiss_index.bin*

# Reconstruir via API
curl -X POST http://localhost:8000/api/v1/deduplication/index/rebuild \
  -H "Authorization: Bearer TOKEN"
```

### Lentitud en embedding

- **Solución 1**: Usar GPU (instalar `torch` con CUDA)
- **Solución 2**: Cambiar a `mobilenet_v2` (más rápido)
- **Solución 3**: Procesar en batch (múltiples reportes simultáneamente)

## Documentación Completa

Ver [B-07_IMPLEMENTATION.md](./docs/B-07_IMPLEMENTATION.md) para:
- Arquitectura detallada
- Benchmarks de performance
- Optimizaciones avanzadas
- Mejoras futuras (fine-tuning, DBSCAN, etc.)

## Contribuir

Para reportar bugs o sugerir mejoras:
1. Crear issue en GitHub
2. Incluir logs relevantes
3. Describir comportamiento esperado vs actual
4. Incluir ejemplos de imágenes si es posible

## Licencia

Parte del proyecto SIRCCD - Sistema Inteligente de Reporte Ciudadano de Calles Dañadas
