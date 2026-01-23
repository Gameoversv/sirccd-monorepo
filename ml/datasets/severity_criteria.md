# Criterios de Severidad para Baches y Grietas

## 1. Definición de Severidad

La severidad se etiqueta en tres niveles:
- **Baja**
- **Media**
- **Alta**

## 2. Criterios para Baches (área)

- **Área**: Se calcula como ancho × alto del bounding box (en píxeles o proporción respecto a la imagen).
- **Umbrales sugeridos** (proporción del área de la imagen):
  - **Baja**: área < 1%
  - **Media**: 1% ≤ área < 3%
  - **Alta**: área ≥ 3%

## 3. Criterios para Grietas (longitud)

- **Longitud**: Se estima como el mayor lado del bounding box (en píxeles o proporción respecto a la imagen).
- **Umbrales sugeridos** (proporción respecto al ancho/alto de la imagen):
  - **Baja**: longitud < 20%
  - **Media**: 20% ≤ longitud < 40%
  - **Alta**: longitud ≥ 40%

## 4. Consideraciones

- Si se dispone de máscara, calcular área real (número de píxeles positivos).
- Si solo hay bbox, usar área/longitud del bbox como aproximación.
- Los umbrales pueden ajustarse según la distribución real del dataset.

## 5. Ejemplo de cálculo

- Imagen: 1280x720 px (921,600 px²)
- Bache bbox: 80x60 px (4,800 px²)
  - Área relativa: 0.52% → **Baja**
- Grieta bbox: 400x20 px (mayor lado = 400 px)
  - Longitud relativa: 400/1280 = 31.2% → **Media**

---

**Referencias:**
- Manuales de conservación vial (INEGI, ASTM D6433)
- Prácticas de datasets públicos (RDD, Pothole-600)
