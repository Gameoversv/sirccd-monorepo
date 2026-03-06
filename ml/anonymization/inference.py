"""
inference.py — Inferencia YOLO11 + blur para anonimización de imágenes

Puede usarse standalone o como módulo importado por el backend.

Uso CLI:
  python ml/anonymization/inference.py --input img.jpg --output anon.jpg
  python ml/anonymization/inference.py --input ./fotos/ --output ./anon/

Como módulo:
  from ml.anonymization.inference import YOLOAnonymizer
  anon = YOLOAnonymizer("path/to/best.pt")
  result_bytes, stats = anon.anonymize(image_bytes)
"""

import argparse
import io
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image


CLASS_NAMES = {0: "face", 1: "license_plate"}
DEFAULT_WEIGHTS = Path(__file__).resolve().parent / "runs" / "anonymizer_v1" / "weights" / "best.pt"


class YOLOAnonymizer:
    """
    Detector YOLO11 para anonimización de rostros y placas con blur.

    Flujo:
      1. Detectar bounding boxes (face, license_plate)
      2. Expandir cada bbox +20%
      3. Aplicar GaussianBlur(51, 30) sobre cada ROI
    """

    def __init__(
        self,
        weights_path: Optional[str] = None,
        conf: float = 0.25,
        iou: float = 0.45,
        imgsz: int = 640,
        device: str = "",
    ):
        """
        Args:
            weights_path: Ruta a best.pt. Si None, busca ruta por defecto.
            conf: Threshold de confianza (bajo = más recall).
            iou: Threshold de NMS IoU.
            imgsz: Tamaño de imagen para inferencia.
            device: "cpu", "cuda", "0", etc. Vacío = auto.
        """
        from ultralytics import YOLO

        if weights_path is None:
            weights_path = str(DEFAULT_WEIGHTS)

        self.model = YOLO(weights_path)
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz
        self.device = device

    def detect(self, image: np.ndarray) -> list[dict]:
        """
        Ejecuta detección sobre una imagen BGR numpy array.

        Returns:
            Lista de detecciones: [{"class": int, "name": str, "conf": float,
                                     "box": [x1, y1, x2, y2]}]
        """
        results = self.model.predict(
            image,
            conf=self.conf,
            iou=self.iou,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )

        detections = []
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                detections.append({
                    "class": cls,
                    "name": CLASS_NAMES.get(cls, f"class_{cls}"),
                    "conf": float(box.conf[0]),
                    "box": box.xyxy[0].cpu().numpy().tolist(),  # [x1, y1, x2, y2]
                })

        return detections

    def blur_regions(
        self,
        image: np.ndarray,
        detections: list[dict],
        margin: float = 0.2,
        blur_kernel: int = 51,
        blur_sigma: float = 30.0,
    ) -> tuple[np.ndarray, int]:
        """
        Aplica GaussianBlur sobre cada bounding box detectada.

        Args:
            image: Imagen BGR.
            detections: Lista de detecciones del método detect().
            margin: Fracción de expansión de la bbox (0.2 = 20%).
            blur_kernel: Tamaño del kernel gaussiano (debe ser impar).
            blur_sigma: Sigma del blur gaussiano.

        Returns:
            (imagen_blurred, count_blurred)
        """
        result = image.copy()
        h_img, w_img = result.shape[:2]
        count = 0

        for det in detections:
            x1, y1, x2, y2 = det["box"]
            bw = x2 - x1
            bh = y2 - y1

            # Expandir bbox
            mx = bw * margin
            my = bh * margin
            x1 = max(0, int(x1 - mx))
            y1 = max(0, int(y1 - my))
            x2 = min(w_img, int(x2 + mx))
            y2 = min(h_img, int(y2 + my))

            if x2 <= x1 or y2 <= y1:
                continue

            roi = result[y1:y2, x1:x2]

            # Kernel adaptativo: mínimo blur_kernel, máximo proporcional al ROI
            k = max(blur_kernel, min(roi.shape[0], roi.shape[1]) // 3)
            if k % 2 == 0:
                k += 1

            blurred_roi = cv2.GaussianBlur(roi, (k, k), blur_sigma)
            result[y1:y2, x1:x2] = blurred_roi
            count += 1

        return result, count

    def anonymize(
        self,
        image_bytes: bytes,
        detect_faces: bool = True,
        detect_plates: bool = True,
    ) -> tuple[bytes, dict]:
        """
        Anonimiza una imagen completa — interfaz compatible con el backend.

        Args:
            image_bytes: Bytes de la imagen de entrada (JPEG/PNG).
            detect_faces: Si True, detecta y difumina rostros.
            detect_plates: Si True, detecta y difumina placas.

        Returns:
            (bytes_anonimizados, stats_dict)
        """
        stats = {
            "faces_detected": 0,
            "plates_detected": 0,
            "regions_blurred": 0,
            "anonymized": False,
            "error": None,
            "detections": [],
        }

        try:
            # Decodificar imagen
            pil_image = Image.open(io.BytesIO(image_bytes))
            image_np = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            # Detectar
            all_detections = self.detect(image_np)

            # Filtrar por tipo solicitado
            filtered = []
            for d in all_detections:
                if d["class"] == 0 and detect_faces:
                    stats["faces_detected"] += 1
                    filtered.append(d)
                elif d["class"] == 1 and detect_plates:
                    stats["plates_detected"] += 1
                    filtered.append(d)

            stats["detections"] = filtered

            # Aplicar blur
            blurred, count = self.blur_regions(image_np, filtered)
            stats["regions_blurred"] = count
            stats["anonymized"] = count > 0

            # Codificar resultado
            blurred_rgb = cv2.cvtColor(blurred, cv2.COLOR_BGR2RGB)
            pil_out = Image.fromarray(blurred_rgb)

            out_buffer = io.BytesIO()
            fmt = pil_image.format or "JPEG"
            save_kwargs = {"format": fmt}
            if fmt in ("JPEG", "JPG"):
                save_kwargs["quality"] = 95
                save_kwargs["optimize"] = True
            pil_out.save(out_buffer, **save_kwargs)

            return out_buffer.getvalue(), stats

        except Exception as e:
            stats["error"] = str(e)
            return image_bytes, stats


def process_file(anonymizer: YOLOAnonymizer, input_path: Path, output_path: Path):
    """Anonimiza un archivo de imagen."""
    with open(input_path, "rb") as f:
        img_bytes = f.read()

    result_bytes, stats = anonymizer.anonymize(img_bytes)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(result_bytes)

    faces = stats["faces_detected"]
    plates = stats["plates_detected"]
    blurred = stats["regions_blurred"]
    print(f"  {input_path.name} → rostros: {faces}, placas: {plates}, blur: {blurred}")


def main():
    parser = argparse.ArgumentParser(description="YOLO11 Anonymizer — blur faces & license plates")
    parser.add_argument("--input", "-i", required=True, help="Imagen o directorio de entrada")
    parser.add_argument("--output", "-o", required=True, help="Imagen o directorio de salida")
    parser.add_argument("--weights", "-w", default=None, help="Ruta a best.pt")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--imgsz", type=int, default=640, help="Tamaño de imagen")
    parser.add_argument("--device", default="", help="Device: cpu, cuda, 0")
    args = parser.parse_args()

    anonymizer = YOLOAnonymizer(
        weights_path=args.weights,
        conf=args.conf,
        imgsz=args.imgsz,
        device=args.device,
    )

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_file():
        process_file(anonymizer, input_path, output_path)
    elif input_path.is_dir():
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        images = [p for p in sorted(input_path.iterdir()) if p.suffix.lower() in exts]
        print(f"Procesando {len(images)} imágenes de {input_path}...")
        for img in images:
            out = output_path / img.name
            process_file(anonymizer, img, out)
        print(f"\n✅ {len(images)} imágenes anonimizadas → {output_path}")
    else:
        print(f"❌ No encontrado: {input_path}")


if __name__ == "__main__":
    main()
