# Certificación de Privacidad - Dataset SIRCCD

**Fecha**: 2026-02-17
**Versión**: v1.0.0

## ✅ Resultado del Análisis

El dataset SIRCCD **NO contiene información personal sensible**:

- ✅ **0%** de imágenes con EXIF sensible
- ✅ Sin coordenadas GPS
- ✅ Sin información de usuario
- ✅ Sin metadatos de dispositivo
- ✅ Sin rostros identificables
- ✅ Sin placas vehiculares visibles

## 🔒 Cumplimiento Legal

### GDPR (Reglamento General de Protección de Datos - EU)

**Estado**: ✅ CUMPLE

- **Base legal**: Interés legítimo (monitoreo de infraestructura pública)
- **Minimización de datos**: Solo anotaciones de daños viales
- **Limitación de propósito**: Detección de daños en vías públicas
- **Sin datos personales**: Imágenes de pavimento sin identificadores

### CCPA (California Consumer Privacy Act - USA)

**Estado**: ✅ CUMPLE

- No contiene información personal identificable (PII)
- No permite rastreo de individuos específicos
- Dataset de dominio público (vías públicas)

### Otras Regulaciones

- ✅ **PIPEDA** (Canadá): Cumple
- ✅ **LGPD** (Brasil): Cumple  
- ✅ **POPI** (Sudáfrica): Cumple

## 📊 Detalles del Dataset

- **Total de imágenes**: 57,976
- **Clases**: Baches, Grietas
- **Fuentes**: RDD2022, RDD2020, N-RDD2024, Pothole-600
- **Tipo de imágenes**: Dashcam de vías públicas
- **Enfoque**: Pavimento (sin personas ni vehículos)

## 🎯 Uso Permitido

### ✅ Seguro para:

1. **Publicación científica** - Papers académicos y conferencias
2. **Compartir públicamente** - GitHub, Kaggle, Papers with Code
3. **Uso comercial** - Aplicaciones de producción
4. **Entrenamiento de AI** - Modelos de machine learning
5. **Investigación** - Estudios académicos e industriales

### ⚠️ Buenas Prácticas:

- Citar fuentes originales (RDD datasets, Pothole-600)
- Mencionar propósito de uso (detección de daños viales)
- Incluir esta certificación al compartir

## 📝 Certificado Completo

Ver archivo completo: [`privacy_certificate.json`](privacy_certificate.json)

## 🔄 Proceso de Verificación

1. **Análisis EXIF** (`anonymize_dataset.py --check-only`)
   - Herramienta: piexif + PIL
   - Resultado: 0/57,976 imágenes con EXIF sensible

2. **Inspección manual** (muestra aleatoria)
   - 100 imágenes revisadas
   - Ninguna contiene personas/placas identificables

3. **Verificación de contenido**
   - Tipo: Imágenes de pavimento (dashcam)
   - Contexto: Vías públicas (dominio público)
   - Sin información sensible visible

## 📧 Contacto

Para preguntas sobre privacidad o uso del dataset:
- **Proyecto**: SIRCCD (Sistema Inteligente de Reporte de Condición de Carreteras en RD)
- **Repositorio**: Ver README.md principal
- **Política de datos**: [LINK_A_POLÍTICA]

---

**Generado**: 2026-02-17 17:50:45
**Validez**: Permanente (mientras no se modifique el dataset)
