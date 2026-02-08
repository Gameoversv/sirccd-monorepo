# Imágenes de Prueba - Detección de Rostros

Este directorio contiene imágenes de prueba para validar la detección de rostros con MediaPipe.

## 📋 Instrucciones de Uso

### 1. Copiar Imágenes de Prueba

Copiar las imágenes que deseas probar a este directorio:

```
data/imagenes_prueba/
```

**Imágenes recomendadas**:
- ✅ 2-3 imágenes CON rostros visibles (personas en la calle, peatones, etc.)
- ✅ 2-3 imágenes SIN rostros (calles vacías, paisajes urbanos, etc.)

Esto permitirá validar tanto la detección correcta como la ausencia de falsos positivos.

### 2. Ejecutar Script de Prueba

Desde el directorio raíz del monorepo:

```bash
python ml/datasets/scripts/test_face_detection_manual.py
```

### 3. Revisar Resultados

Los resultados se guardarán en:

```
data/imagenes_prueba/output/
├── detected/    # Imágenes con rectángulos rojos marcando rostros detectados
└── blurred/     # Imágenes con rostros difuminados automáticamente
```

## 📊 Interpretación de Resultados

### Caso 1: Detección Exitosa
```
✅ Rostros detectados correctamente
📷 Imagen con personas → Rostros marcados en rojo
🔒 Rostros difuminados con blur gaussiano adaptativo
```

### Caso 2: Sin Rostros (Normal)
```
ℹ️  No se detectaron rostros
📷 Imagen de calle vacía → Sin marcas (correcto)
```

### Caso 3: Falso Positivo (Raro con MediaPipe)
```
⚠️  Rostro detectado donde no hay personas
Revisar imagen en detected/ para verificar
```

## 🎯 Métricas de Éxito

El sistema funciona correctamente cuando:

- ✅ Detecta rostros en imágenes CON personas
- ✅ NO detecta rostros en imágenes SIN personas  
- ✅ El difuminado cubre completamente cada rostro
- ✅ El difuminado es irreversible

## 🔧 Configuración de MediaPipe

- **Model selection**: 1 (rango completo, ideal para dash cam)
- **Min confidence**: 0.5 (50% de confianza mínima)
- **Margin expansion**: 20% (asegurar cobertura completa)
- **Blur kernel**: Adaptativo (30% del tamaño del rostro)

## 📝 Siguiente Paso

Una vez validado que funciona correctamente:

```bash
# Procesar dataset completo con detección de rostros
python ml/datasets/scripts/anonymize_dataset.py --detect-faces
```

⏱️ Tiempo estimado para 57,976 imágenes: ~30-60 minutos (depende del hardware)

## 🚨 Notas Importantes

- Las imágenes originales NO se modifican
- Las imágenes de salida se guardan en `output/`
- Puedes ejecutar el script múltiples veces sin problemas
- Los resultados visuales ayudan a validar antes del procesamiento masivo
