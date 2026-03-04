"""
Servicio de Inferencia ML - YOLO para detección de daños viales
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import logging

import numpy as np
from PIL import Image

from core.config import settings
from models.report import DamageType, SeverityLevel

logger = logging.getLogger(__name__)


class BoundingBox:
    """Representa un bounding box de detección"""
    
    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        confidence: float,
        class_name: str,
        class_id: int
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence
        self.class_name = class_name
        self.class_id = class_id
    
    def to_dict(self) -> dict:
        """Convierte a diccionario"""
        return {
            "x": float(self.x),
            "y": float(self.y),
            "width": float(self.width),
            "height": float(self.height),
            "confidence": float(self.confidence),
            "class_name": self.class_name,
            "class_id": int(self.class_id),
        }
    
    def area(self) -> float:
        """Calcula el área del bounding box"""
        return self.width * self.height


class DetectionResult:
    """Resultado de detección ML"""
    
    def __init__(
        self,
        damage_type: DamageType,
        severity: SeverityLevel,
        confidence: float,
        bounding_boxes: List[BoundingBox],
        image_width: int,
        image_height: int,
        model_version: str = "mock",
    ):
        self.damage_type = damage_type
        self.severity = severity
        self.confidence = confidence
        self.bounding_boxes = bounding_boxes
        self.image_width = image_width
        self.image_height = image_height
        self.model_version = model_version
    
    def to_dict(self) -> dict:
        """Convierte a diccionario serializable"""
        return {
            "damage_type": self.damage_type.value,
            "severity": self.severity.value,
            "confidence": float(self.confidence),
            "bounding_boxes": [bb.to_dict() for bb in self.bounding_boxes],
            "image_width": self.image_width,
            "image_height": self.image_height,
            "model_version": self.model_version,
            "num_detections": len(self.bounding_boxes),
        }
    
    def to_json(self) -> str:
        """Serializa a JSON string"""
        return json.dumps(self.to_dict())


class MLInferenceService:
    """
    Servicio de inferencia ML para detección de daños viales
    
    Usa YOLOv8 para detectar y clasificar baches/grietas.
    Si el modelo no está disponible, usa detección mock.
    """
    
    def __init__(self, model_path: Optional[str] = None, use_mock: bool = False):
        """
        Inicializa el servicio de inferencia
        
        Args:
            model_path: Ruta al modelo YOLO (.pt o .onnx)
            use_mock: Si True, usa detección simulada en lugar de modelo real
        """
        self.model_path = model_path or settings.YOLO_MODEL_PATH
        self.use_mock = use_mock
        self.model = None
        self.model_loaded = False
        
        # Mapeo de clases YOLO a DamageType
        self.class_mapping = {
            0: DamageType.BACHE,
            1: DamageType.GRIETA,
            # Agregar más clases según el modelo entrenado
        }
        
        if not use_mock:
            self._load_model()
    
    def _load_model(self):
        """Carga el modelo YOLO"""
        try:
            from ultralytics import YOLO
            
            if not os.path.exists(self.model_path):
                logger.warning(
                    f" Modelo YOLO no encontrado en {self.model_path}. "
                    f"Usando detección mock."
                )
                self.use_mock = True
                return
            
            logger.info(f" Cargando modelo YOLO desde {self.model_path}...")
            self.model = YOLO(self.model_path)
            self.model_loaded = True
            logger.info(" Modelo YOLO cargado exitosamente")
            
        except ImportError:
            logger.warning(
                " Ultralytics no disponible. Usando detección mock."
            )
            self.use_mock = True
        except Exception as e:
            logger.error(f" Error cargando modelo YOLO: {e}")
            self.use_mock = True
    
    def _mock_detection(
        self,
        image_width: int,
        image_height: int
    ) -> DetectionResult:
        """
        Genera detección simulada para testing
        
        Args:
            image_width: Ancho de la imagen
            image_height: Alto de la imagen
        
        Returns:
            DetectionResult con detecciones simuladas
        """
        import random
        
        # Simular 1-3 detecciones
        num_detections = random.randint(1, 3)
        bounding_boxes = []
        
        for _ in range(num_detections):
            # Generar bounding box aleatorio
            x = random.uniform(0.1, 0.7) * image_width
            y = random.uniform(0.1, 0.7) * image_height
            w = random.uniform(50, 200)
            h = random.uniform(50, 200)
            conf = random.uniform(0.6, 0.95)
            class_id = random.choice([0, 1])
            
            bbox = BoundingBox(
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=conf,
                class_name=self.class_mapping[class_id].value,
                class_id=class_id
            )
            bounding_boxes.append(bbox)
        
        # Determinar tipo de daño dominante
        if bounding_boxes:
            # Usar la detección con mayor confianza
            best_bbox = max(bounding_boxes, key=lambda bb: bb.confidence)
            damage_type = self.class_mapping[best_bbox.class_id]
            confidence = best_bbox.confidence
        else:
            damage_type = random.choice([DamageType.BACHE, DamageType.GRIETA])
            confidence = random.uniform(0.5, 0.8)
        
        # Calcular severidad basada en tamaño de detecciones
        severity = self._calculate_severity(bounding_boxes, image_width, image_height)
        
        return DetectionResult(
            damage_type=damage_type,
            severity=severity,
            confidence=confidence,
            bounding_boxes=bounding_boxes,
            image_width=image_width,
            image_height=image_height,
            model_version="mock-v1.0"
        )
    
    def _calculate_severity(
        self,
        bounding_boxes: List[BoundingBox],
        image_width: int,
        image_height: int
    ) -> SeverityLevel:
        """
        Calcula severidad basada en tamaño y cantidad de detecciones
        
        Args:
            bounding_boxes: Lista de detecciones
            image_width: Ancho de la imagen
            image_height: Alto de la imagen
        
        Returns:
            SeverityLevel (BAJA, MEDIA, ALTA)
        """
        if not bounding_boxes:
            return SeverityLevel.BAJA
        
        image_area = image_width * image_height
        
        # Calcular área total de daños
        total_damage_area = sum(bb.area() for bb in bounding_boxes)
        damage_ratio = total_damage_area / image_area
        
        # Considerar también la cantidad de detecciones
        num_detections = len(bounding_boxes)
        
        # Criterios de severidad
        if damage_ratio > 0.15 or num_detections >= 4:
            return SeverityLevel.ALTA
        elif damage_ratio > 0.05 or num_detections >= 2:
            return SeverityLevel.MEDIA
        else:
            return SeverityLevel.BAJA
    
    def _yolo_detection(
        self,
        image_path: str
    ) -> DetectionResult:
        """
        Ejecuta detección con modelo YOLO real
        
        Args:
            image_path: Ruta a la imagen
        
        Returns:
            DetectionResult con detecciones del modelo
        """
        if not self.model_loaded:
            raise RuntimeError("Modelo YOLO no cargado")
        
        # Ejecutar inferencia
        results = self.model.predict(
            source=image_path,
            conf=settings.CONFIDENCE_THRESHOLD,
            iou=settings.IOU_THRESHOLD,
            verbose=False
        )
        
        # Procesar resultados
        result = results[0]
        boxes = result.boxes
        
        # Obtener dimensiones de la imagen
        img = Image.open(image_path)
        image_width, image_height = img.size
        
        # Convertir detecciones a BoundingBox
        bounding_boxes = []
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            
            # Convertir formato (x1,y1,x2,y2) -> (x,y,w,h)
            x = float(x1)
            y = float(y1)
            width = float(x2 - x1)
            height = float(y2 - y1)
            
            # Mapear clase
            damage_type = self.class_mapping.get(class_id, DamageType.BACHE)
            
            bbox = BoundingBox(
                x=x,
                y=y,
                width=width,
                height=height,
                confidence=conf,
                class_name=damage_type.value,
                class_id=class_id
            )
            bounding_boxes.append(bbox)
        
        # Determinar tipo de daño y confianza
        if bounding_boxes:
            best_bbox = max(bounding_boxes, key=lambda bb: bb.confidence)
            damage_type = self.class_mapping.get(best_bbox.class_id, DamageType.BACHE)
            confidence = best_bbox.confidence
        else:
            # Sin detecciones - asumir bache con baja confianza
            damage_type = DamageType.BACHE
            confidence = 0.3
        
        # Calcular severidad
        severity = self._calculate_severity(bounding_boxes, image_width, image_height)
        
        return DetectionResult(
            damage_type=damage_type,
            severity=severity,
            confidence=confidence,
            bounding_boxes=bounding_boxes,
            image_width=image_width,
            image_height=image_height,
            model_version=f"yolov8-{Path(self.model_path).stem}"
        )
    
    def detect(self, image_path: str) -> DetectionResult:
        """
        Ejecuta detección en una imagen
        
        Args:
            image_path: Ruta a la imagen (local o URL)
        
        Returns:
            DetectionResult con detecciones y clasificación
        """
        logger.info(f" Ejecutando detección ML en: {image_path}")
        
        # Verificar que la imagen existe
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Imagen no encontrada: {image_path}")
        
        # Obtener dimensiones
        img = Image.open(image_path)
        image_width, image_height = img.size
        
        # Ejecutar detección (mock o real)
        if self.use_mock:
            logger.info(" Usando detección MOCK")
            result = self._mock_detection(image_width, image_height)
        else:
            logger.info(" Usando modelo YOLO")
            result = self._yolo_detection(image_path)
        
        logger.info(
            f" Detección completada: {result.damage_type.value} "
            f"({result.severity.value}) - {len(result.bounding_boxes)} detecciones"
        )
        
        return result
    
    def detect_from_bytes(self, image_bytes: bytes) -> DetectionResult:
        """
        Ejecuta detección desde bytes de imagen
        
        Args:
            image_bytes: Bytes de la imagen
        
        Returns:
            DetectionResult con detecciones
        """
        import tempfile
        
        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name
        
        try:
            result = self.detect(tmp_path)
            return result
        finally:
            # Limpiar archivo temporal
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# Instancia global del servicio de inferencia
# Por defecto usa mock, se puede reconfigurar para usar modelo real
ml_service = MLInferenceService(use_mock=True)


def get_ml_service() -> MLInferenceService:
    """
    Obtiene la instancia del servicio de inferencia ML
    
    Returns:
        MLInferenceService singleton
    """
    return ml_service
