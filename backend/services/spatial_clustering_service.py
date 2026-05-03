"""
Servicio de Clustering Espacial (M-13)

Agrupa reportes existentes en la BD mediante DBSCAN geoespacial.
Complementa M-11 (deduplicación por reporte individual) con análisis
de área completa: detecta grupos de reportes que reportan el mismo daño.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import DBSCAN
from sqlalchemy.orm import Session

from models.report import Report, ReportStatus

logger = logging.getLogger(__name__)

_EARTH_RADIUS_M = 6_371_000.0


def _haversine_matrix(coords_rad: np.ndarray) -> np.ndarray:
    """Pairwise haversine distance matrix (meters) — used internally for verification."""
    n = len(coords_rad)
    dist = np.zeros((n, n), dtype="float64")
    for i in range(n):
        for j in range(i + 1, n):
            dlat = coords_rad[j, 0] - coords_rad[i, 0]
            dlon = coords_rad[j, 1] - coords_rad[i, 1]
            a = math.sin(dlat / 2) ** 2 + (
                math.cos(coords_rad[i, 0]) * math.cos(coords_rad[j, 0]) * math.sin(dlon / 2) ** 2
            )
            d = 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))
            dist[i, j] = dist[j, i] = d
    return dist


@dataclass
class ClusterMember:
    report_id: int
    latitude: float
    longitude: float
    damage_type: str
    severity: str
    confidence: float
    status: str
    created_at: str
    is_primary: bool = False


@dataclass
class SpatialCluster:
    cluster_id: int
    primary_report_id: int
    member_count: int
    centroid_lat: float
    centroid_lon: float
    damage_type: str
    radius_m: float
    members: List[ClusterMember] = field(default_factory=list)
    oldest_report_at: Optional[str] = None
    newest_report_at: Optional[str] = None


@dataclass
class ClusteringResult:
    clusters: List[SpatialCluster]
    noise_report_ids: List[int]
    total_reports_analyzed: int
    total_clustered: int
    total_noise: int
    eps_meters: float
    min_samples: int
    damage_type_filter: Optional[str]
    time_window_days: Optional[int]


def get_clustering_params(
    db,
    eps_meters,
    min_samples,
    time_window_days,
):
    """
    Resolve clustering params: use explicit values when provided,
    fall back to admin PrioritySetting row, then hardcoded defaults.
    """
    if eps_meters is None or min_samples is None or time_window_days is None:
        try:
            from models.priority_setting import PrioritySetting
            row = db.query(PrioritySetting).order_by(PrioritySetting.id.asc()).first()
        except Exception:
            row = None
        if row:
            if eps_meters is None:
                eps_meters = float(getattr(row, "clustering_eps_meters", 50))
            if min_samples is None:
                min_samples = int(getattr(row, "clustering_min_samples", 2))
            if time_window_days is None:
                time_window_days = int(getattr(row, "duplicate_time_window_days", 30))
    return (
        eps_meters if eps_meters is not None else 50.0,
        min_samples if min_samples is not None else 2,
        time_window_days if time_window_days is not None else 30,
    )


class SpatialClusteringService:
    """
    Clustering espacial DBSCAN sobre reportes de la BD.

    M-11 responde: "¿este reporte nuevo es duplicado de uno existente?" (1 vs todos).
    M-13 responde: "¿qué grupos de reportes existentes describen el mismo daño?" (todos vs todos).
    """

    def __init__(
        self,
        db: Session,
        eps_meters: float = 50.0,
        min_samples: int = 2,
        time_window_days: Optional[int] = 30,
    ):
        self.db = db
        self.eps_meters = eps_meters
        self.min_samples = min_samples
        self.time_window_days = time_window_days

    def _fetch_reports(self, damage_type: Optional[str]) -> List[Report]:
        query = self.db.query(Report).filter(Report.status != ReportStatus.REJECTED)

        if self.time_window_days is not None:
            cutoff = datetime.utcnow() - timedelta(days=self.time_window_days)
            query = query.filter(Report.created_at >= cutoff)

        if damage_type:
            query = query.filter(Report.damage_type == damage_type)

        return query.order_by(Report.created_at.asc()).all()

    @staticmethod
    def _report_coords(report: Report) -> Tuple[float, float]:
        from geoalchemy2.shape import to_shape

        point = to_shape(report.location)
        return float(point.y), float(point.x)  # lat, lon

    def _select_primary(self, members: List[Report]) -> Report:
        """Primary = highest confidence; tie-break = earliest creation date."""
        return max(members, key=lambda r: (r.confidence, -r.created_at.timestamp()))

    def _cluster_radius(self, members: List[Report], centroid_lat: float, centroid_lon: float) -> float:
        if len(members) <= 1:
            return 0.0

        max_dist = 0.0
        clat_rad = math.radians(centroid_lat)
        clon_rad = math.radians(centroid_lon)

        for r in members:
            rlat, rlon = self._report_coords(r)
            dlat = math.radians(rlat) - clat_rad
            dlon = math.radians(rlon) - clon_rad
            a = math.sin(dlat / 2) ** 2 + math.cos(clat_rad) * math.cos(math.radians(rlat)) * math.sin(dlon / 2) ** 2
            d = 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))
            if d > max_dist:
                max_dist = d

        return round(max_dist, 2)

    def compute_clusters(self, damage_type: Optional[str] = None) -> ClusteringResult:
        """
        Ejecuta DBSCAN sobre todos los reportes activos y retorna clusters.

        Args:
            damage_type: Filtro opcional por tipo de daño ("bache" | "grieta").

        Returns:
            ClusteringResult con lista de SpatialCluster y reportes noise.
        """
        reports = self._fetch_reports(damage_type)
        total = len(reports)

        if total == 0:
            return ClusteringResult(
                clusters=[],
                noise_report_ids=[],
                total_reports_analyzed=0,
                total_clustered=0,
                total_noise=0,
                eps_meters=self.eps_meters,
                min_samples=self.min_samples,
                damage_type_filter=damage_type,
                time_window_days=self.time_window_days,
            )

        # Build coordinate matrix in radians for DBSCAN haversine
        coords = np.array(
            [list(self._report_coords(r)) for r in reports], dtype="float64"
        )
        coords_rad = np.radians(coords)

        eps_rad = self.eps_meters / _EARTH_RADIUS_M

        db = DBSCAN(
            eps=eps_rad,
            min_samples=self.min_samples,
            algorithm="ball_tree",
            metric="haversine",
        )
        labels = db.fit_predict(coords_rad)

        # Group by label
        label_to_reports: Dict[int, List[Report]] = {}
        noise_ids: List[int] = []

        for idx, (label, report) in enumerate(zip(labels, reports)):
            if label == -1:
                noise_ids.append(report.id)
            else:
                label_to_reports.setdefault(int(label), []).append(report)

        # Build SpatialCluster objects
        clusters: List[SpatialCluster] = []

        for cluster_label in sorted(label_to_reports.keys()):
            members = label_to_reports[cluster_label]
            primary = self._select_primary(members)

            lats = [self._report_coords(r)[0] for r in members]
            lons = [self._report_coords(r)[1] for r in members]
            centroid_lat = float(np.mean(lats))
            centroid_lon = float(np.mean(lons))
            radius = self._cluster_radius(members, centroid_lat, centroid_lon)

            # Damage type: all same when filtering; otherwise use primary's
            cluster_damage_type = primary.damage_type.value

            created_ats = sorted(r.created_at for r in members)

            cluster_members = [
                ClusterMember(
                    report_id=r.id,
                    latitude=self._report_coords(r)[0],
                    longitude=self._report_coords(r)[1],
                    damage_type=r.damage_type.value,
                    severity=r.severity.value,
                    confidence=float(r.confidence),
                    status=r.status.value,
                    created_at=r.created_at.isoformat(),
                    is_primary=(r.id == primary.id),
                )
                for r in members
            ]

            clusters.append(
                SpatialCluster(
                    cluster_id=cluster_label,
                    primary_report_id=primary.id,
                    member_count=len(members),
                    centroid_lat=round(centroid_lat, 7),
                    centroid_lon=round(centroid_lon, 7),
                    damage_type=cluster_damage_type,
                    radius_m=radius,
                    members=cluster_members,
                    oldest_report_at=created_ats[0].isoformat() if created_ats else None,
                    newest_report_at=created_ats[-1].isoformat() if created_ats else None,
                )
            )

        total_clustered = sum(c.member_count for c in clusters)
        logger.info(
            "M-13 clustering: %d reportes → %d clusters, %d noise (eps=%.1fm, min=%d)",
            total,
            len(clusters),
            len(noise_ids),
            self.eps_meters,
            self.min_samples,
        )

        return ClusteringResult(
            clusters=clusters,
            noise_report_ids=noise_ids,
            total_reports_analyzed=total,
            total_clustered=total_clustered,
            total_noise=len(noise_ids),
            eps_meters=self.eps_meters,
            min_samples=self.min_samples,
            damage_type_filter=damage_type,
            time_window_days=self.time_window_days,
        )

    def resolve_cluster(
        self,
        cluster_id: int,
        damage_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resuelve un cluster: marca todos los miembros no-primarios como REJECTED.

        Returns:
            Dict con primary_report_id, resolved_ids, skipped_ids.
        """
        result = self.compute_clusters(damage_type=damage_type)

        target = next((c for c in result.clusters if c.cluster_id == cluster_id), None)
        if target is None:
            raise ValueError(f"Cluster {cluster_id} no encontrado")

        non_primary_ids = [m.report_id for m in target.members if not m.is_primary]

        if not non_primary_ids:
            return {
                "primary_report_id": target.primary_report_id,
                "resolved_ids": [],
                "skipped_ids": [],
                "message": "Cluster con un solo miembro; nada que resolver",
            }

        reports = (
            self.db.query(Report)
            .filter(Report.id.in_(non_primary_ids))
            .all()
        )

        resolved: List[int] = []
        skipped: List[int] = []

        for r in reports:
            if r.status == ReportStatus.REJECTED:
                skipped.append(r.id)
            else:
                r.status = ReportStatus.REJECTED
                r.rejection_reason = (
                    f"Duplicado espacial — cluster M-13 #{cluster_id}, "
                    f"reporte primario #{target.primary_report_id}"
                )
                r.updated_at = datetime.utcnow()
                resolved.append(r.id)

        self.db.commit()

        logger.info(
            "M-13 resolve cluster %d: primary=%d resolved=%d skipped=%d",
            cluster_id,
            target.primary_report_id,
            len(resolved),
            len(skipped),
        )

        return {
            "primary_report_id": target.primary_report_id,
            "resolved_ids": resolved,
            "skipped_ids": skipped,
            "message": f"{len(resolved)} reporte(s) marcados como duplicados",
        }

    def resolve_all_clusters(
        self,
        damage_type: Optional[str] = None,
        min_cluster_size: int = 2,
    ) -> Dict[str, Any]:
        """
        Resuelve todos los clusters de una sola operación batch.

        Args:
            damage_type: Filtro por tipo de daño.
            min_cluster_size: Solo resolver clusters con al menos N miembros.

        Returns:
            Resumen con totales por cluster.
        """
        result = self.compute_clusters(damage_type=damage_type)

        eligible = [c for c in result.clusters if c.member_count >= min_cluster_size]

        all_resolved: List[int] = []
        all_skipped: List[int] = []
        cluster_summaries: List[Dict[str, Any]] = []

        for cluster in eligible:
            non_primary_ids = [m.report_id for m in cluster.members if not m.is_primary]
            if not non_primary_ids:
                continue

            reports = self.db.query(Report).filter(Report.id.in_(non_primary_ids)).all()

            resolved: List[int] = []
            skipped: List[int] = []

            for r in reports:
                if r.status == ReportStatus.REJECTED:
                    skipped.append(r.id)
                else:
                    r.status = ReportStatus.REJECTED
                    r.rejection_reason = (
                        f"Duplicado espacial — cluster M-13 #{cluster.cluster_id}, "
                        f"reporte primario #{cluster.primary_report_id}"
                    )
                    r.updated_at = datetime.utcnow()
                    resolved.append(r.id)

            cluster_summaries.append(
                {
                    "cluster_id": cluster.cluster_id,
                    "primary_report_id": cluster.primary_report_id,
                    "resolved": len(resolved),
                    "skipped": len(skipped),
                }
            )
            all_resolved.extend(resolved)
            all_skipped.extend(skipped)

        self.db.commit()

        logger.info(
            "M-13 resolve_all: %d clusters → %d resolved, %d skipped",
            len(eligible),
            len(all_resolved),
            len(all_skipped),
        )

        return {
            "clusters_processed": len(eligible),
            "total_resolved": len(all_resolved),
            "total_skipped": len(all_skipped),
            "resolved_ids": all_resolved,
            "cluster_summaries": cluster_summaries,
        }
