"""
Servicio de Deduplicación Visual + Geográfica (B-07, M-11)

Implementa deduplicación multimodal con:
- Embeddings visuales reales (ResNet / CLIP) con fallback controlado
- Índices FAISS por modelo
- Score fusionado (visual + geo + texto)
"""

from __future__ import annotations

import io
import logging
import math
import pickle
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import cv2
import faiss
import numpy as np
import requests
from PIL import Image
from sqlalchemy.orm import Session

from core.config import settings
from models.report import Report, ReportStatus

logger = logging.getLogger(__name__)


def _safe_div(num: float, den: float) -> float:
    if den == 0:
        return 0.0
    return num / den


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    vec = vec.astype("float32")
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec = vec / norm
    return vec


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = _l2_normalize(a)
    b = _l2_normalize(b)
    return float(np.dot(a, b))


def _text_similarity(a: Optional[str], b: Optional[str]) -> float:
    if not a or not b:
        return 0.0
    from difflib import SequenceMatcher

    return float(SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio())


def _model_alias(name: str) -> str:
    n = (name or "").strip().lower()
    aliases = {
        "resnet": "resnet50",
        "resnet50": "resnet50",
        "resnet101": "resnet101",
        "mobilenet": "mobilenet_v2",
        "mobilenet_v2": "mobilenet_v2",
        "clip": "clip-vit-base-patch32",
        "clip-vit-base-patch32": "clip-vit-base-patch32",
        "hist": "histogram",
        "histogram": "histogram",
    }
    if n not in aliases:
        raise ValueError(f"Modelo visual no soportado: {name}")
    return aliases[n]


@dataclass
class CandidateScore:
    report: Report
    visual_distance: float
    geo_distance: float
    fused_score: float
    visual_similarity: float
    geo_similarity: float
    text_similarity: float
    model_distances: Dict[str, float]
    model_similarities: Dict[str, float]
    age_days: int


class VisualEmbedder:
    """
    Generador de embeddings visuales con soporte real para:
    - ResNet50 / ResNet101 / MobileNetV2 (torchvision)
    - CLIP ViT-B/32 (transformers)

    Si faltan dependencias y el fallback está habilitado, usa histograma de color.
    """

    HISTOGRAM_DIM = 192

    def __init__(self, model_name: str = "resnet50", allow_histogram_fallback: bool = True):
        self.original_model_name = model_name
        self.model_name = _model_alias(model_name)
        self.allow_histogram_fallback = allow_histogram_fallback

        self.backend = "histogram"
        self.embedding_dim = self.HISTOGRAM_DIM
        self.device = "cpu"

        self._torch = None
        self._model = None
        self._preprocess = None
        self._clip_processor = None

        self._init_backend()

    def _init_backend(self):
        if self.model_name in {"resnet50", "resnet101", "mobilenet_v2"}:
            self._init_torchvision_backend()
            return

        if self.model_name == "clip-vit-base-patch32":
            self._init_clip_backend()
            return

        # Explicit histogram mode
        self.backend = "histogram"
        self.embedding_dim = self.HISTOGRAM_DIM
        self.device = "cpu"
        logger.info("VisualEmbedder inicializado en modo histogram")

    def _fallback_to_histogram(self, reason: str):
        if not self.allow_histogram_fallback:
            raise RuntimeError(reason)

        self.backend = "histogram"
        self.embedding_dim = self.HISTOGRAM_DIM
        self.device = "cpu"
        logger.warning(
            "No fue posible inicializar %s (%s). Se usará fallback histogram.",
            self.model_name,
            reason,
        )

    def _init_torchvision_backend(self):
        try:
            import torch
            import torchvision.models as models
            import torchvision.transforms as transforms

            self._torch = torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

            if self.model_name == "resnet50":
                weights = models.ResNet50_Weights.IMAGENET1K_V2
                base_model = models.resnet50(weights=weights)
                self.embedding_dim = 2048
                self._preprocess = weights.transforms()
                self._model = torch.nn.Sequential(*list(base_model.children())[:-1])
            elif self.model_name == "resnet101":
                weights = models.ResNet101_Weights.IMAGENET1K_V2
                base_model = models.resnet101(weights=weights)
                self.embedding_dim = 2048
                self._preprocess = weights.transforms()
                self._model = torch.nn.Sequential(*list(base_model.children())[:-1])
            else:
                weights = models.MobileNet_V2_Weights.IMAGENET1K_V2
                base_model = models.mobilenet_v2(weights=weights)
                self.embedding_dim = 1280
                self._preprocess = weights.transforms()
                self._model = base_model.features

            self._model.eval().to(self.device)
            self.backend = "torchvision"
            logger.info(
                "VisualEmbedder inicializado: model=%s backend=%s device=%s dim=%s",
                self.model_name,
                self.backend,
                self.device,
                self.embedding_dim,
            )
        except Exception as exc:
            self._fallback_to_histogram(str(exc))

    def _init_clip_backend(self):
        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor

            self._torch = torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

            model_id = "openai/clip-vit-base-patch32"
            self._model = CLIPModel.from_pretrained(model_id)
            self._clip_processor = CLIPProcessor.from_pretrained(model_id)
            self._model.eval().to(self.device)

            self.embedding_dim = int(self._model.config.projection_dim)
            self.backend = "clip"
            logger.info(
                "VisualEmbedder inicializado: model=%s backend=%s device=%s dim=%s",
                self.model_name,
                self.backend,
                self.device,
                self.embedding_dim,
            )
        except Exception as exc:
            self._fallback_to_histogram(str(exc))

    def _compute_histogram(self, image: Image.Image) -> np.ndarray:
        if image.mode != "RGB":
            image = image.convert("RGB")

        img = cv2.cvtColor(np.array(image.resize((224, 224))), cv2.COLOR_RGB2BGR)
        hist_parts: List[np.ndarray] = []
        for ch in range(3):
            h = cv2.calcHist([img], [ch], None, [64], [0, 256]).flatten()
            hist_parts.append(h)

        return _l2_normalize(np.concatenate(hist_parts).astype("float32"))

    def _compute_torchvision(self, image: Image.Image) -> np.ndarray:
        if image.mode != "RGB":
            image = image.convert("RGB")

        torch = self._torch
        assert torch is not None and self._model is not None and self._preprocess is not None

        tensor = self._preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            features = self._model(tensor)
            if features.ndim == 4:
                features = torch.nn.functional.adaptive_avg_pool2d(features, (1, 1))
            features = features.view(features.size(0), -1)

        return _l2_normalize(features[0].detach().cpu().numpy())

    def _compute_clip(self, image: Image.Image) -> np.ndarray:
        if image.mode != "RGB":
            image = image.convert("RGB")

        torch = self._torch
        assert torch is not None and self._model is not None and self._clip_processor is not None

        inputs = self._clip_processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            features = self._model.get_image_features(**inputs)

        return _l2_normalize(features[0].detach().cpu().numpy())

    def embed(self, image: Image.Image) -> np.ndarray:
        try:
            if self.backend == "torchvision":
                return self._compute_torchvision(image)
            if self.backend == "clip":
                return self._compute_clip(image)
            return self._compute_histogram(image)
        except Exception as exc:
            logger.error("Error generando embedding con %s: %s", self.model_name, exc)
            if self.backend != "histogram" and self.allow_histogram_fallback:
                return self._compute_histogram(image)
            raise

    def embed_batch(self, images: Sequence[Image.Image]) -> np.ndarray:
        if not images:
            return np.zeros((0, self.embedding_dim), dtype="float32")

        # Se mantiene robusto por compatibilidad y simplicidad.
        return np.stack([self.embed(img) for img in images]).astype("float32")


class FAISSIndex:
    """Índice FAISS para búsqueda eficiente de similitud."""

    def __init__(self, embedding_dim: int, index_type: str = "L2"):
        self.embedding_dim = embedding_dim
        self.index_type = index_type

        if index_type == "L2":
            self.index = faiss.IndexFlatL2(embedding_dim)
        elif index_type == "IP":
            self.index = faiss.IndexFlatIP(embedding_dim)
        else:
            raise ValueError(f"Tipo de índice no soportado: {index_type}")

        self.id_map: List[int] = []

    def clear(self):
        if self.index_type == "L2":
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        else:
            self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.id_map = []

    def add(self, embeddings: np.ndarray, report_ids: Sequence[int]):
        if len(embeddings) != len(report_ids):
            raise ValueError("Número de embeddings y report_ids no coincide")

        self.index.add(embeddings.astype("float32"))
        self.id_map.extend([int(rid) for rid in report_ids])

    def search(self, query_embedding: np.ndarray, k: int = 10) -> Tuple[np.ndarray, List[int]]:
        if self.index.ntotal == 0:
            return np.array([]), []

        query = query_embedding.reshape(1, -1).astype("float32")
        k = min(max(k, 1), self.index.ntotal)
        distances, indices = self.index.search(query, k)

        report_ids = [self.id_map[idx] for idx in indices[0] if 0 <= idx < len(self.id_map)]
        return distances[0], report_ids

    def save(self, filepath: str):
        faiss.write_index(self.index, filepath)
        with open(filepath + ".ids", "wb") as f:
            pickle.dump(self.id_map, f)

    def load(self, filepath: str):
        self.index = faiss.read_index(filepath)
        with open(filepath + ".ids", "rb") as f:
            self.id_map = pickle.load(f)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia Haversine entre dos puntos (en metros)."""
    from math import atan2, cos, radians, sin, sqrt

    r = 6371000
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


class DeduplicationService:
    """Servicio de deduplicación multimodelo con score fusionado."""

    def __init__(
        self,
        db: Session,
        visual_model: str = "resnet50",
        secondary_visual_model: Optional[str] = None,
        index_path: Optional[str] = None,
    ):
        self.db = db

        self.index_base_path = index_path or getattr(settings, "FAISS_INDEX_PATH", "storage/faiss_index.bin")
        self.primary_model = _model_alias(visual_model)
        self.secondary_model = _model_alias(secondary_visual_model) if secondary_visual_model else None

        model_order = [self.primary_model]
        if self.secondary_model and self.secondary_model != self.primary_model:
            model_order.append(self.secondary_model)
        self.models = model_order

        allow_fallback = bool(getattr(settings, "DEDUPLICATION_ALLOW_HISTOGRAM_FALLBACK", True))

        self.embedders: Dict[str, VisualEmbedder] = {
            model: VisualEmbedder(model_name=model, allow_histogram_fallback=allow_fallback)
            for model in self.models
        }
        self.indexes: Dict[str, FAISSIndex] = {
            model: FAISSIndex(embedding_dim=embedder.embedding_dim, index_type="L2")
            for model, embedder in self.embedders.items()
        }

        self.VISUAL_SIMILARITY_THRESHOLD = float(getattr(settings, "VISUAL_SIMILARITY_THRESHOLD", 0.15))
        self.GEO_DISTANCE_THRESHOLD = float(getattr(settings, "GEO_DISTANCE_THRESHOLD", 50.0))
        self.TIME_WINDOW_DAYS = int(getattr(settings, "DEDUP_TIME_WINDOW_DAYS", 30))

        self.FUSION_SCORE_THRESHOLD = float(getattr(settings, "DEDUPLICATION_SCORE_THRESHOLD", 0.72))
        self.W_VISUAL_PRIMARY = float(getattr(settings, "DEDUPLICATION_VISUAL_WEIGHT_PRIMARY", 0.45))
        self.W_VISUAL_SECONDARY = float(getattr(settings, "DEDUPLICATION_VISUAL_WEIGHT_SECONDARY", 0.25))
        self.W_GEO = float(getattr(settings, "DEDUPLICATION_GEO_WEIGHT", 0.20))
        self.W_TEXT = float(getattr(settings, "DEDUPLICATION_TEXT_WEIGHT", 0.10))

        self._load_existing_indexes()

    def _model_index_path(self, model_name: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9]+", "_", model_name.lower()).strip("_")
        base = Path(self.index_base_path)

        if base.suffix:
            root = base.with_suffix("")
            return str(root) + f"_{safe}.faiss"

        return str(base) + f"_{safe}.faiss"

    def _load_existing_indexes(self):
        for model_name, index in self.indexes.items():
            path = self._model_index_path(model_name)
            if Path(path).exists() and Path(path + ".ids").exists():
                try:
                    index.load(path)
                    logger.info("Índice cargado para %s desde %s", model_name, path)
                except Exception as exc:
                    logger.warning("No se pudo cargar índice %s: %s", path, exc)

    def _distance_to_similarity(self, distance_l2: float) -> float:
        # Con embeddings normalizados, L2 en [0, 2].
        return max(0.0, 1.0 - (float(distance_l2) / 2.0))

    def _geo_similarity(self, geo_distance_m: float, geo_threshold_m: float) -> float:
        scale = max(geo_threshold_m, 1.0)
        return float(math.exp(-float(geo_distance_m) / scale))

    def _fusion_score(
        self,
        model_similarities: Dict[str, float],
        geo_similarity: float,
        text_similarity: float,
    ) -> float:
        primary_sim = model_similarities.get(self.primary_model, 0.0)
        secondary_sim = 0.0
        if self.secondary_model:
            secondary_sim = model_similarities.get(self.secondary_model, 0.0)

        w_total = self.W_VISUAL_PRIMARY + self.W_VISUAL_SECONDARY + self.W_GEO + self.W_TEXT
        if w_total <= 0:
            w_total = 1.0

        fused = (
            self.W_VISUAL_PRIMARY * primary_sim
            + self.W_VISUAL_SECONDARY * secondary_sim
            + self.W_GEO * geo_similarity
            + self.W_TEXT * text_similarity
        ) / w_total

        return float(max(0.0, min(1.0, fused)))

    def _load_report_image(self, image_url: str) -> Optional[Image.Image]:
        if not image_url:
            return None

        # Local storage fallback (dev)
        if image_url.startswith("/storage/images/"):
            rel = image_url.replace("/storage/images/", "")
            backend_dir = Path(__file__).resolve().parent.parent
            file_path = backend_dir / "storage" / "images" / rel
            if file_path.exists():
                return Image.open(file_path).convert("RGB")
            return None

        # MinIO/object URL
        if image_url.startswith("http://") or image_url.startswith("https://"):
            try:
                if settings.MINIO_ENDPOINT in image_url:
                    from minio import Minio

                    mc = Minio(
                        settings.MINIO_ENDPOINT,
                        access_key=settings.MINIO_ACCESS_KEY,
                        secret_key=settings.MINIO_SECRET_KEY,
                        secure=settings.MINIO_SECURE,
                    )
                    url_path = image_url.split(settings.MINIO_ENDPOINT)[-1].lstrip("/")
                    bucket = url_path.split("/")[0]
                    object_key = "/".join(url_path.split("/")[1:])

                    response = mc.get_object(bucket, object_key)
                    try:
                        raw = response.read()
                    finally:
                        response.close()
                        response.release_conn()
                    return Image.open(io.BytesIO(raw)).convert("RGB")

                resp = requests.get(image_url, timeout=15)
                resp.raise_for_status()
                return Image.open(io.BytesIO(resp.content)).convert("RGB")
            except Exception as exc:
                logger.warning("No se pudo cargar imagen %s: %s", image_url, exc)
                return None

        return None

    def add_report_to_index(self, report: Report, image: Image.Image, description: Optional[str] = None):
        if report is None or image is None:
            return

        for model_name, embedder in self.embedders.items():
            embedding = embedder.embed(image)
            self.indexes[model_name].add(embeddings=embedding.reshape(1, -1), report_ids=[report.id])

        logger.info("Reporte %s añadido a índice dedup (modelos=%s)", report.id, ", ".join(self.models))

    def _query_embeddings(self, image: Image.Image) -> Dict[str, np.ndarray]:
        return {model_name: embedder.embed(image) for model_name, embedder in self.embedders.items()}

    def _candidate_distances(self, query_embeddings: Dict[str, np.ndarray], top_k: int) -> Dict[int, Dict[str, float]]:
        candidates: Dict[int, Dict[str, float]] = {}

        for model_name, query_embedding in query_embeddings.items():
            distances, ids = self.indexes[model_name].search(query_embedding, k=top_k)
            for distance, report_id in zip(distances, ids):
                item = candidates.setdefault(int(report_id), {})
                item[model_name] = float(distance)

        return candidates

    def _compose_candidate(
        self,
        report: Report,
        latitude: float,
        longitude: float,
        model_distances: Dict[str, float],
        description: Optional[str],
        geo_threshold: float,
    ) -> CandidateScore:
        from geoalchemy2.shape import to_shape

        point = to_shape(report.location)
        report_lat = float(point.y)
        report_lon = float(point.x)

        geo_dist = haversine_distance(latitude, longitude, report_lat, report_lon)
        geo_similarity = self._geo_similarity(geo_dist, geo_threshold)
        text_similarity = _text_similarity(description, report.description)

        model_similarities = {
            model_name: self._distance_to_similarity(distance)
            for model_name, distance in model_distances.items()
        }
        fused = self._fusion_score(model_similarities, geo_similarity, text_similarity)

        primary_visual_distance = model_distances.get(self.primary_model)
        if primary_visual_distance is None and model_distances:
            primary_visual_distance = min(model_distances.values())
        if primary_visual_distance is None:
            primary_visual_distance = 2.0

        visual_similarity = model_similarities.get(self.primary_model, 0.0)

        age_days = max(0, (datetime.utcnow() - report.created_at).days)

        return CandidateScore(
            report=report,
            visual_distance=float(primary_visual_distance),
            geo_distance=float(geo_dist),
            fused_score=float(fused),
            visual_similarity=float(visual_similarity),
            geo_similarity=float(geo_similarity),
            text_similarity=float(text_similarity),
            model_distances={k: float(v) for k, v in model_distances.items()},
            model_similarities={k: float(v) for k, v in model_similarities.items()},
            age_days=age_days,
        )

    def find_similar_reports(
        self,
        image: Image.Image,
        latitude: float,
        longitude: float,
        damage_type: str,
        top_k: int = 20,
        description: Optional[str] = None,
    ) -> List[CandidateScore]:
        query_embeddings = self._query_embeddings(image)
        candidates = self._candidate_distances(query_embeddings, top_k=top_k)

        if not candidates:
            return []

        candidate_ids = list(candidates.keys())
        reports = self.db.query(Report).filter(Report.id.in_(candidate_ids)).all()
        reports_map = {r.id: r for r in reports}

        results: List[CandidateScore] = []
        for report_id, model_distances in candidates.items():
            report = reports_map.get(report_id)
            if report is None:
                continue

            if report.damage_type.value != damage_type:
                continue

            candidate = self._compose_candidate(
                report=report,
                latitude=latitude,
                longitude=longitude,
                model_distances=model_distances,
                description=description,
                geo_threshold=self.GEO_DISTANCE_THRESHOLD,
            )

            if candidate.age_days > self.TIME_WINDOW_DAYS:
                continue

            results.append(candidate)

        results.sort(key=lambda c: c.fused_score, reverse=True)
        return results

    def is_duplicate(
        self,
        image: Image.Image,
        latitude: float,
        longitude: float,
        damage_type: str,
        visual_threshold: Optional[float] = None,
        geo_threshold: Optional[float] = None,
        description: Optional[str] = None,
    ) -> Tuple[bool, Optional[Report], Dict[str, Any]]:
        visual_threshold = float(visual_threshold or self.VISUAL_SIMILARITY_THRESHOLD)
        geo_threshold = float(geo_threshold or self.GEO_DISTANCE_THRESHOLD)

        similar = self.find_similar_reports(
            image=image,
            latitude=latitude,
            longitude=longitude,
            damage_type=damage_type,
            top_k=25,
            description=description,
        )

        if not similar:
            return False, None, {"reason": "no_candidates"}

        for candidate in similar:
            meets_legacy = (
                candidate.visual_distance < visual_threshold
                and candidate.geo_distance < geo_threshold
            )
            meets_fusion = candidate.fused_score >= self.FUSION_SCORE_THRESHOLD

            if meets_legacy or meets_fusion:
                metadata = {
                    "reason": "duplicate_found",
                    "decision_mode": "legacy_and" if meets_legacy else "fusion_score",
                    "original_report_id": candidate.report.id,
                    "visual_distance": candidate.visual_distance,
                    "visual_similarity": candidate.visual_similarity,
                    "geo_distance": candidate.geo_distance,
                    "geo_similarity": candidate.geo_similarity,
                    "text_similarity": candidate.text_similarity,
                    "fused_score": candidate.fused_score,
                    "fusion_threshold": self.FUSION_SCORE_THRESHOLD,
                    "model_distances": candidate.model_distances,
                    "model_similarities": candidate.model_similarities,
                    "age_days": candidate.age_days,
                    "visual_threshold": visual_threshold,
                    "geo_threshold": geo_threshold,
                }
                return True, candidate.report, metadata

        best = similar[0]
        metadata = {
            "reason": "no_duplicate",
            "closest_report_id": best.report.id,
            "visual_distance": best.visual_distance,
            "visual_similarity": best.visual_similarity,
            "geo_distance": best.geo_distance,
            "geo_similarity": best.geo_similarity,
            "text_similarity": best.text_similarity,
            "fused_score": best.fused_score,
            "fusion_threshold": self.FUSION_SCORE_THRESHOLD,
            "model_distances": best.model_distances,
            "model_similarities": best.model_similarities,
            "age_days": best.age_days,
            "visual_threshold": visual_threshold,
            "geo_threshold": geo_threshold,
        }
        return False, None, metadata

    def rebuild_index(self, batch_size: int = 100):
        logger.info("Iniciando reconstrucción de índices FAISS dedup...")

        reports = (
            self.db.query(Report)
            .filter(Report.image_url.isnot(None), Report.status != ReportStatus.REJECTED)
            .order_by(Report.created_at.desc())
            .all()
        )

        for index in self.indexes.values():
            index.clear()

        if not reports:
            logger.warning("No hay reportes para indexar")
            return

        total = len(reports)
        indexed = 0

        for i in range(0, total, batch_size):
            batch = reports[i : i + batch_size]
            images: List[Image.Image] = []
            report_ids: List[int] = []

            for report in batch:
                img = self._load_report_image(report.image_url)
                if img is None:
                    continue
                images.append(img)
                report_ids.append(int(report.id))

            if not images:
                continue

            for model_name, embedder in self.embedders.items():
                try:
                    embeddings = embedder.embed_batch(images)
                    self.indexes[model_name].add(embeddings, report_ids)
                except Exception as exc:
                    logger.error("Error indexando batch con %s: %s", model_name, exc)

            indexed += len(report_ids)
            logger.info("Reconstrucción dedup: %s/%s reportes indexados", indexed, total)

        logger.info("Reconstrucción de índices dedup completada")

    def save_index(self, filepath: Optional[str] = None):
        if filepath:
            self.index_base_path = filepath

        for model_name, index in self.indexes.items():
            path = self._model_index_path(model_name)
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            index.save(path)

    def get_statistics(self) -> Dict[str, Any]:
        primary_index = self.indexes[self.primary_model]
        primary_embedder = self.embedders[self.primary_model]

        return {
            "index_size": int(primary_index.index.ntotal),
            "embedding_dim": int(primary_embedder.embedding_dim),
            "visual_threshold": float(self.VISUAL_SIMILARITY_THRESHOLD),
            "geo_threshold": float(self.GEO_DISTANCE_THRESHOLD),
            "time_window_days": int(self.TIME_WINDOW_DAYS),
            "active_models": list(self.models),
            "model_dimensions": {
                model_name: int(embedder.embedding_dim)
                for model_name, embedder in self.embedders.items()
            },
            "model_backends": {
                model_name: embedder.backend
                for model_name, embedder in self.embedders.items()
            },
            "model_index_sizes": {
                model_name: int(index.index.ntotal)
                for model_name, index in self.indexes.items()
            },
            "fusion_score_threshold": float(self.FUSION_SCORE_THRESHOLD),
            "weights": {
                "visual_primary": float(self.W_VISUAL_PRIMARY),
                "visual_secondary": float(self.W_VISUAL_SECONDARY),
                "geo": float(self.W_GEO),
                "text": float(self.W_TEXT),
            },
        }


_deduplication_service: Optional[DeduplicationService] = None


def get_deduplication_service(db: Session) -> DeduplicationService:
    global _deduplication_service

    if _deduplication_service is None:
        _deduplication_service = DeduplicationService(
            db=db,
            visual_model=getattr(settings, "DEDUPLICATION_VISUAL_MODEL", "resnet50"),
            secondary_visual_model=getattr(settings, "DEDUPLICATION_SECONDARY_MODEL", "clip"),
            index_path=getattr(settings, "FAISS_INDEX_PATH", None),
        )

    # Siempre refrescar sesión activa para operaciones de lectura/escritura.
    _deduplication_service.db = db
    return _deduplication_service
