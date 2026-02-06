# Documentación del Procesamiento de Datos

Esta carpeta contiene toda la documentación relacionada con el procesamiento, limpieza y preparación del dataset SIRCCD.

## 📄 Índice de Documentos

### Configuración y Criterios

- **[augmentation_config.md](augmentation_config.md)** - Configuración de data augmentation para entrenamiento
  - Técnicas: flip, rotation, blur, brightness, cropping
  - Frameworks: Albumentations + YOLOv8
  - Simulación de condiciones urbanas (lluvia, sombras, niebla)

- **[severity_criteria.md](severity_criteria.md)** - Criterios de clasificación de severidad
  - Baches: por área relativa (baja <1%, media 1-3%, alta ≥3%)
  - Grietas: por longitud relativa (baja <20%, media 20-40%, alta ≥40%)

### Reportes de Procesos

- **[CONVERSION_SUMMARY.md](CONVERSION_SUMMARY.md)** - Resumen de conversión de formatos
  - Conversión de datasets a formato YOLO
  - Mapeo de clases unificadas
  - Estadísticas de conversión

- **[CLEANING_REPORT.md](CLEANING_REPORT.md)** - Reporte de limpieza y balanceo (D-02)
  - Validación de integridad de imágenes
  - Detección y eliminación de duplicados
  - Balanceo de clases

- **[SPLIT_REPORT.md](SPLIT_REPORT.md)** - Reporte de división del dataset (D-03)
  - Particionado estratificado 70/20/10
  - Estadísticas por split
  - Seed: 42 para reproducibilidad

- **[SEVERITY_REPORT.md](SEVERITY_REPORT.md)** - Reporte de etiquetado de severidad (D-05)
  - Proceso automatizado de etiquetado
  - Ejemplos de clasificación
  - Criterios aplicados

### Guías de Implementación

- **[D-07_MINIO_INGESTION.md](D-07_MINIO_INGESTION.md)** - Ingesta a MinIO (D-07)
  - Configuración de MinIO con Docker
  - Estructura de buckets y versionado
  - Metadata schema y validación
  - Proceso de ingesta con hashing SHA256

- **[D-08_ANONYMIZATION.md](D-08_ANONYMIZATION.md)** - Anonimización y Privacidad (D-08)
  - Eliminación de metadatos EXIF sensibles (GPS, usuario, dispositivo)
  - Detección y difuminado de rostros/placas (implementado, requiere Python estable)
  - Cumplimiento de GDPR/CCPA
  - Proceso de validación y reporte

- **[ANONYMIZATION_REPORT.md](ANONYMIZATION_REPORT.md)** - Reporte de Ejecución D-08
  - 57,976 imágenes procesadas
  - EXIF completamente eliminado
  - Dataset seguro para compartir
  - Limitaciones técnicas (Python 3.14-alpha)

## 🔄 Flujo de Procesamiento

```
1. Datasets Raw
   ↓
2. Conversión (CONVERSION_SUMMARY.md)
   ↓
3. Limpieza y Balanceo (CLEANING_REPORT.md)
   ↓
4. División Estratificada (SPLIT_REPORT.md)
   ↓
5. Etiquetado de Severidad (SEVERITY_REPORT.md)
   ↓
6. Data Augmentation (augmentation_config.md)
   ↓
7. Ingesta a MinIO (D-07_MINIO_INGESTION.md)
   ↓
8. Anonimización (D-08_ANONYMIZATION.md)
```

## 📊 Estado Actual del Dataset

- **Versión**: v1.0.0
- **Total imágenes**: 58,209
- **Clases**: bache (0), grieta (2)
- **Splits**: train (70%), val (20%), test (10%)
- **Severidad**: Etiquetada en todas las muestras
- **Almacenamiento**: MinIO (bucket: sirccd-datasets)

## 🔗 Referencias

Para instrucciones de uso de los scripts, consulta el [README principal](../README.md).
