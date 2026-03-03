"""
Servicio de Deduplicación Visual + Geográfica (B-07)

Determina si un nuevo reporte pertenece a un incidente existente combinando:
- Embeddings visuales + índice FAISS para similitud de imágenes
- Distancia geográfica (Haversine) para proximidad espacial
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import pickle
from datetime import datetime, timedelta

import numpy as np
import faiss
from PIL import Image
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_Distance, ST_MakePoint
from sqlalchemy import cast, Float, and_

from models.report import Report, ReportStatus
from core.config import settings

logger = logging.getLogger(__name__)


class VisualEmbedder:
    """
    Generador de embeddings visuales usando ResNet50 pre-entrenado
    """
    
    def __init__(self, model_name: str = "resnet50"):
        """
        Inicializa el modelo de embeddings
        
        Args:
            model_name: Nombre del modelo ('resnet50', 'resnet101', 'mobilenet_v2')
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Inicializando VisualEmbedder con {model_name} en {self.device}")
        
        # Cargar modelo pre-entrenado
        if model_name == "resnet50":
            self.model = models.resnet50(pretrained=True)
            self.embedding_dim = 2048
        elif model_name == "resnet101":
            self.model = models.resnet101(pretrained=True)
            self.embedding_dim = 2048
        elif model_name == "mobilenet_v2":
            self.model = models.mobilenet_v2(pretrained=True)
            self.embedding_dim = 1280
        else:
            raise ValueError(f"Modelo no soportado: {model_name}")
        
        # Remover la última capa (clasificación) para obtener embeddings
        if model_name.startswith("resnet"):
            self.model = torch.nn.Sequential(*list(self.model.children())[:-1])
        else:  # mobilenet
            self.model = torch.nn.Sequential(*list(self.model.children())[:-1])
        
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Transformaciones para normalizar imágenes (ImageNet stats)
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        logger.info(f"Modelo cargado. Dimensión de embeddings: {self.embedding_dim}")
    
    def embed(self, image: Image.Image) -> np.ndarray:
        """
        Genera embedding para una imagen
        
        Args:
            image: Imagen PIL
            
        Returns:
            Vector de embedding (ndarray)
        """
        try:
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Aplicar transformaciones
            img_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Generar embedding
            with torch.no_grad():
                embedding = self.model(img_tensor)
            
            # Aplanar y normalizar
            embedding = embedding.cpu().numpy().flatten()
            embedding = embedding / np.linalg.norm(embedding)  # L2 normalization
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise
    
    def embed_batch(self, images: List[Image.Image]) -> np.ndarray:
        """
        Genera embeddings para un batch de imágenes
        
        Args:
            images: Lista de imágenes PIL
            
        Returns:
            Matriz de embeddings (n_images, embedding_dim)
        """
        try:
            # Preparar batch
            batch_tensors = []
            for image in images:
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                img_tensor = self.transform(image)
                batch_tensors.append(img_tensor)
            
            batch = torch.stack(batch_tensors).to(self.device)
            
            # Generar embeddings
            with torch.no_grad():
                embeddings = self.model(batch)
            
            # Aplanar y normalizar
            embeddings = embeddings.cpu().numpy()
            embeddings = embeddings.reshape(len(images), -1)
            
            # L2 normalization
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / norms
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generando embeddings batch: {e}")
            raise


class FAISSIndex:
    """
    Índice FAISS para búsqueda eficiente de similitud
    """
    
    def __init__(self, embedding_dim: int, index_type: str = "L2"):
        """
        Inicializa el índice FAISS
        
        Args:
            embedding_dim: Dimensión de los embeddings
            index_type: Tipo de índice ('L2', 'IP' para inner product)
        """
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        
        # Crear índice
        if index_type == "L2":
            self.index = faiss.IndexFlatL2(embedding_dim)
        elif index_type == "IP":
            self.index = faiss.IndexFlatIP(embedding_dim)
        else:
            raise ValueError(f"Tipo de índice no soportado: {index_type}")
        
        # Mapeo de índice FAISS a report_id
        self.id_map: List[int] = []
        
        logger.info(f"Índice FAISS creado: {index_type}, dim={embedding_dim}")
    
    def add(self, embeddings: np.ndarray, report_ids: List[int]):
        """
        Añade embeddings al índice
        
        Args:
            embeddings: Matriz de embeddings (n, embedding_dim)
            report_ids: IDs de reportes correspondientes
        """
        if len(embeddings) != len(report_ids):
            raise ValueError("Número de embeddings y report_ids no coincide")
        
        # Asegurar tipo float32
        embeddings = embeddings.astype('float32')
        
        # Añadir al índice
        self.index.add(embeddings)
        self.id_map.extend(report_ids)
        
        logger.info(f"Añadidos {len(embeddings)} embeddings. Total: {self.index.ntotal}")
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        k: int = 10
    ) -> Tuple[np.ndarray, List[int]]:
        """
        Busca los k vecinos más cercanos
        
        Args:
            query_embedding: Embedding de consulta
            k: Número de vecinos a retornar
            
        Returns:
            Tuple (distancias, report_ids)
        """
        if self.index.ntotal == 0:
            return np.array([]), []
        
        # Asegurar dimensiones correctas
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Buscar
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)
        
        # Mapear índices a report_ids
        report_ids = [self.id_map[idx] for idx in indices[0] if idx < len(self.id_map)]
        
        return distances[0], report_ids
    
    def save(self, filepath: str):
        """Guarda el índice en disco"""
        faiss.write_index(self.index, filepath)
        
        # Guardar mapeo de IDs
        id_map_file = filepath + ".ids"
        with open(id_map_file, 'wb') as f:
            pickle.dump(self.id_map, f)
        
        logger.info(f"Índice guardado: {filepath}")
    
    def load(self, filepath: str):
        """Carga el índice desde disco"""
        self.index = faiss.read_index(filepath)
        
        # Cargar mapeo de IDs
        id_map_file = filepath + ".ids"
        with open(id_map_file, 'rb') as f:
            self.id_map = pickle.load(f)
        
        logger.info(f"Índice cargado: {filepath}, {len(self.id_map)} elementos")


def haversine_distance(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float
) -> float:
    """
    Calcula distancia Haversine entre dos puntos (en metros)
    
    Args:
        lat1, lon1: Coordenadas del punto 1
        lat2, lon2: Coordenadas del punto 2
        
    Returns:
        Distancia en metros
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # Radio de la Tierra en metros
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return distance


class DeduplicationService:
    """
    Servicio de Deduplicación que combina similitud visual y distancia geográfica
    """
    
    def __init__(
        self,
        db: Session,
        visual_model: str = "resnet50",
        index_path: Optional[str] = None
    ):
        """
        Inicializa el servicio de deduplicación
        
        Args:
            db: Sesión de base de datos
            visual_model: Modelo para embeddings visuales
            index_path: Ruta al índice FAISS guardado (opcional)
        """
        self.db = db
        
        # Inicializar embedder
        self.embedder = VisualEmbedder(model_name=visual_model)
        
        # Inicializar índice FAISS
        self.index = FAISSIndex(
            embedding_dim=self.embedder.embedding_dim,
            index_type="L2"
        )
        
        # Cargar índice si existe
        if index_path and Path(index_path).exists():
            self.index.load(index_path)
            logger.info(f"Índice FAISS cargado desde {index_path}")
        else:
            logger.info("Índice FAISS nuevo (vacío)")
        
        # Umbrales por defecto (configurables)
        self.VISUAL_SIMILARITY_THRESHOLD = 0.15  # Distancia L2 (menor = más similar)
        self.GEO_DISTANCE_THRESHOLD = 50.0  # metros
        self.TIME_WINDOW_DAYS = 30  # días
    
    def add_report_to_index(self, report: Report, image: Image.Image):
        """
        Añade un reporte al índice de deduplicación
        
        Args:
            report: Reporte a añadir
            image: Imagen del reporte
        """
        try:
            # Generar embedding
            embedding = self.embedder.embed(image)
            
            # Añadir al índice
            self.index.add(
                embeddings=embedding.reshape(1, -1),
                report_ids=[report.id]
            )
            
            logger.info(f"Reporte {report.id} añadido al índice")
            
        except Exception as e:
            logger.error(f"Error añadiendo reporte {report.id} al índice: {e}")
            raise
    
    def find_similar_reports(
        self,
        image: Image.Image,
        latitude: float,
        longitude: float,
        damage_type: str,
        top_k: int = 20
    ) -> List[Tuple[Report, float, float]]:
        """
        Encuentra reportes similares basándose en imagen y ubicación
        
        Args:
            image: Imagen del nuevo reporte
            latitude: Latitud del nuevo reporte
            longitude: Longitud del nuevo reporte
            damage_type: Tipo de daño
            top_k: Número máximo de candidatos a considerar
            
        Returns:
            Lista de tuplas (Report, visual_distance, geo_distance)
        """
        try:
            # 1. Generar embedding para la nueva imagen
            query_embedding = self.embedder.embed(image)
            
            # 2. Buscar top-k vecinos visuales más cercanos
            visual_distances, candidate_ids = self.index.search(query_embedding, k=top_k)
            
            if len(candidate_ids) == 0:
                logger.info("No hay reportes en el índice")
                return []
            
            # 3. Obtener reportes de la BD
            reports = self.db.query(Report).filter(
                Report.id.in_(candidate_ids)
            ).all()
            
            # Crear diccionario para acceso rápido
            reports_dict = {r.id: r for r in reports}
            
            # 4. Calcular distancias geográficas y filtrar
            results = []
            
            for report_id, visual_dist in zip(candidate_ids, visual_distances):
                if report_id not in reports_dict:
                    continue
                
                report = reports_dict[report_id]
                
                # Filtrar por tipo de daño
                if report.damage_type.value != damage_type:
                    continue
                
                # Extraer coordenadas del reporte existente
                # GeoAlchemy2 devuelve datos binarios, necesitamos parsear
                from geoalchemy2.shape import to_shape
                point = to_shape(report.location)
                report_lat = point.y
                report_lon = point.x
                
                # Calcular distancia geográfica
                geo_dist = haversine_distance(
                    latitude, longitude,
                    report_lat, report_lon
                )
                
                results.append((report, float(visual_dist), float(geo_dist)))
            
            # Ordenar por distancia visual (ya viene ordenado, pero por si acaso)
            results.sort(key=lambda x: x[1])
            
            logger.info(f"Encontrados {len(results)} reportes similares")
            return results
            
        except Exception as e:
            logger.error(f"Error buscando reportes similares: {e}")
            raise
    
    def is_duplicate(
        self,
        image: Image.Image,
        latitude: float,
        longitude: float,
        damage_type: str,
        visual_threshold: Optional[float] = None,
        geo_threshold: Optional[float] = None
    ) -> Tuple[bool, Optional[Report], Dict]:
        """
        Determina si un nuevo reporte es duplicado de uno existente
        
        Estrategia:
        - Buscar reportes con alta similitud visual Y proximidad geográfica
        - Combinar ambas métricas con pesos
        
        Args:
            image: Imagen del nuevo reporte
            latitude: Latitud del nuevo reporte
            longitude: Longitud del nuevo reporte
            damage_type: Tipo de daño
            visual_threshold: Umbral de similitud visual (opcional)
            geo_threshold: Umbral de distancia geográfica (opcional)
            
        Returns:
            Tuple (is_duplicate, original_report, metadata)
        """
        # Usar umbrales por defecto si no se especifican
        visual_threshold = visual_threshold or self.VISUAL_SIMILARITY_THRESHOLD
        geo_threshold = geo_threshold or self.GEO_DISTANCE_THRESHOLD
        
        # Buscar reportes similares
        similar_reports = self.find_similar_reports(
            image=image,
            latitude=latitude,
            longitude=longitude,
            damage_type=damage_type,
            top_k=20
        )
        
        if not similar_reports:
            return False, None, {"reason": "no_candidates"}
        
        # Evaluar cada candidato
        for report, visual_dist, geo_dist in similar_reports:
            # Verificar ventana temporal (reportes muy antiguos no se consideran)
            age_days = (datetime.utcnow() - report.created_at).days
            if age_days > self.TIME_WINDOW_DAYS:
                continue
            
            # Verificar umbrales
            is_visually_similar = visual_dist < visual_threshold
            is_geographically_close = geo_dist < geo_threshold
            
            # Lógica de decisión: AMBOS criterios deben cumplirse
            if is_visually_similar and is_geographically_close:
                metadata = {
                    "reason": "duplicate_found",
                    "original_report_id": report.id,
                    "visual_distance": visual_dist,
                    "geo_distance": geo_dist,
                    "age_days": age_days,
                    "visual_threshold": visual_threshold,
                    "geo_threshold": geo_threshold
                }
                
                logger.info(
                    f"Duplicado detectado: "
                    f"report_id={report.id}, "
                    f"visual_dist={visual_dist:.4f}, "
                    f"geo_dist={geo_dist:.1f}m"
                )
                
                return True, report, metadata
        
        # No se encontró duplicado
        best_match = similar_reports[0]
        metadata = {
            "reason": "no_duplicate",
            "closest_report_id": best_match[0].id,
            "visual_distance": best_match[1],
            "geo_distance": best_match[2],
            "visual_threshold": visual_threshold,
            "geo_threshold": geo_threshold
        }
        
        return False, None, metadata
    
    def rebuild_index(self, batch_size: int = 100):
        """
        Reconstruye el índice FAISS desde cero usando todos los reportes aprobados
        
        Útil para:
        - Inicialización
        - Recuperación después de corrupción
        - Cambio de modelo de embeddings
        
        Args:
            batch_size: Tamaño de batch para procesamiento
        """
        logger.info("Iniciando reconstrucción del índice FAISS...")
        
        # Obtener todos los reportes aprobados (que forman parte de incidentes)
        from models.incident import Incident
        
        reports = self.db.query(Report).filter(
            Report.status == ReportStatus.APPROVED
        ).all()
        
        if not reports:
            logger.warning("No hay reportes aprobados para indexar")
            return
        
        logger.info(f"Procesando {len(reports)} reportes...")
        
        # Resetear índice
        self.index = FAISSIndex(
            embedding_dim=self.embedder.embedding_dim,
            index_type="L2"
        )
        
        # Procesar en batches
        for i in range(0, len(reports), batch_size):
            batch = reports[i:i+batch_size]
            
            # Cargar imágenes
            images = []
            report_ids = []
            
            for report in batch:
                try:
                    # Cargar imagen desde MinIO (implementar según tu storage service)
                    # Por ahora, placeholder
                    # image = load_image_from_minio(report.image_url)
                    # images.append(image)
                    # report_ids.append(report.id)
                    pass
                except Exception as e:
                    logger.error(f"Error cargando imagen para report {report.id}: {e}")
            
            if images:
                # Generar embeddings batch
                embeddings = self.embedder.embed_batch(images)
                
                # Añadir al índice
                self.index.add(embeddings, report_ids)
                
                logger.info(f"Procesados {i+len(images)}/{len(reports)} reportes")
        
        logger.info("Índice reconstruido exitosamente")
    
    def save_index(self, filepath: str):
        """Guarda el índice en disco"""
        self.index.save(filepath)
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas del servicio"""
        return {
            "index_size": self.index.index.ntotal,
            "embedding_dim": self.embedder.embedding_dim,
            "visual_threshold": self.VISUAL_SIMILARITY_THRESHOLD,
            "geo_threshold": self.GEO_DISTANCE_THRESHOLD,
            "time_window_days": self.TIME_WINDOW_DAYS
        }


# Instancia global (singleton)
_deduplication_service: Optional[DeduplicationService] = None


def get_deduplication_service(db: Session) -> DeduplicationService:
    """
    Factory para obtener instancia del servicio de deduplicación
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Instancia de DeduplicationService
    """
    global _deduplication_service
    
    if _deduplication_service is None:
        index_path = getattr(settings, 'FAISS_INDEX_PATH', None)
        _deduplication_service = DeduplicationService(
            db=db,
            visual_model="resnet50",
            index_path=index_path
        )
    
    return _deduplication_service
