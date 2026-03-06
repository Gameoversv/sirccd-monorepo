"""
Servicio de anonimización de imágenes - Blur de rostros y placas

Implementa B-05: Middleware para difuminar rostros y placas antes de persistir.

Detector: YOLO11s Detect (2 clases: face, license_plate)
"""

import io
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List
from PIL import Image
from dataclasses import dataclass


@dataclass
class BlurRegion:
    """Región detectada para aplicar blur"""
    x1: int
    y1: int
    x2: int
    y2: int
    type: str  # 'face' o 'license_plate'
    confidence: float = 1.0


# Rutas posibles para el modelo YOLO11 de anonimización
_MODEL_SEARCH_PATHS = [
    Path(__file__).resolve().parent.parent.parent / "ml" / "anonymization" / "runs" / "anonymizer_v1" / "weights" / "best.pt",
    Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "anonymizer" / "best.pt",
    Path(__file__).resolve().parent / "models" / "anonymizer_best.pt",
]

_CLASS_NAMES = {0: "face", 1: "license_plate"}


class ImageAnonymizer:
    """
    Servicio para anonimizar imágenes detectando y difuminando rostros y placas
    mediante YOLO11s Detect.
    """

    def __init__(self, conf: float = 0.25, iou: float = 0.45, imgsz: int = 640):
        self.yolo_model = None
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz
        self._load_model()

    def _load_model(self):
        """Carga el modelo YOLO11 entrenado para anonimización"""
        try:
            from ultralytics import YOLO

            for model_path in _MODEL_SEARCH_PATHS:
                if model_path.exists():
                    self.yolo_model = YOLO(str(model_path))
                    print(f"✅ YOLO11 anonymizer cargado: {model_path}")
                    return

            print("⚠  No se encontró modelo YOLO11 para anonimización (best.pt)")
        except ImportError:
            print("⚠  ultralytics no instalado — anonimización no disponible")
        except Exception as e:
            print(f"⚠  Error cargando YOLO11: {e}")

    @property
    def available(self) -> bool:
        return self.yolo_model is not None

    def detect(self, image: np.ndarray) -> List[BlurRegion]:
        """
        Detecta rostros y placas en la imagen con YOLO11.

        Args:
            image: Imagen BGR (numpy array)

        Returns:
            Lista de BlurRegion con coordenadas absolutas (x1,y1,x2,y2)
        """
        if not self.available:
            return []

        results = self.yolo_model.predict(
            image,
            conf=self.conf,
            iou=self.iou,
            imgsz=self.imgsz,
            verbose=False,
        )

        regions: List[BlurRegion] = []
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
                regions.append(BlurRegion(
                    x1=int(x1),
                    y1=int(y1),
                    x2=int(x2),
                    y2=int(y2),
                    type=_CLASS_NAMES.get(cls, f"class_{cls}"),
                    confidence=float(box.conf[0]),
                ))

        return regions

    def apply_blur(
        self,
        image: np.ndarray,
        regions: List[BlurRegion],
        margin: float = 0.2,
        blur_kernel: int = 51,
        blur_sigma: float = 30.0,
    ) -> Tuple[np.ndarray, int]:
        """
        Aplica blur gaussiano a cada región detectada, con margen de expansión.

        Args:
            image: Imagen original BGR
            regions: Regiones a difuminar
            margin: Fracción de expansión de cada bbox (0.2 = 20%)
            blur_kernel: Tamaño mínimo del kernel gaussiano (impar)
            blur_sigma: Sigma del blur

        Returns:
            (imagen_procesada, cantidad_de_regiones_difuminadas)
        """
        if not regions:
            return image, 0

        blurred = image.copy()
        h_img, w_img = blurred.shape[:2]
        count = 0

        for region in regions:
            bw = region.x2 - region.x1
            bh = region.y2 - region.y1
            mx = int(bw * margin)
            my = int(bh * margin)

            x1 = max(0, region.x1 - mx)
            y1 = max(0, region.y1 - my)
            x2 = min(w_img, region.x2 + mx)
            y2 = min(h_img, region.y2 + my)

            if x2 <= x1 or y2 <= y1:
                continue

            roi = blurred[y1:y2, x1:x2]
            k = max(blur_kernel, min(roi.shape[0], roi.shape[1]) // 3)
            if k % 2 == 0:
                k += 1

            blurred[y1:y2, x1:x2] = cv2.GaussianBlur(roi, (k, k), blur_sigma)
            count += 1

        return blurred, count

    def anonymize(
        self,
        image_bytes: bytes,
        detect_faces: bool = True,
        detect_plates: bool = True,
    ) -> Tuple[bytes, dict]:
        """
        Anonimiza una imagen detectando y difuminando rostros y placas.

        Args:
            image_bytes: Bytes de la imagen original
            detect_faces: Si True, difumina rostros
            detect_plates: Si True, difumina placas

        Returns:
            (bytes_anonimizados, estadísticas)
        """
        stats = {
            'faces_detected': 0,
            'plates_detected': 0,
            'regions_blurred': 0,
            'anonymized': False,
            'error': None,
        }

        if not self.available:
            stats['error'] = 'Modelo YOLO11 no disponible'
            return image_bytes, stats

        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            image_np = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            all_regions = self.detect(image_np)

            # Filtrar por tipo solicitado
            filtered: List[BlurRegion] = []
            for r in all_regions:
                if r.type == 'face' and detect_faces:
                    stats['faces_detected'] += 1
                    filtered.append(r)
                elif r.type == 'license_plate' and detect_plates:
                    stats['plates_detected'] += 1
                    filtered.append(r)

            blurred_image, blur_count = self.apply_blur(image_np, filtered)
            stats['regions_blurred'] = blur_count
            stats['anonymized'] = blur_count > 0

            blurred_pil = Image.fromarray(cv2.cvtColor(blurred_image, cv2.COLOR_BGR2RGB))

            output = io.BytesIO()
            fmt = pil_image.format or 'JPEG'
            save_kwargs = {'format': fmt}
            if fmt in ('JPEG', 'JPG'):
                save_kwargs['quality'] = 95
                save_kwargs['optimize'] = True

            blurred_pil.save(output, **save_kwargs)
            return output.getvalue(), stats

        except Exception as e:
            stats['error'] = str(e)
            print(f"⚠  Error anonimizando imagen: {e}")
            return image_bytes, stats


# Instancia global del servicio
image_anonymizer = ImageAnonymizer()
