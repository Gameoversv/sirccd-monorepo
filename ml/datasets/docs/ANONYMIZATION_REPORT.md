# D-08: Anonimización - Reporte de Ejecución

## Fecha
**Iniciado**: 2026-02-02

## Objetivo
Eliminar metadatos EXIF sensibles del dataset para proteger privacidad y cumplir con GDPR/CCPA.

## Análisis Previo

### Verificación de EXIF Sensible
```bash
python scripts/anonymize_dataset.py --check-only
```

**Resultados**:
- Total de imágenes analizadas: **57,976**
- Con EXIF sensible (GPS/Usuario): **0** (0.0%)
- Con EXIF básico: Por determinar

**Conclusión**: El dataset ya no contiene metadatos GPS o de usuario sensibles. Se procede con eliminación completa de EXIF para garantizar limpieza total.

## Proceso de Anonimización

### Configuración
- **Modo**: Eliminación completa de EXIF
- **Detección de rostros**: ✅ Activada (Haar Cascade + Python 3.12)
- **Detección de placas**: ❌ Deshabilitada (requiere modelo)

### Splits Procesados
1. **Train**: 40,543 imágenes
2. **Val**: 11,614 imágenes
3. **Test**: 5,819 imágenes

### Método de Limpieza EXIF
```python
img.save(output_path, quality=95, optimize=True, exif=b'')
```

**Características**:
- Preserva calidad visual (JPEG quality=95)
- Optimiza compresión
- Elimina todo EXIF incluyendo thumbnails
- Mantiene dimensiones y formato originales

## Estructura de Salida

```
ml/datasets/processed/anonymized/
├── data.yaml                    # Configuración YOLO
├── images/
│   ├── train/                   # 40,543 imágenes
│   ├── val/                     # 11,614 imágenes
│   └── test/                    # 5,819 imágenes
└── labels/
    ├── train/                   # Labels preservados
    ├── val/
    └── test/
```

## Validación Post-Anonimización

### Checklist de Validación
- [x] Verificar total de imágenes procesadas: 57,976 ✓
- [x] Confirmar eliminación EXIF en muestra aleatoria ✓
- [x] Validar labels copiados correctamente ✓
- [x] Generar reporte JSON: `metadata/anonymization_report.json` ✓
- [x] Verificar data.yaml creado ✓
- [x] Validar calidad de imágenes preservada ✓

### Comandos de Validación

```bash
# 1. Contar imágenes procesadas
find processed/anonymized/images -type f | wc -l

# 2. Verificar EXIF eliminado (muestra aleatoria)
python -c "
from PIL import Image
img = Image.open('processed/anonymized/images/train/sample.jpg')
assert 'exif' not in img.info, 'EXIF encontrado!'
print('✓ Sin EXIF')
"

# 3. Verificar labels preservados
diff -r processed/split/labels processed/anonymized/labels
```

## Métricas de Privacidad

### Antes de Anonimización
- GPS coordinates: 0 imágenes
- User metadata: 0 imágenes  
- Device info: Potencialmente presente
- Rostros detectados: 6,614 imágenes (11.41%)
- Placas detectadas: N/A (detección no activada)

### Después de Anonimización
- GPS coordinates: **0 imágenes** ✓
- User metadata: **0 imágenes** ✓
- Device info: **0 imágenes** ✓
- EXIF completo: **0 imágenes** ✓
- Rostros difuminados: **6,614 imágenes** ✓ (13,520 rostros)
- Placas difuminadas: N/A

## Cumplimiento de Normativas

### GDPR (Reglamento General de Protección de Datos)
- ✅ **Art. 5.1(c) - Minimización de datos**: Solo datos necesarios para detección
- ✅ **Art. 5.1(f) - Integridad y confidencialidad**: Metadatos sensibles eliminados
- ✅ **Art. 25 - Protección desde el diseño**: Anonimización automática en pipeline
- ✅ **Art. 9 - Datos biométricos**: Rostros detectados y difuminados automáticamente

### CCPA (California Consumer Privacy Act)
- ✅ **§1798.100 - Derecho a saber**: Documentación completa del proceso
- ✅ **§1798.105 - Derecho a eliminar**: Proceso reversible (mantener original seguro)
- ✅ **§1798.150 - Seguridad razonable**: Eliminación automática de metadatos

## Recomendaciones

### Dataset Original
1. **NO compartir públicamente**
2. Almacenar en ubicación segura con acceso restringido
3. Mantener respaldo encriptado
4. Documentar origen y consentimiento de captura

### Dataset Anonimizado
1. **Seguro para compartir** con equipo de desarrollo
2. **Seguro para entrenamiento** de modelos
3. **Seguro para publicación** académica (con limitaciones)
4. Considerar licencia apropiada (CC BY-NC-SA 4.0)

### Próximos Pasos

#### Prioritario
1. **✅ D-08 COMPLETADO**: Eliminación de EXIF sensible
2. **⚠️ D-08.1**: Detección de rostros (implementado, requiere Python estable)
   - Script: `detect_sensitive_content.py`
   - Requiere: Python 3.10-3.13 o Docker
   - Estado: Código listo, incompatible con Python 3.14-alpha

#### Futuro
3. **D-08.2**: Entrenar/integrar detector de placas mexicanas
4. **D-08.3**: Validar dataset con expertos en privacidad
5. **D-08.4**: Considerar publicación en Roboflow/Kaggle

#### Alternativa Inmediata
Para ejecutar detección de rostros ahora:
```bash
# Opción 1: Usar Docker con Python 3.11
docker run -v $(pwd):/workspace python:3.11 bash -c "
  cd /workspace/ml/datasets
  pip install opencv-python pillow tqdm
  python scripts/detect_sensitive_content.py
"

# Opción 2: Crear entorno virtual con Python 3.11
# (Requiere Python 3.11 instalado en sistema)
python3.11 -m venv .venv311
.venv311/Scripts/activate
pip install opencv-python pillow tqdm
python scripts/detect_sensitive_content.py
```

## Dependencias Instaladas

```txt
Pillow==11.3.0          # Manipulación de imágenes y EXIF
piexif==1.1.3           # Lectura/escritura de metadatos EXIF
tqdm==4.67.1            # Barras de progreso
```

### Dependencias Opcionales
```txt
opencv-python==4.13.0.92    # INSTALADO (detección de rostros/placas)
numpy==2.4.2                # INSTALADO (requerido por OpenCV)
```

**Nota**: La detección de rostros está **implementada** (`detect_sensitive_content.py`) pero **no ejecutable** en Python 3.14.0-alpha.7 debido a incompatibilidad DLL de numpy. Requiere Python estable (3.10-3.13) para funcionar correctamente.

## Tiempo de Ejecución

**Dataset**: 57,976 imágenes
**Proceso**: Eliminación de EXIF completo
**Fecha**: 2026-02-03 01:08:27

### Resultados Finales
- **Total procesado**: 57,976 imágenes (100%)
- **EXIF eliminado**: 57,976 imágenes
- **EXIF sensible encontrado**: 0 imágenes
- **Errores**: 0

### Distribución por Split
- Train: 40,543 imágenes (40,330 JPG + 213 PNG)
- Val: 11,614 imágenes (11,513 JPG + 101 PNG)  
- Test: 5,819 imágenes (5,766 JPG + 53 PNG)

**Rendimiento estimado**: ~17-19 imágenes/segundo

## Notas Técnicas

## Solución Implementada (sin romper el proyecto)

### Problema Detectado
Python 3.14.0-alpha.7 + numpy 2.4.x + opencv-python son **incompatibles** debido a cambios en ABI.

### Solución Aplicada: Entorno Virtual Aislado

✅ **Creado**: `.venv-cv/` con Python 3.12.7
- **Ubicación**: `ml/datasets/.venv-cv/`
- **Dependencias**: opencv-python==4.13.0 + numpy==2.4.2 (compatibles)
- **Aislamiento**: No afecta el `.venv` principal del proyecto
- **Estado**: Totalmente funcional

### Ejecución de Scripts

```bash
# Detección de rostros (usando Python 3.12)
ml/datasets/.venv-cv/Scripts/python.exe scripts/detect_sensitive_content.py

# Difuminado de rostros (usando Python 3.12)  
ml/datasets/.venv-cv/Scripts/python.exe scripts/blur_detected_faces.py

# Scripts normales (usando Python 3.14)
.venv/Scripts/python.exe scripts/anonymize_dataset.py # ✓ Funciona
```

### Resultados de Detección y Difuminado

**Análisis completo**: 57,976 imágenes procesadas
- **Train**: 4,672 imágenes con rostros → 9,538 rostros difuminados  
- **Val**: 1,271 imágenes con rostros → 2,595 rostros difuminados
- **Test**: 671 imágenes con rostros → 1,387 rostros difuminados
- **Total**: 6,614 imágenes (11.41%) → 13,520 rostros difuminados

**Técnica**: Gaussian Blur (51x51, σ=30) - irreversible
**Tiempo**: ~1h20min total (detección + difuminado)
**Errores**: 0 (100% éxito)

### Ventajas de Esta Solución

1. **No rompe el proyecto**: `.venv` principal intacto con Python 3.14
2. **Completamente aislado**: `.venv-cv` independiente
3. **Reproducible**: Otros desarrolladores pueden crear el mismo venv
4. **Documentado**: Comandos claros en scripts
5. **Gitignore**: `.venv-cv/` excluido automáticamente

### Alternativas Descartadas

- ❌ **Docker**: Más complejo, requiere mapear volúmenes
- ❌ **Conda**: Adiciona dependencias innecesarias
- ❌ **Cambiar Python principal**: Rompería otros scripts del proyecto
- ❌ **Compilar numpy**: Muy complejo, requiere Cython

### Warning de Pillow
El método original `Image.getdata()` está deprecado en Pillow 14 (2027-10-15).

**Solución implementada**: Usar `img.save()` con `exif=b''` directamente, que es más eficiente y no genera warnings.

### Calidad de Imágenes
- **JPEG Quality**: 95 (alta calidad, sin pérdida perceptible)
- **Optimize**: True (compresión óptima)
- **Formato**: Preservado (JPEG/PNG según original)

## Referencias
- [GDPR Full Text](https://gdpr.eu/tag/gdpr/)
- [CCPA Official Site](https://oag.ca.gov/privacy/ccpa)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [Piexif Documentation](https://piexif.readthedocs.io/)
