"""
M-11: Evaluación de embeddings visuales para deduplicación.

Compara modelos de embeddings (ResNet/CLIP) en similitud sobre reportes reales
utilizando pseudo-labels basados en proximidad geo-temporal y tipo de daño.

Uso:
  python backend/scripts/evaluate_dedup_embeddings.py
  python backend/scripts/evaluate_dedup_embeddings.py --models resnet50 clip-vit-base-patch32 --max-reports 250
"""

from __future__ import annotations

import argparse
import io
import json
import random
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import requests
from PIL import Image

# Permite ejecutar el script desde backend/ o desde la raíz del monorepo.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.config import settings
from db.session import SessionLocal
from models.report import Report, ReportStatus
from services.deduplication_service import VisualEmbedder, haversine_distance


@dataclass
class ReportSample:
    report_id: int
    damage_type: str
    created_at: datetime
    latitude: float
    longitude: float
    description: Optional[str]
    image: Image.Image


def _load_image(image_url: str) -> Optional[Image.Image]:
    if not image_url:
        return None

    if image_url.startswith("/storage/images/"):
        rel = image_url.replace("/storage/images/", "")
        file_path = BACKEND_DIR / "storage" / "images" / rel
        if file_path.exists():
            return Image.open(file_path).convert("RGB")
        return None

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
                path = image_url.split(settings.MINIO_ENDPOINT)[-1].lstrip("/")
                bucket = path.split("/")[0]
                object_key = "/".join(path.split("/")[1:])
                obj = mc.get_object(bucket, object_key)
                try:
                    raw = obj.read()
                finally:
                    obj.close()
                    obj.release_conn()
                return Image.open(io.BytesIO(raw)).convert("RGB")

            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content)).convert("RGB")
        except Exception:
            return None

    return None


def _build_samples(max_reports: int, seed: int) -> List[ReportSample]:
    from geoalchemy2.shape import to_shape  # pyright: ignore[reportMissingImports]

    db = SessionLocal()
    try:
        reports = (
            db.query(Report)
            .filter(Report.image_url.isnot(None), Report.status != ReportStatus.REJECTED)
            .order_by(Report.created_at.desc())
            .limit(max_reports * 3)
            .all()
        )

        random.Random(seed).shuffle(reports)

        samples: List[ReportSample] = []
        for report in reports:
            if len(samples) >= max_reports:
                break

            image = _load_image(report.image_url)
            if image is None:
                continue

            point = to_shape(report.location)
            samples.append(
                ReportSample(
                    report_id=report.id,
                    damage_type=report.damage_type.value,
                    created_at=report.created_at,
                    latitude=float(point.y),
                    longitude=float(point.x),
                    description=report.description,
                    image=image,
                )
            )

        return samples
    finally:
        db.close()


def _build_pairs(
    samples: Sequence[ReportSample],
    geo_threshold: float,
    time_window_days: int,
    max_pairs: int,
    seed: int,
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    positives: List[Tuple[int, int]] = []
    negatives: List[Tuple[int, int]] = []

    n = len(samples)
    for i in range(n):
        a = samples[i]
        for j in range(i + 1, n):
            b = samples[j]

            geo = haversine_distance(a.latitude, a.longitude, b.latitude, b.longitude)
            dt_days = abs((a.created_at - b.created_at).days)

            is_positive = (
                a.damage_type == b.damage_type
                and geo <= geo_threshold
                and dt_days <= time_window_days
            )
            is_negative = (
                a.damage_type != b.damage_type
                or geo >= geo_threshold * 3
                or dt_days >= time_window_days * 2
            )

            if is_positive:
                positives.append((a.report_id, b.report_id))
            elif is_negative:
                negatives.append((a.report_id, b.report_id))

    rng = random.Random(seed)
    rng.shuffle(positives)
    rng.shuffle(negatives)

    positives = positives[: max_pairs // 2]
    negatives = negatives[: max_pairs // 2]

    if positives and negatives:
        target = min(len(positives), len(negatives))
        positives = positives[:target]
        negatives = negatives[:target]

    return positives, negatives


def _evaluate_model(
    model_name: str,
    samples: Sequence[ReportSample],
    positives: Sequence[Tuple[int, int]],
    negatives: Sequence[Tuple[int, int]],
) -> Dict[str, float]:
    from sklearn.metrics import precision_recall_curve, roc_auc_score  # type: ignore

    embedder = VisualEmbedder(model_name=model_name)

    emb_by_report: Dict[int, np.ndarray] = {}
    latencies_ms: List[float] = []

    for sample in samples:
        t0 = perf_counter()
        emb = embedder.embed(sample.image)
        latencies_ms.append((perf_counter() - t0) * 1000.0)
        emb_by_report[sample.report_id] = emb

    y_true: List[int] = []
    y_score: List[float] = []

    pos_scores: List[float] = []
    neg_scores: List[float] = []

    for a, b in positives:
        score = float(np.dot(emb_by_report[a], emb_by_report[b]))
        y_true.append(1)
        y_score.append(score)
        pos_scores.append(score)

    for a, b in negatives:
        score = float(np.dot(emb_by_report[a], emb_by_report[b]))
        y_true.append(0)
        y_score.append(score)
        neg_scores.append(score)

    auc = float(roc_auc_score(y_true, y_score))

    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    f1 = (2 * precision * recall) / np.maximum(precision + recall, 1e-9)

    if len(thresholds) > 0:
        best_idx = int(np.argmax(f1[:-1]))
        best_threshold = float(thresholds[best_idx])
        best_f1 = float(f1[best_idx])
        best_precision = float(precision[best_idx])
        best_recall = float(recall[best_idx])
    else:
        best_threshold = 0.5
        best_f1 = 0.0
        best_precision = 0.0
        best_recall = 0.0

    return {
        "model": model_name,
        "backend": embedder.backend,
        "device": embedder.device,
        "embedding_dim": int(embedder.embedding_dim),
        "samples": int(len(samples)),
        "pairs_positive": int(len(positives)),
        "pairs_negative": int(len(negatives)),
        "mean_positive_similarity": float(np.mean(pos_scores)) if pos_scores else 0.0,
        "mean_negative_similarity": float(np.mean(neg_scores)) if neg_scores else 0.0,
        "separation_margin": float(np.mean(pos_scores) - np.mean(neg_scores)) if pos_scores and neg_scores else 0.0,
        "roc_auc": auc,
        "best_threshold": best_threshold,
        "best_f1": best_f1,
        "best_precision": best_precision,
        "best_recall": best_recall,
        "latency_ms_avg": float(np.mean(latencies_ms)) if latencies_ms else 0.0,
        "latency_ms_p95": float(np.percentile(latencies_ms, 95)) if latencies_ms else 0.0,
    }


def main():
    parser = argparse.ArgumentParser(description="M-11 evaluation: CLIP vs ResNet for dedup similarity")
    parser.add_argument("--models", nargs="+", default=["resnet50", "clip-vit-base-patch32"])
    parser.add_argument("--max-reports", type=int, default=220)
    parser.add_argument("--max-pairs", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="backend/scripts/outputs/m11_embedding_evaluation.json")
    args = parser.parse_args()

    geo_threshold = float(getattr(settings, "GEO_DISTANCE_THRESHOLD", 50.0))
    time_window_days = int(getattr(settings, "DEDUP_TIME_WINDOW_DAYS", 30))

    samples = _build_samples(max_reports=args.max_reports, seed=args.seed)
    if len(samples) < 20:
        raise RuntimeError("No hay suficientes reportes con imagen para evaluar (mínimo recomendado: 20)")

    positives, negatives = _build_pairs(
        samples=samples,
        geo_threshold=geo_threshold,
        time_window_days=time_window_days,
        max_pairs=args.max_pairs,
        seed=args.seed,
    )

    if not positives or not negatives:
        raise RuntimeError("No se pudieron construir pares positivos/negativos suficientes para evaluación")

    model_results = []
    for model_name in args.models:
        model_results.append(_evaluate_model(model_name, samples, positives, negatives))

    best = sorted(
        model_results,
        key=lambda r: (r["roc_auc"], r["separation_margin"], -r["latency_ms_avg"]),
        reverse=True,
    )[0]

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "max_reports": args.max_reports,
        "max_pairs": args.max_pairs,
        "geo_threshold_m": geo_threshold,
        "time_window_days": time_window_days,
        "models": model_results,
        "recommended_model": best["model"],
        "recommendation_reason": {
            "roc_auc": best["roc_auc"],
            "separation_margin": best["separation_margin"],
            "latency_ms_avg": best["latency_ms_avg"],
        },
    }

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = BACKEND_DIR.parent / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("=" * 72)
    print("M-11 Embedding Evaluation")
    print("=" * 72)
    print(f"Samples: {len(samples)} | Pos pairs: {len(positives)} | Neg pairs: {len(negatives)}")
    print()
    for row in model_results:
        print(
            f"{row['model']:<24} backend={row['backend']:<12} auc={row['roc_auc']:.4f} "
            f"f1={row['best_f1']:.4f} sep={row['separation_margin']:.4f} "
            f"lat_avg={row['latency_ms_avg']:.1f}ms"
        )
    print()
    print(f"Recommended model: {best['model']}")
    print(f"Results saved to: {out_path}")


if __name__ == "__main__":
    main()
