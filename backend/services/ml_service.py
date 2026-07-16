"""
Servicio de Inferencia ML - Roboflow Hosted API (Instance Segmentation)
"""

import os
import json
import logging
import tempfile
from typing import Dict, List, Optional

from PIL import Image

from core.config import settings
from models.report import DamageType, SeverityLevel

logger = logging.getLogger(__name__)


class BoundingBox:
    """Representa una detección con bounding box y máscara de segmentación"""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        confidence: float,
        class_name: str,
        class_id: int,
        points: Optional[List[Dict]] = None,  # polígono de segmentación
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence
        self.class_name = class_name
        self.class_id = class_id
        self.points = points or []  # [{"x": ..., "y": ...}, ...]

    def to_dict(self) -> dict:
        return {
            "x": float(self.x),
            "y": float(self.y),
            "width": float(self.width),
            "height": float(self.height),
            "confidence": float(self.confidence),
            "class_name": self.class_name,
            "class_id": int(self.class_id),
            "points": self.points,
        }

    def area(self) -> float:
        if len(self.points) >= 3:
            pts = self.points
            n = len(pts)
            a = 0.0
            for i in range(n):
                j = (i + 1) % n
                a += pts[i]["x"] * pts[j]["y"]
                a -= pts[j]["x"] * pts[i]["y"]
            return abs(a) / 2.0
        return self.width * self.height


class DetectionResult:
    """Resultado de detección ML"""

    MODEL_PRECISION = 0.0
    MODEL_RECALL = 0.0
    MODEL_MAP50 = 0.0
    MODEL_MAP50_95 = 0.0

    def __init__(
        self,
        damage_type: DamageType,
        severity: SeverityLevel,
        confidence: float,
        bounding_boxes: List[BoundingBox],
        image_width: int,
        image_height: int,
        model_version: str = "roboflow",
    ):
        self.damage_type = damage_type
        self.severity = severity
        self.confidence = confidence
        self.bounding_boxes = bounding_boxes
        self.image_width = image_width
        self.image_height = image_height
        self.model_version = model_version

    def to_dict(self) -> dict:
        return {
            "damage_type": self.damage_type.value,
            "severity": self.severity.value,
            "confidence": float(self.confidence),
            "bounding_boxes": [bb.to_dict() for bb in self.bounding_boxes],
            "image_width": self.image_width,
            "image_height": self.image_height,
            "model_version": self.model_version,
            "num_detections": len(self.bounding_boxes),
            "model_precision": MLInferenceService.MODEL_PRECISION,
            "model_recall": MLInferenceService.MODEL_RECALL,
            "model_map50": MLInferenceService.MODEL_MAP50,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class MLInferenceService:
    """Servicio de inferencia usando Roboflow Instance Segmentation API"""

    MODEL_PRECISION = 0.0
    MODEL_RECALL = 0.0
    MODEL_MAP50 = 0.0
    MODEL_MAP50_95 = 0.0

    CLASS_MAPPING: Dict[str, DamageType] = {
        "pothole": DamageType.BACHE,
        "bache": DamageType.BACHE,
        "crack": DamageType.GRIETA,
        "grieta": DamageType.GRIETA,
    }

    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        if not use_mock:
            self._init_client()

    def _init_client(self):
        if not settings.ROBOFLOW_API_KEY:
            logger.warning("ROBOFLOW_API_KEY no configurada. Usando mock.")
            self.use_mock = True
            return

        try:
            import requests
            logger.info(f"Roboflow API lista. Modelo: {settings.ROBOFLOW_MODEL_ID}")
            self._fetch_model_metrics(requests)
        except ImportError:
            logger.warning("requests no disponible. Usando mock.")
            self.use_mock = True

    def _fetch_model_metrics(self, requests_module=None):
        """Obtiene métricas del modelo desde Roboflow API"""
        try:
            import requests as req
            r = req if requests_module is None else requests_module
            parts = settings.ROBOFLOW_MODEL_ID.split("/")
            project = parts[0]
            version = parts[1] if len(parts) > 1 else "1"

            resp_root = r.get(
                "https://api.roboflow.com",
                params={"api_key": settings.ROBOFLOW_API_KEY},
                timeout=10,
            )
            print(f"[METRICS] Roboflow root: {resp_root.status_code}")
            if not resp_root.ok:
                print(f"[METRICS] Error: {resp_root.text[:200]}")
                return

            root_data = resp_root.json()
            print(f"[METRICS] Root keys: {list(root_data.keys())}")
            ws = root_data.get("workspace")
            print(f"[METRICS] Workspace value: {ws}")

            workspace = None
            if isinstance(ws, dict):
                workspace = ws.get("url") or ws.get("name") or ws.get("id")
            elif isinstance(ws, str):
                workspace = ws

            if not workspace:
                print("[METRICS] No se pudo determinar workspace.")
                return

            url = f"https://api.roboflow.com/{workspace}/{project}/{version}"
            print(f"[METRICS] Fetching: {url}")
            resp = r.get(url, params={"api_key": settings.ROBOFLOW_API_KEY}, timeout=10)
            print(f"[METRICS] Model info response: {resp.status_code}")
            if resp.ok:
                data = resp.json()
                print(f"[METRICS] Version keys: {list(data.get('version', {}).keys())}")
                model_info = data.get("version", {})
                metrics = model_info.get("metrics", {})
                # Métricas en train.results (validación)
                train = model_info.get("train", {})
                results = train.get("results", {})
                eval_results = train.get("modelEvalResults", {})
                # Usar resultados de validación (valid set)
                valid_all = next(
                    (c for c in results.get("class_map", {}).get("valid", []) if c.get("class") == "all"),
                    None
                )
                if valid_all:
                    MLInferenceService.MODEL_PRECISION = float(valid_all.get("precision", 0.0))
                    MLInferenceService.MODEL_RECALL = float(valid_all.get("recall", 0.0))
                    MLInferenceService.MODEL_MAP50 = float(valid_all.get("map50", 0.0))
                elif eval_results:
                    MLInferenceService.MODEL_PRECISION = float(eval_results.get("precision", 0.0))
                    MLInferenceService.MODEL_RECALL = float(eval_results.get("recall", 0.0))
                    MLInferenceService.MODEL_MAP50 = float(eval_results.get("map50", 0.0))
                print(f"[METRICS] P={MLInferenceService.MODEL_PRECISION:.3f} R={MLInferenceService.MODEL_RECALL:.3f} mAP50={MLInferenceService.MODEL_MAP50:.3f}")
            else:
                print(f"[METRICS] Error {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            print(f"[METRICS] Exception: {e}")

    def _map_class(self, class_name: str, index: int):
        key = class_name.lower()
        damage_type = self.CLASS_MAPPING.get(key, DamageType.BACHE)
        class_id = 0 if damage_type == DamageType.BACHE else 1
        return damage_type, class_id

    def _calculate_severity(
        self,
        bounding_boxes: List[BoundingBox],
        image_width: int,
        image_height: int,
        focal_scale_factor: float = 1.0,
    ) -> SeverityLevel:
        if not bounding_boxes:
            return SeverityLevel.BAJA
        image_area = image_width * image_height
        total_damage_area = sum(bb.area() for bb in bounding_boxes)
        damage_ratio = total_damage_area / image_area if image_area > 0 else 0

        # D-08 / normalización por zoom: si la cámara tiene zoom (focal > referencia),
        # el bache aparece más grande en píxeles de lo que es en realidad.
        # focal_scale_factor = focal_referencia / focal_real < 1.0 → reduce el ratio.
        damage_ratio *= focal_scale_factor

        # Detecciones ponderadas por confianza (evita que conf=45% cuente igual que conf=95%)
        weighted_detections = sum(bb.confidence for bb in bounding_boxes)
        if damage_ratio > 0.15 or weighted_detections >= 3.0:
            return SeverityLevel.ALTA
        elif damage_ratio > 0.05 or weighted_detections >= 1.5:
            return SeverityLevel.MEDIA
        else:
            return SeverityLevel.BAJA

    def _mock_detection(self, image_width: int, image_height: int, focal_scale_factor: float = 1.0) -> "DetectionResult":
        import random
        bounding_boxes = []
        for _ in range(random.randint(1, 3)):
            x = random.uniform(0.1, 0.7) * image_width
            y = random.uniform(0.1, 0.7) * image_height
            w = random.uniform(50, 200)
            h = random.uniform(50, 200)
            conf = random.uniform(0.6, 0.95)
            class_id = random.choice([0, 1])
            damage_type = DamageType.BACHE if class_id == 0 else DamageType.GRIETA
            bounding_boxes.append(BoundingBox(
                x=x, y=y, width=w, height=h, confidence=conf,
                class_name=damage_type.value, class_id=class_id,
            ))
        if bounding_boxes:
            best = max(bounding_boxes, key=lambda bb: bb.confidence)
            damage_type = DamageType.BACHE if best.class_id == 0 else DamageType.GRIETA
            confidence = best.confidence
        else:
            damage_type = DamageType.BACHE
            confidence = 0.5
        return DetectionResult(
            damage_type=damage_type,
            severity=self._calculate_severity(bounding_boxes, image_width, image_height, focal_scale_factor),
            confidence=confidence,
            bounding_boxes=bounding_boxes,
            image_width=image_width,
            image_height=image_height,
            model_version="mock-v1.0",
        )

    def _roboflow_detection(self, image_path: str, focal_scale_factor: float = 1.0) -> "DetectionResult":
        import base64, requests

        img = Image.open(image_path)
        image_width, image_height = img.size

        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        url = f"https://serverless.roboflow.com/{settings.ROBOFLOW_MODEL_ID}"
        response = requests.post(
            url,
            params={"api_key": settings.ROBOFLOW_API_KEY},
            data=image_b64,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        logger.info(f"Roboflow response status: {response.status_code}")
        if not response.ok:
            logger.error(f"Roboflow error body: {response.text[:500]}")
        response.raise_for_status()
        data = response.json()
        logger.info(f"Roboflow predictions count: {len(data.get('predictions', []))}")
        if data.get('predictions'):
            logger.info(f"First prediction keys: {list(data['predictions'][0].keys())}")

        predictions = data.get("predictions", [])
        bounding_boxes = []

        for i, pred in enumerate(predictions):
            conf = float(pred.get("confidence", 0))
            if conf < settings.CONFIDENCE_THRESHOLD:
                continue

            class_name = str(pred.get("class", "pothole"))
            cx = float(pred.get("x", 0))
            cy = float(pred.get("y", 0))
            w = float(pred.get("width", 0))
            h = float(pred.get("height", 0))

            # Roboflow centro -> esquina superior izquierda
            x = cx - w / 2
            y = cy - h / 2

            # Polígono de segmentación
            points = pred.get("points", [])

            damage_type, class_id = self._map_class(class_name, i)

            bounding_boxes.append(BoundingBox(
                x=x, y=y, width=w, height=h,
                confidence=conf,
                class_name=damage_type.value,
                class_id=class_id,
                points=points,
            ))

        if bounding_boxes:
            best = max(bounding_boxes, key=lambda bb: bb.confidence)
            dominant_type = DamageType.BACHE if best.class_id == 0 else DamageType.GRIETA
            confidence = best.confidence
        else:
            dominant_type = DamageType.BACHE
            confidence = 0.0

        return DetectionResult(
            damage_type=dominant_type,
            severity=self._calculate_severity(bounding_boxes, image_width, image_height, focal_scale_factor),
            confidence=confidence,
            bounding_boxes=bounding_boxes,
            image_width=image_width,
            image_height=image_height,
            model_version=settings.ROBOFLOW_MODEL_ID,
        )

    def detect(self, image_path: str, focal_scale_factor: float = 1.0) -> "DetectionResult":
        logger.info(f"Ejecutando detección ML en: {image_path}")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

        img = Image.open(image_path)
        image_width, image_height = img.size

        if self.use_mock:
            result = self._mock_detection(image_width, image_height, focal_scale_factor)
        else:
            try:
                result = self._roboflow_detection(image_path, focal_scale_factor)
            except Exception as e:
                logger.error(f"Error en Roboflow API: {e}. Usando mock.")
                result = self._mock_detection(image_width, image_height, focal_scale_factor)

        logger.info(
            f"Detección: {result.damage_type.value} ({result.severity.value}) "
            f"- {len(result.bounding_boxes)} detecciones"
        )
        return result

    def detect_from_bytes(self, image_bytes: bytes) -> "DetectionResult":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        try:
            return self.detect(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def annotate_image(
        self,
        image_path: str,
        result: "DetectionResult",
        output_path: str,
    ) -> str:
        """Dibuja máscaras de segmentación sobre la imagen original"""
        from PIL import ImageDraw, ImageFont

        img = Image.open(image_path).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_img = ImageDraw.Draw(img)

        color_map = {
            "bache":  {"fill": (239, 68, 68, 80),   "outline": (239, 68, 68, 255)},
            "grieta": {"fill": (249, 115, 22, 80),  "outline": (249, 115, 22, 255)},
        }

        try:
            font = ImageFont.truetype("arial.ttf", max(14, img.width // 50))
        except Exception:
            try:
                font = ImageFont.load_default(size=max(14, img.width // 50))
            except Exception:
                font = ImageFont.load_default()

        for bb in result.bounding_boxes:
            colors = color_map.get(bb.class_name, color_map["bache"])
            outline_color = colors["outline"][:3]  # RGB para PIL Draw
            fill_rgba = colors["fill"]

            if bb.points:
                # Dibujar polígono de segmentación
                poly = [(p["x"], p["y"]) for p in bb.points]
                if len(poly) >= 3:
                    draw_overlay.polygon(poly, fill=fill_rgba)
                    draw_img.polygon(poly, outline=outline_color + (255,), width=max(2, img.width // 300))
            else:
                # Fallback a bounding box
                x1, y1 = int(bb.x), int(bb.y)
                x2, y2 = int(bb.x + bb.width), int(bb.y + bb.height)
                draw_overlay.rectangle([x1, y1, x2, y2], fill=fill_rgba)
                draw_img.rectangle([x1, y1, x2, y2], outline=outline_color, width=max(2, img.width // 300))

            # Etiqueta
            label = f"{bb.class_name} {bb.confidence:.0%}"
            lx = int(bb.x)
            ly = int(bb.y) - 20
            if ly < 0:
                ly = int(bb.y) + 4
            try:
                tb = draw_img.textbbox((0, 0), label, font=font)
                tw, th = tb[2] - tb[0], tb[3] - tb[1]
            except Exception:
                tw, th = 80, 16
            draw_img.rectangle([lx, ly, lx + tw + 6, ly + th + 4], fill=outline_color)
            draw_img.text((lx + 3, ly + 2), label, fill="white", font=font)

        # Combinar overlay de máscaras con la imagen
        img = Image.alpha_composite(img, overlay).convert("RGB")

        if not result.bounding_boxes:
            draw_final = ImageDraw.Draw(img)
            draw_final.rectangle([8, 8, 180, 30], fill=(29, 78, 216))
            draw_final.text((12, 10), "Sin detecciones", fill="white", font=font)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, "JPEG", quality=90)
        return output_path


ml_service = MLInferenceService(use_mock=False)


def get_ml_service() -> MLInferenceService:
    return ml_service
