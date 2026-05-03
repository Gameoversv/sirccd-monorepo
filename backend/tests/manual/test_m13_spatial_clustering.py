"""
Tests M-13: Spatial Clustering Service

Ejecutar con:
    python -m pytest tests/manual/test_m13_spatial_clustering.py -v --noconftest
"""

# ── Step 0: compute backend root (needed for stub __path__) ──────────────────
import pathlib as _pathlib
_BACKEND = _pathlib.Path(__file__).parents[2]

# ── Step 1: mock ALL heavy deps before any project import ─────────────────────
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

# Services that auto-import heavy libs
for _svc in [
    "services.ml_service", "services.anonymizer",
    "services.queue_service", "services.storage",
    "services.deduplication_service",
]:
    sys.modules.setdefault(_svc, MagicMock())

# models.report — must expose DamageType, SeverityLevel, ReportStatus
_rm = types.ModuleType("models.report")


class _EnumVal:
    """Minimal enum-like value: has .value, supports equality."""
    def __init__(self, v: str):
        self.value = v
    def __eq__(self, other):
        if isinstance(other, _EnumVal):
            return self.value == other.value
        return NotImplemented
    def __hash__(self):
        return hash(self.value)
    def __repr__(self):
        return self.value


class ReportStatus:
    REJECTED = _EnumVal("rejected")
    APPROVED = _EnumVal("approved")
    PENDING  = _EnumVal("pending")
    _by_value = {}

ReportStatus._by_value = {
    "rejected": ReportStatus.REJECTED,
    "approved": ReportStatus.APPROVED,
    "pending":  ReportStatus.PENDING,
}


class DamageType:
    BACHE = "bache"
    GRIETA = "grieta"


class SeverityLevel:
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"

_rm.ReportStatus = ReportStatus
_rm.DamageType = DamageType
_rm.SeverityLevel = SeverityLevel
_rm.Report = MagicMock()   # spatial_clustering_service imports Report
sys.modules["models.report"] = _rm

# geoalchemy2
_geo = types.ModuleType("geoalchemy2")
_geo.Geography = MagicMock()
_geo.Geometry = MagicMock()
_geo_shape = types.ModuleType("geoalchemy2.shape")

# Shape registry: maps sentinel → SimpleNamespace(y=lat, x=lon)
_SHAPE_REGISTRY: dict = {}
_geo_shape.to_shape = lambda sentinel: _SHAPE_REGISTRY[sentinel]
_geo.shape = _geo_shape
sys.modules.setdefault("geoalchemy2", _geo)
sys.modules.setdefault("geoalchemy2.shape", _geo_shape)

# SQLAlchemy stubs (models may import Column, etc.)
for _sa in ["sqlalchemy", "sqlalchemy.orm", "sqlalchemy.ext",
            "sqlalchemy.ext.declarative", "db.session", "core.config"]:
    sys.modules.setdefault(_sa, MagicMock())

# db.base needs a real Base class so models can inherit from it
_db_base = types.ModuleType("db.base")
class _Base:
    pass
_db_base.Base = _Base
sys.modules["db.base"] = _db_base

# Stub other model submodules so models/__init__.py loads without errors
for _mod in ["models.user", "models.incident", "models.poi", "models.metric"]:
    sys.modules.setdefault(_mod, MagicMock())

# Stub schemas package so schemas/__init__.py never runs (it imports everything)
# __path__ must point to the real directory so submodule files can be found.
_schemas_pkg = types.ModuleType("schemas")
_schemas_pkg.__path__ = [str(_BACKEND / "schemas")]
_schemas_pkg.__package__ = "schemas"
sys.modules.setdefault("schemas", _schemas_pkg)

# ── Step 2: add backend to sys.path ──────────────────────────────────────────
import pathlib
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# ── Step 3: import the units under test ──────────────────────────────────────
import math
from datetime import datetime, timedelta

import numpy as np
import pytest

from services.spatial_clustering_service import (   # noqa: E402
    SpatialClusteringService,
    get_clustering_params,
)
from schemas.deduplication import (                 # noqa: E402
    ClusterResolveRequest,
    SpatialClusteringResponse,
)
from schemas.priority_settings import (             # noqa: E402
    PrioritySettingsResponse,
    PrioritySettingsUpdateRequest,
)


def haversine_distance(lat1, lon1, lat2, lon2):
    """Local copy for testing (same formula as deduplication_service)."""
    import math
    r = 6_371_000.0
    rl1, rl2 = math.radians(lat1), math.radians(lat2)
    dl, dg = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dl / 2) ** 2 + math.cos(rl1) * math.cos(rl2) * math.sin(dg / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_report(
    rid: int,
    lat: float,
    lon: float,
    damage_type: str = "bache",
    severity: str = "media",
    confidence: float = 0.90,
    status_val: str = "approved",
    days_old: int = 0,
):
    r = MagicMock()
    r.id = rid
    sentinel = object()           # unique per-report sentinel
    r.location = sentinel
    _SHAPE_REGISTRY[sentinel] = SimpleNamespace(y=lat, x=lon)
    r.damage_type = SimpleNamespace(value=damage_type)
    r.severity = SimpleNamespace(value=severity)
    r.confidence = confidence
    r.status = ReportStatus._by_value.get(status_val, _EnumVal(status_val))
    r.created_at = datetime.utcnow() - timedelta(days=days_old)
    r.description = None
    return r


def _make_db(reports):
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.all.return_value = reports
    db.query.return_value = q
    return db


def _svc(reports, eps_meters=50.0, min_samples=2, time_window_days=None):
    # time_window_days=None avoids Report.created_at >= datetime comparison
    # on the MagicMock column, which raises TypeError outside SQLAlchemy context.
    return SpatialClusteringService(
        db=_make_db(reports),
        eps_meters=eps_meters,
        min_samples=min_samples,
        time_window_days=time_window_days,
    )


# ── haversine_distance ────────────────────────────────────────────────────────

class TestHaversineDistance:
    def test_same_point_is_zero(self):
        assert haversine_distance(19.45, -70.69, 19.45, -70.69) == pytest.approx(0.0, abs=1e-3)

    def test_one_degree_latitude(self):
        d = haversine_distance(0.0, 0.0, 1.0, 0.0)
        assert 110_000 < d < 112_000

    def test_symmetry(self):
        a, b = (18.4, -69.9), (18.5, -70.0)
        assert haversine_distance(*a, *b) == pytest.approx(haversine_distance(*b, *a), rel=1e-6)

    def test_small_distance(self):
        # 10 cm shift in latitude
        d = haversine_distance(19.45, -70.69, 19.450001, -70.69)
        assert d < 1.0  # less than 1 metre


# ── compute_clusters ──────────────────────────────────────────────────────────

class TestComputeClusters:
    def test_empty_db(self):
        result = _svc([]).compute_clusters()
        assert result.clusters == []
        assert result.noise_report_ids == []
        assert result.total_reports_analyzed == 0

    def test_two_close_reports_form_one_cluster(self):
        r1 = _make_report(1, 19.450000, -70.690000)
        r2 = _make_report(2, 19.450010, -70.690010)   # ~1.5 m away
        result = _svc([r1, r2]).compute_clusters()
        assert len(result.clusters) == 1
        assert result.clusters[0].member_count == 2
        assert result.total_noise == 0

    def test_two_far_reports_are_noise(self):
        r1 = _make_report(1, 19.0, -70.0)
        r2 = _make_report(2, 20.0, -70.0)             # ~111 km
        result = _svc([r1, r2]).compute_clusters()
        assert len(result.clusters) == 0
        assert len(result.noise_report_ids) == 2

    def test_single_report_is_noise(self):
        r1 = _make_report(1, 19.45, -70.69)
        result = _svc([r1]).compute_clusters()
        assert 1 in result.noise_report_ids

    def test_two_separate_clusters(self):
        a1 = _make_report(1, 19.450000, -70.690000)
        a2 = _make_report(2, 19.450010, -70.690010)
        b1 = _make_report(3, 18.480000, -69.900000)
        b2 = _make_report(4, 18.480010, -69.900010)
        result = _svc([a1, a2, b1, b2]).compute_clusters()
        assert len(result.clusters) == 2
        assert result.total_clustered == 4
        assert result.total_noise == 0

    def test_totals_are_consistent(self):
        r1 = _make_report(1, 19.450000, -70.690000)
        r2 = _make_report(2, 19.450010, -70.690010)
        r3 = _make_report(3, 20.000000, -70.000000)   # isolated
        result = _svc([r1, r2, r3]).compute_clusters()
        assert result.total_reports_analyzed == 3
        assert result.total_clustered + result.total_noise == 3

    def test_primary_by_confidence(self):
        r1 = _make_report(1, 19.450000, -70.690000, confidence=0.95)
        r2 = _make_report(2, 19.450010, -70.690010, confidence=0.70)
        result = _svc([r1, r2]).compute_clusters()
        assert result.clusters[0].primary_report_id == 1

    def test_primary_tiebreak_oldest(self):
        r1 = _make_report(1, 19.450000, -70.690000, confidence=0.80, days_old=10)
        r2 = _make_report(2, 19.450010, -70.690010, confidence=0.80, days_old=2)
        result = _svc([r1, r2]).compute_clusters()
        assert result.clusters[0].primary_report_id == 1

    def test_is_primary_flag(self):
        r1 = _make_report(1, 19.450000, -70.690000, confidence=0.95)
        r2 = _make_report(2, 19.450010, -70.690010, confidence=0.70)
        result = _svc([r1, r2]).compute_clusters()
        by_id = {m.report_id: m for m in result.clusters[0].members}
        assert by_id[1].is_primary is True
        assert by_id[2].is_primary is False

    def test_centroid_midpoint(self):
        lat1, lon1 = 19.450000, -70.690000
        lat2, lon2 = 19.450100, -70.690100
        r1 = _make_report(1, lat1, lon1)
        r2 = _make_report(2, lat2, lon2)
        result = _svc([r1, r2]).compute_clusters()
        c = result.clusters[0]
        assert c.centroid_lat == pytest.approx((lat1 + lat2) / 2, abs=1e-6)
        assert c.centroid_lon == pytest.approx((lon1 + lon2) / 2, abs=1e-6)

    def test_oldest_newest_ordering(self):
        r1 = _make_report(1, 19.450000, -70.690000, days_old=5)
        r2 = _make_report(2, 19.450010, -70.690010, days_old=1)
        result = _svc([r1, r2]).compute_clusters()
        c = result.clusters[0]
        assert c.oldest_report_at is not None
        assert c.newest_report_at is not None
        assert c.oldest_report_at < c.newest_report_at

    def test_eps_returned_in_result(self):
        result = _svc([], eps_meters=123.0).compute_clusters()
        assert result.eps_meters == 123.0

    def test_min_samples_returned_in_result(self):
        result = _svc([], min_samples=5).compute_clusters()
        assert result.min_samples == 5

    def test_damage_type_filter_stored_in_result(self):
        result = _svc([]).compute_clusters(damage_type="grieta")
        assert result.damage_type_filter == "grieta"

    def test_radius_nonnegative(self):
        r1 = _make_report(1, 19.450000, -70.690000)
        r2 = _make_report(2, 19.450010, -70.690010)
        result = _svc([r1, r2]).compute_clusters()
        assert result.clusters[0].radius_m >= 0.0

    def test_three_members_cluster(self):
        r1 = _make_report(1, 19.450000, -70.690000)
        r2 = _make_report(2, 19.450005, -70.690005)
        r3 = _make_report(3, 19.450010, -70.690010)
        result = _svc([r1, r2, r3]).compute_clusters()
        assert len(result.clusters) == 1
        assert result.clusters[0].member_count == 3


# ── resolve_cluster ───────────────────────────────────────────────────────────

class TestResolveCluster:
    def test_raises_for_unknown_cluster_id(self):
        db = _make_db([])
        svc = SpatialClusteringService(db=db, time_window_days=None)
        with pytest.raises(ValueError, match="99"):
            svc.resolve_cluster(cluster_id=99)

    def test_marks_non_primary_rejected(self):
        r1 = _make_report(1, 19.450000, -70.690000, confidence=0.95)
        r2 = _make_report(2, 19.450010, -70.690010, confidence=0.70)

        db = MagicMock()
        cluster_q = MagicMock()
        cluster_q.filter.return_value = cluster_q
        cluster_q.order_by.return_value = cluster_q
        cluster_q.all.return_value = [r1, r2]

        resolve_q = MagicMock()
        resolve_q.filter.return_value = resolve_q
        resolve_q.all.return_value = [r2]

        db.query.side_effect = [cluster_q, resolve_q]

        svc = SpatialClusteringService(db=db, eps_meters=50.0, min_samples=2, time_window_days=None)
        result = svc.resolve_cluster(cluster_id=0)

        assert result["primary_report_id"] == 1
        assert 2 in result["resolved_ids"]
        assert result["skipped_ids"] == []
        db.commit.assert_called_once()

    def test_already_rejected_is_skipped(self):
        r1 = _make_report(1, 19.450000, -70.690000, confidence=0.95)
        r2 = _make_report(2, 19.450010, -70.690010, confidence=0.70, status_val="rejected")

        db = MagicMock()
        cluster_q = MagicMock()
        cluster_q.filter.return_value = cluster_q
        cluster_q.order_by.return_value = cluster_q
        cluster_q.all.return_value = [r1, r2]

        resolve_q = MagicMock()
        resolve_q.filter.return_value = resolve_q
        resolve_q.all.return_value = [r2]

        db.query.side_effect = [cluster_q, resolve_q]

        svc = SpatialClusteringService(db=db, eps_meters=50.0, min_samples=2, time_window_days=None)

        # Patch ReportStatus at service module level
        import services.spatial_clustering_service as _svc_mod
        original = _svc_mod.ReportStatus
        _svc_mod.ReportStatus = ReportStatus
        try:
            result = svc.resolve_cluster(cluster_id=0)
        finally:
            _svc_mod.ReportStatus = original

        assert 2 in result["skipped_ids"]
        assert result["resolved_ids"] == []

    def test_single_member_cluster_returns_empty_resolved(self):
        # Cluster with only the primary — nothing to resolve
        r1 = _make_report(1, 19.450000, -70.690000)
        r2 = _make_report(2, 19.450005, -70.690005)

        # Build a cluster of 2, then call resolve; mock the resolve_q to return []
        db = MagicMock()
        cluster_q = MagicMock()
        cluster_q.filter.return_value = cluster_q
        cluster_q.order_by.return_value = cluster_q
        cluster_q.all.return_value = [r1, r2]

        resolve_q = MagicMock()
        resolve_q.filter.return_value = resolve_q
        resolve_q.all.return_value = []  # already all rejected

        db.query.side_effect = [cluster_q, resolve_q]

        svc = SpatialClusteringService(db=db, eps_meters=50.0, min_samples=2, time_window_days=None)
        result = svc.resolve_cluster(cluster_id=0)
        assert result["resolved_ids"] == []


# ── resolve_all_clusters ──────────────────────────────────────────────────────

class TestResolveAllClusters:
    def test_two_clusters_both_resolved(self):
        a1 = _make_report(1, 19.450000, -70.690000, confidence=0.95)
        a2 = _make_report(2, 19.450010, -70.690010, confidence=0.70)
        b1 = _make_report(3, 18.480000, -69.900000, confidence=0.90)
        b2 = _make_report(4, 18.480010, -69.900010, confidence=0.60)

        db = MagicMock()
        cluster_q = MagicMock()
        cluster_q.filter.return_value = cluster_q
        cluster_q.order_by.return_value = cluster_q
        cluster_q.all.return_value = [a1, a2, b1, b2]

        qa = MagicMock(); qa.filter.return_value = qa; qa.all.return_value = [a2]
        qb = MagicMock(); qb.filter.return_value = qb; qb.all.return_value = [b2]
        db.query.side_effect = [cluster_q, qa, qb]

        svc = SpatialClusteringService(db=db, eps_meters=50.0, min_samples=2, time_window_days=None)
        result = svc.resolve_all_clusters()

        assert result["clusters_processed"] == 2
        assert result["total_resolved"] == 2
        db.commit.assert_called()

    def test_min_cluster_size_filters(self):
        a1 = _make_report(1, 19.450000, -70.690000)
        a2 = _make_report(2, 19.450010, -70.690010)
        db = _make_db([a1, a2])
        svc = SpatialClusteringService(db=db, eps_meters=50.0, min_samples=2, time_window_days=None)
        result = svc.resolve_all_clusters(min_cluster_size=3)
        assert result["clusters_processed"] == 0
        assert result["total_resolved"] == 0

    def test_empty_db_returns_zero(self):
        db = _make_db([])
        svc = SpatialClusteringService(db=db, time_window_days=None)
        result = svc.resolve_all_clusters()
        assert result["clusters_processed"] == 0
        assert result["total_resolved"] == 0


# ── get_clustering_params (service helper) ────────────────────────────────────

def _row(eps=75, minsamp=3, window=14):
    return SimpleNamespace(
        clustering_eps_meters=eps,
        clustering_min_samples=minsamp,
        duplicate_time_window_days=window,
    )


def _db_with_row(row):
    db = MagicMock()
    q = MagicMock()
    q.order_by.return_value = q
    q.first.return_value = row
    db.query.return_value = q
    return db


class TestGetClusteringParams:
    def test_all_none_reads_from_db(self):
        db = _db_with_row(_row(75, 3, 14))
        eps, minsamp, win = get_clustering_params(db, None, None, None)
        assert eps == 75.0
        assert minsamp == 3
        assert win == 14

    def test_explicit_values_override_db(self):
        db = _db_with_row(_row(75, 3, 14))
        eps, minsamp, win = get_clustering_params(db, 200.0, 5, 60)
        assert eps == 200.0
        assert minsamp == 5
        assert win == 60

    def test_no_db_row_uses_hardcoded_defaults(self):
        db = _db_with_row(None)
        eps, minsamp, win = get_clustering_params(db, None, None, None)
        assert eps == 50.0
        assert minsamp == 2
        assert win == 30

    def test_partial_override_reads_db_for_missing(self):
        db = _db_with_row(_row(75, 3, 14))
        eps, minsamp, win = get_clustering_params(db, 200.0, None, None)
        assert eps == 200.0
        assert minsamp == 3
        assert win == 14


# ── Schemas ───────────────────────────────────────────────────────────────────

class TestSchemas:
    def test_cluster_resolve_request_defaults_none(self):
        from schemas.deduplication import ClusterResolveRequest
        req = ClusterResolveRequest(cluster_id=5)
        assert req.eps_meters is None
        assert req.min_samples is None
        assert req.time_window_days is None

    def test_cluster_resolve_request_explicit(self):
        from schemas.deduplication import ClusterResolveRequest
        req = ClusterResolveRequest(cluster_id=5, eps_meters=100.0, min_samples=3, time_window_days=60)
        assert req.eps_meters == 100.0
        assert req.min_samples == 3
        assert req.time_window_days == 60

    def test_spatial_clustering_response(self):
        from schemas.deduplication import SpatialClusteringResponse
        data = {
            "clusters": [], "noise_report_ids": [1, 2],
            "total_reports_analyzed": 2, "total_clustered": 0,
            "total_noise": 2, "eps_meters": 50.0, "min_samples": 2,
            "damage_type_filter": None, "time_window_days": 30,
        }
        resp = SpatialClusteringResponse(**data)
        assert resp.total_noise == 2

    def test_priority_settings_response_has_clustering_fields(self):
        from schemas.priority_settings import PrioritySettingsResponse
        assert "clustering_eps_meters" in PrioritySettingsResponse.model_fields
        assert "clustering_min_samples" in PrioritySettingsResponse.model_fields

    def test_priority_settings_update_clustering_fields(self):
        from schemas.priority_settings import PrioritySettingsUpdateRequest
        req = PrioritySettingsUpdateRequest(clustering_eps_meters=75, clustering_min_samples=3)
        assert req.clustering_eps_meters == 75
        assert req.clustering_min_samples == 3

    def test_clustering_eps_below_min_raises(self):
        import pydantic
        from schemas.priority_settings import PrioritySettingsUpdateRequest
        with pytest.raises(pydantic.ValidationError):
            PrioritySettingsUpdateRequest(clustering_eps_meters=3)   # ge=5

    def test_clustering_eps_above_max_raises(self):
        import pydantic
        from schemas.priority_settings import PrioritySettingsUpdateRequest
        with pytest.raises(pydantic.ValidationError):
            PrioritySettingsUpdateRequest(clustering_eps_meters=9999)  # le=2000

    def test_clustering_min_samples_below_min_raises(self):
        import pydantic
        from schemas.priority_settings import PrioritySettingsUpdateRequest
        with pytest.raises(pydantic.ValidationError):
            PrioritySettingsUpdateRequest(clustering_min_samples=1)   # ge=2

    def test_clustering_min_samples_above_max_raises(self):
        import pydantic
        from schemas.priority_settings import PrioritySettingsUpdateRequest
        with pytest.raises(pydantic.ValidationError):
            PrioritySettingsUpdateRequest(clustering_min_samples=21)  # le=20


# ── Model columns ─────────────────────────────────────────────────────────────

class TestModel:
    def test_priority_setting_has_clustering_columns(self):
        from models.priority_setting import PrioritySetting
        assert hasattr(PrioritySetting, "clustering_eps_meters")
        assert hasattr(PrioritySetting, "clustering_min_samples")


# ── Alembic migration (text-based checks — avoids real sqlalchemy import) ─────

class TestMigration:
    def _src(self):
        path = _BACKEND / "alembic" / "versions" / "003_add_clustering_params.py"
        return path.read_text(encoding="utf-8")

    def test_revision_id(self):
        assert 'revision: str = "003"' in self._src()

    def test_down_revision(self):
        assert 'down_revision' in self._src()
        assert '"002"' in self._src()

    def test_adds_eps_column(self):
        assert "clustering_eps_meters" in self._src()

    def test_adds_min_samples_column(self):
        assert "clustering_min_samples" in self._src()

    def test_has_upgrade(self):
        assert "def upgrade()" in self._src()

    def test_has_downgrade(self):
        assert "def downgrade()" in self._src()

    def test_downgrade_drops_both_columns(self):
        src = self._src()
        assert src.count("drop_column") == 2


# ── i18n JSON validity ────────────────────────────────────────────────────────

class TestI18n:
    def _load(self, locale: str):
        import json
        path = _BACKEND.parent / "frontend" / "src" / "i18n" / "locales" / f"{locale}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_es_json_valid(self):
        data = self._load("es")
        assert "settings" in data

    def test_en_json_valid(self):
        data = self._load("en")
        assert "settings" in data

    def test_es_clustering_keys(self):
        data = self._load("es")
        s = data["settings"]
        assert "clustering" in s["sections"]
        assert "clusteringHint" in s
        assert "clusteringEps" in s["fields"]
        assert "clusteringMinSamples" in s["fields"]

    def test_en_clustering_keys(self):
        data = self._load("en")
        s = data["settings"]
        assert "clustering" in s["sections"]
        assert "clusteringHint" in s
        assert "clusteringEps" in s["fields"]
        assert "clusteringMinSamples" in s["fields"]
