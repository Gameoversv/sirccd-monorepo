# D-04: Configuración de Data Augmentation

## 1. Técnicas de aumento recomendadas

- **Flip horizontal/vertical**: Simula cambios de orientación de la cámara.
- **Rotación**: ±10° a ±30° para simular inclinaciones leves.
- **Blur (desenfoque)**: GaussianBlur para simular lluvia o desenfoque de movimiento.
- **Brightness/Contrast**: Simula diferentes condiciones de luz (día, sombra, atardecer).
- **Random Cropping**: Simula encuadres parciales o recortes por obstáculos.
- **Color Jitter**: Variaciones de saturación y tono para simular asfalto desgastado.
- **Noise**: Añade ruido para simular baja calidad de imagen.

## 2. Simulación de condiciones urbanas RD

- **Lluvia**: Añadir líneas semitransparentes inclinadas (Albumentations: `IAARain`)
- **Sombras**: Polígonos oscuros aleatorios (Albumentations: `RandomShadow`)
- **Asfalto desgastado**: Variar textura y color (Albumentations: `RandomBrightnessContrast`, `CLAHE`)
- **Reflejos**: `RandomSunFlare` o `RandomFog` para simular reflejos y neblina

## 3. Ejemplo de pipeline con Albumentations

```python
import albumentations as A

transform = A.Compose([
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.1),
    A.Rotate(limit=20, p=0.4),
    A.GaussianBlur(blur_limit=(3,7), p=0.2),
    A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.4),
    A.RandomCrop(width=640, height=480, p=0.3),
    A.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.05, p=0.2),
    A.IAAAdditiveGaussianNoise(scale=(10, 30), p=0.15),
    A.IAARain(p=0.15),
    A.RandomShadow(p=0.15),
    A.CLAHE(p=0.1),
    A.RandomSunFlare(p=0.05),
    A.RandomFog(p=0.05),
], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
```

## 4. Configuración YOLOv8 (data.yaml o CLI)

YOLOv8 soporta augmentations nativos:
- `hsv_h`, `hsv_s`, `hsv_v`: Jitter de color
- `degrees`, `translate`, `scale`, `shear`, `perspective`
- `flipud`, `fliplr`
- `mosaic`, `mixup`, `copy_paste`

**Ejemplo CLI:**
```bash
yolo detect train data=... model=... epochs=50 \
  --hsv_h=0.015 --hsv_s=0.7 --hsv_v=0.4 \
  --degrees=20 --translate=0.1 --scale=0.5 --shear=2.0 \
  --flipud=0.1 --fliplr=0.5 --mosaic=1.0 --mixup=0.2
```

## 5. Recomendaciones

- Usar augmentations moderados para no distorsionar la semántica de baches/grietas.
- Simular lluvia y sombras solo en una fracción de imágenes (p=0.1-0.2).
- Validar visualmente el resultado antes de entrenar.
- Documentar la configuración final usada en cada experimento.

---

**Referencias:**
- [Albumentations Docs](https://albumentations.ai/docs/)
- [YOLOv8 Docs - Augmentations](https://docs.ultralytics.com/yolov8/augmentation/)
