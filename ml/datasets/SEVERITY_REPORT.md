# D-05: Etiquetado de Severidad (área/longitud)

## 1. Objetivo

Etiquetar automáticamente la severidad de baches y grietas en los labels YOLO, usando área (bache) o longitud (grieta) relativa al tamaño de la imagen.

## 2. Criterios de Severidad

- **Bache (área relativa):**
  - Baja: área < 1%
  - Media: 1% ≤ área < 3%
  - Alta: área ≥ 3%
- **Grieta (longitud relativa):**
  - Baja: longitud < 20%
  - Media: 20% ≤ longitud < 40%
  - Alta: longitud ≥ 40%

## 3. Proceso Automatizado

- Script: `label_severity.py`
- Entrada: labels YOLOv8 (`processed/split/labels/`)
- Salida: labels con severidad (`processed/split/labels_severity/`)
- Para cada objeto:
  - Calcula área y/o longitud relativa
  - Asigna severidad según umbrales
  - Añade la etiqueta al final de cada línea del label

**Ejemplo de línea resultante:**
```
0 0.5 0.5 0.1 0.1 baja
2 0.3 0.7 0.4 0.05 media
```

## 4. Ejemplo de cálculo

- Imagen: 1280x720 px
- Bache bbox: 80x60 px → área 0.52% → **baja**
- Grieta bbox: 400x20 px → longitud 31.2% → **media**

## 5. Consideraciones

- Si existen máscaras, se recomienda calcular área real para mayor precisión.
- Los umbrales pueden ajustarse según la distribución real del dataset.
- La severidad puede usarse como clase adicional o para análisis estadístico.

## 6. Referencias
- `severity_criteria.md` (criterios detallados)
- Manuales de conservación vial (INEGI, ASTM D6433)
- Prácticas de datasets públicos (RDD, Pothole-600)

---

**Generado por:** `label_severity.py`  
**Última actualización:** 2026-01-22
