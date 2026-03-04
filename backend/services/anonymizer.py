"""
Servicio de anonimización de imágenes - Blur de rostros y placas

Implementa B-05: Middleware para difuminar rostros y placas antes de persistir.
"""

import io
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional
from PIL import Image
from dataclasses import dataclass


@dataclass
class BlurRegion:
    """Región detectada para aplicar blur"""
    x: int
    y: int
    w: int
    h: int
    type: str  # 'face' o 'plate'
    confidence: float = 1.0


class ImageAnonymizer:
    """
    Servicio para anonimizar imágenes detectando y difuminando rostros y placas.
    
    Features:
    - Detección de rostros (OpenCV Haar Cascade)
    - Detección básica de placas (por color y forma)
    - Blur gaussiano de alta intensidad
    - Preservación de calidad de imagen
    """
    
    def __init__(self):
        """Inicializa detectores de rostros y placas"""
        self.face_cascade = None
        self.plate_cascade = None
        self._load_face_detector()
        self._load_plate_detector()
    
    def _load_face_detector(self):
        """Carga el clasificador Haar Cascade para detección de rostros"""
        try:
            # Intentar cargar desde OpenCV data
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                print("  No se pudo cargar el detector de rostros Haar Cascade")
                self.face_cascade = None
            else:
                print(" Detector de rostros cargado correctamente")
        except Exception as e:
            print(f"  Error cargando detector de rostros: {e}")
            self.face_cascade = None
    
    def _load_plate_detector(self):
        """
        Carga detector de placas (simplificado)
        
        Nota: Para detección robusta de placas, se requeriría un modelo YOLO
        o similar entrenado específicamente. Esta implementación usa
        características básicas de color y forma.
        """
        try:
            # Intentar cargar Haar Cascade para placas rusas (más genérico)
            cascade_path = cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
            self.plate_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.plate_cascade.empty():
                print("ℹ  Detector de placas Haar no disponible (usar método alternativo)")
                self.plate_cascade = None
            else:
                print(" Detector de placas cargado correctamente")
        except Exception as e:
            print(f"ℹ  Detector de placas no disponible: {e}")
            self.plate_cascade = None
    
    def detect_faces(self, image: np.ndarray) -> List[BlurRegion]:
        """
        Detecta rostros en la imagen usando Haar Cascade
        
        Args:
            image: Imagen en formato numpy array (BGR)
        
        Returns:
            Lista de regiones detectadas (rostros)
        """
        if self.face_cascade is None:
            return []
        
        regions = []
        
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detectar rostros
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Crear regiones con margen adicional
            for (x, y, w, h) in faces:
                # Expandir región en 20% para asegurar cobertura completa
                margin_w = int(w * 0.2)
                margin_h = int(h * 0.2)
                
                new_x = max(0, x - margin_w)
                new_y = max(0, y - margin_h)
                new_w = min(image.shape[1] - new_x, w + 2 * margin_w)
                new_h = min(image.shape[0] - new_y, h + 2 * margin_h)
                
                regions.append(BlurRegion(
                    x=new_x,
                    y=new_y,
                    w=new_w,
                    h=new_h,
                    type='face',
                    confidence=1.0
                ))
        
        except Exception as e:
            print(f"  Error detectando rostros: {e}")
        
        return regions
    
    def detect_plates_basic(self, image: np.ndarray) -> List[BlurRegion]:
        """
        Detecta placas vehiculares usando método básico de visión por computadora
        
        Estrategia:
        1. Buscar regiones rectangulares con alta relación ancho/alto
        2. Filtrar por color (blanco, amarillo, azul típicos de placas)
        3. Detectar contornos rectangulares
        
        Args:
            image: Imagen en formato numpy array (BGR)
        
        Returns:
            Lista de regiones detectadas (placas)
        """
        regions = []
        
        try:
            # Convertir a HSV para mejor detección de color
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Definir rangos de color para placas (blanco, amarillo, azul claro)
            # Blanco
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 30, 255])
            mask_white = cv2.inRange(hsv, lower_white, upper_white)
            
            # Amarillo
            lower_yellow = np.array([20, 100, 100])
            upper_yellow = np.array([30, 255, 255])
            mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
            
            # Azul claro
            lower_blue = np.array([90, 50, 50])
            upper_blue = np.array([130, 255, 255])
            mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
            
            # Combinar máscaras
            mask = cv2.bitwise_or(mask_white, mask_yellow)
            mask = cv2.bitwise_or(mask, mask_blue)
            
            # Aplicar operaciones morfológicas para limpiar
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Obtener bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filtrar por tamaño y relación de aspecto (placas típicas)
                aspect_ratio = w / float(h) if h > 0 else 0
                area = w * h
                
                # Las placas suelen tener aspect ratio entre 2:1 y 5:1
                # y un área mínima de unos 2000 píxeles
                if 2.0 <= aspect_ratio <= 5.0 and area >= 2000:
                    # Expandir región ligeramente
                    margin = int(min(w, h) * 0.1)
                    new_x = max(0, x - margin)
                    new_y = max(0, y - margin)
                    new_w = min(image.shape[1] - new_x, w + 2 * margin)
                    new_h = min(image.shape[0] - new_y, h + 2 * margin)
                    
                    regions.append(BlurRegion(
                        x=new_x,
                        y=new_y,
                        w=new_w,
                        h=new_h,
                        type='plate',
                        confidence=0.7  # Confianza media para método básico
                    ))
        
        except Exception as e:
            print(f"  Error detectando placas: {e}")
        
        return regions
    
    def detect_plates_cascade(self, image: np.ndarray) -> List[BlurRegion]:
        """
        Detecta placas usando Haar Cascade (si está disponible)
        
        Args:
            image: Imagen en formato numpy array (BGR)
        
        Returns:
            Lista de regiones detectadas (placas)
        """
        if self.plate_cascade is None:
            return []
        
        regions = []
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            plates = self.plate_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(50, 20)
            )
            
            for (x, y, w, h) in plates:
                # Expandir región ligeramente
                margin = int(min(w, h) * 0.15)
                new_x = max(0, x - margin)
                new_y = max(0, y - margin)
                new_w = min(image.shape[1] - new_x, w + 2 * margin)
                new_h = min(image.shape[0] - new_y, h + 2 * margin)
                
                regions.append(BlurRegion(
                    x=new_x,
                    y=new_y,
                    w=new_w,
                    h=new_h,
                    type='plate',
                    confidence=1.0
                ))
        
        except Exception as e:
            print(f"  Error detectando placas con cascade: {e}")
        
        return regions
    
    def apply_blur(self, image: np.ndarray, regions: List[BlurRegion]) -> Tuple[np.ndarray, int]:
        """
        Aplica blur gaussiano a las regiones detectadas
        
        Args:
            image: Imagen original (numpy array BGR)
            regions: Lista de regiones a difuminar
        
        Returns:
            Tuple(imagen procesada, número de regiones difuminadas)
        """
        if not regions:
            return image, 0
        
        # Crear copia de la imagen
        blurred_image = image.copy()
        
        blur_count = 0
        
        for region in regions:
            try:
                # Extraer región
                x, y, w, h = region.x, region.y, region.w, region.h
                
                # Validar límites
                if x < 0 or y < 0 or x + w > image.shape[1] or y + h > image.shape[0]:
                    continue
                
                roi = blurred_image[y:y+h, x:x+w]
                
                # Aplicar blur gaussiano intenso
                # Kernel size debe ser impar y grande para blur efectivo
                kernel_size = max(51, min(w, h) // 3)
                if kernel_size % 2 == 0:
                    kernel_size += 1
                
                blurred_roi = cv2.GaussianBlur(roi, (kernel_size, kernel_size), 30)
                
                # Reemplazar región en imagen
                blurred_image[y:y+h, x:x+w] = blurred_roi
                
                blur_count += 1
            
            except Exception as e:
                print(f"  Error aplicando blur a región {region.type}: {e}")
        
        return blurred_image, blur_count
    
    def anonymize(
        self,
        image_bytes: bytes,
        detect_faces: bool = True,
        detect_plates: bool = True
    ) -> Tuple[bytes, dict]:
        """
        Anonimiza una imagen detectando y difuminando rostros y placas
        
        Args:
            image_bytes: Bytes de la imagen original
            detect_faces: Si True, detecta y difumina rostros
            detect_plates: Si True, detecta y difumina placas
        
        Returns:
            Tuple(bytes de imagen anonimizada, estadísticas)
        """
        stats = {
            'faces_detected': 0,
            'plates_detected': 0,
            'regions_blurred': 0,
            'anonymized': False,
            'error': None
        }
        
        try:
            # Convertir bytes a imagen PIL
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Convertir a numpy array (BGR para OpenCV)
            image_np = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            all_regions = []
            
            # Detectar rostros
            if detect_faces:
                face_regions = self.detect_faces(image_np)
                stats['faces_detected'] = len(face_regions)
                all_regions.extend(face_regions)
            
            # Detectar placas (intentar ambos métodos)
            if detect_plates:
                plate_regions = self.detect_plates_cascade(image_np)
                
                # Si el cascade no encontró nada, usar método básico
                if not plate_regions:
                    plate_regions = self.detect_plates_basic(image_np)
                
                stats['plates_detected'] = len(plate_regions)
                all_regions.extend(plate_regions)
            
            # Aplicar blur a todas las regiones
            blurred_image, blur_count = self.apply_blur(image_np, all_regions)
            stats['regions_blurred'] = blur_count
            stats['anonymized'] = blur_count > 0
            
            # Convertir de vuelta a PIL
            blurred_pil = Image.fromarray(cv2.cvtColor(blurred_image, cv2.COLOR_BGR2RGB))
            
            # Convertir a bytes
            output = io.BytesIO()
            
            # Mantener formato original si es posible
            format = pil_image.format or 'JPEG'
            save_kwargs = {'format': format}
            
            if format in ['JPEG', 'JPG']:
                save_kwargs['quality'] = 95
                save_kwargs['optimize'] = True
            
            blurred_pil.save(output, **save_kwargs)
            
            return output.getvalue(), stats
        
        except Exception as e:
            stats['error'] = str(e)
            print(f" Error anonimizando imagen: {e}")
            # En caso de error, retornar imagen original (política conservadora)
            # NOTA: En producción estricta, podría bloquear el guardado
            return image_bytes, stats


# Instancia global del servicio
image_anonymizer = ImageAnonymizer()
