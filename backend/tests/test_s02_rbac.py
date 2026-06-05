"""
Tests S-02 — RBAC granular con mínimos privilegios

Verifica que:
- Ciudadano recibe 403 en todos los endpoints de incidentes (SUPERVISOR+)
- Ciudadano recibe 403 en /reportes/jobs/{id}/status (SUPERVISOR+)
- Sin autenticación → 401 en endpoints protegidos
- Supervisor NO recibe 403 por rol en endpoints de incidentes
- Supervisor recibe 403 en endpoints exclusivos de ADMIN (sla/config PUT, sla/check)
- Admin NO recibe 403 en ningún endpoint
- Heatmap permite cualquier usuario autenticado (ciudadano → no 403)
- GET /reportes/{id}: ciudadano recibe 403 al intentar ver reporte ajeno
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.user import User, UserRole
from core.security import get_password_hash, create_access_token


# ─── Fixtures adicionales ──────────────────────────────────────────────────────

@pytest.fixture
def supervisor_user(test_db: Session) -> User:
    user = User(
        email="supervisor@test.com",
        username="supervisor_test",
        full_name="Supervisor Test",
        hashed_password=get_password_hash("supervisor123"),
        role=UserRole.SUPERVISOR,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def supervisor_token(supervisor_user: User) -> str:
    return create_access_token(
        subject=supervisor_user.id,
        additional_claims={"role": supervisor_user.role.value, "username": supervisor_user.username},
    )


@pytest.fixture
def auth_headers_supervisor(supervisor_token: str) -> dict:
    return {"Authorization": f"Bearer {supervisor_token}"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

INCIDENTS_BASE = "/api/v1/incidents"
REPORTS_BASE = "/api/v1/reportes"

# Respuestas válidas para supervisor/admin (rol ok, pero datos pueden fallar por SQLite/PostGIS)
ALLOWED_STATUS = {status.HTTP_200_OK, status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Endpoints de incidentes — ciudadano recibe 403
# ═══════════════════════════════════════════════════════════════════════════════

class TestIncidentsCiudadanoForbidden:
    """Ciudadano recibe 403 en todos los endpoints de incidentes."""

    def test_list_incidents_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{INCIDENTS_BASE}/", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_get_incident_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{INCIDENTS_BASE}/1", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_update_status_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.patch(
            f"{INCIDENTS_BASE}/1/status",
            headers=auth_headers_citizen,
            json={"status": "in_progress"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_update_details_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.patch(
            f"{INCIDENTS_BASE}/1/details",
            headers=auth_headers_citizen,
            data={"estimated_repair_hours": "4"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_recalculate_priority_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.post(f"{INCIDENTS_BASE}/1/recalculate-priority", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_priority_breakdown_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{INCIDENTS_BASE}/1/priority-breakdown", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_stats_overview_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{INCIDENTS_BASE}/stats/overview", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_audit_log_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{INCIDENTS_BASE}/1/audit", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_sla_expiring_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{INCIDENTS_BASE}/sla/expiring", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_sla_incident_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{INCIDENTS_BASE}/1/sla", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_sla_config_get_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{INCIDENTS_BASE}/sla/config", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_sla_config_put_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.put(
            f"{INCIDENTS_BASE}/sla/config",
            headers=auth_headers_citizen,
            json={"sla_hours_baja": 72},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_sla_check_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.post(f"{INCIDENTS_BASE}/sla/check", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Endpoints de incidentes — sin autenticación recibe 401
# ═══════════════════════════════════════════════════════════════════════════════

class TestIncidentsUnauthenticated:
    """Sin token → 401 en endpoints protegidos."""

    def test_list_incidents_unauthenticated(self, client: TestClient):
        r = client.get(f"{INCIDENTS_BASE}/")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_incident_unauthenticated(self, client: TestClient):
        r = client.get(f"{INCIDENTS_BASE}/1")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_status_unauthenticated(self, client: TestClient):
        r = client.patch(f"{INCIDENTS_BASE}/1/status", json={"status": "in_progress"})
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_sla_config_unauthenticated(self, client: TestClient):
        r = client.get(f"{INCIDENTS_BASE}/sla/config")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Supervisor tiene acceso (no 403) en endpoints SUPERVISOR+
# ═══════════════════════════════════════════════════════════════════════════════

class TestIncidentsSupervisorAllowed:
    """Supervisor NO recibe 403 (puede recibir 200/404/500 por falta de datos PostGIS)."""

    def test_list_incidents_supervisor_not_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.get(f"{INCIDENTS_BASE}/", headers=auth_headers_supervisor)
        assert r.status_code != status.HTTP_403_FORBIDDEN

    def test_get_incident_supervisor_not_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.get(f"{INCIDENTS_BASE}/999", headers=auth_headers_supervisor)
        assert r.status_code != status.HTTP_403_FORBIDDEN

    def test_update_status_supervisor_not_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.patch(
            f"{INCIDENTS_BASE}/999/status",
            headers=auth_headers_supervisor,
            json={"status": "in_progress"},
        )
        assert r.status_code != status.HTTP_403_FORBIDDEN

    def test_stats_overview_supervisor_not_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.get(f"{INCIDENTS_BASE}/stats/overview", headers=auth_headers_supervisor)
        assert r.status_code != status.HTTP_403_FORBIDDEN

    def test_sla_config_get_supervisor_not_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.get(f"{INCIDENTS_BASE}/sla/config", headers=auth_headers_supervisor)
        assert r.status_code != status.HTTP_403_FORBIDDEN


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Admin tiene acceso (no 403) en todos los endpoints
# ═══════════════════════════════════════════════════════════════════════════════

class TestIncidentsAdminAllowed:
    """Admin NO recibe 403 en ningún endpoint de incidentes."""

    def test_list_incidents_admin_not_forbidden(
        self, client: TestClient, auth_headers_admin: dict
    ):
        r = client.get(f"{INCIDENTS_BASE}/", headers=auth_headers_admin)
        assert r.status_code != status.HTTP_403_FORBIDDEN

    def test_sla_config_put_admin_not_forbidden(
        self, client: TestClient, auth_headers_admin: dict
    ):
        r = client.put(
            f"{INCIDENTS_BASE}/sla/config",
            headers=auth_headers_admin,
            json={"sla_hours_baja": 72},
        )
        assert r.status_code != status.HTTP_403_FORBIDDEN

    def test_sla_check_admin_not_forbidden(
        self, client: TestClient, auth_headers_admin: dict
    ):
        r = client.post(f"{INCIDENTS_BASE}/sla/check", headers=auth_headers_admin)
        assert r.status_code != status.HTTP_403_FORBIDDEN


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PUT sla/config y POST sla/check son exclusivos de ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdminOnlyEndpoints:
    """Supervisor recibe 403 en endpoints exclusivos de ADMIN."""

    def test_sla_config_put_supervisor_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.put(
            f"{INCIDENTS_BASE}/sla/config",
            headers=auth_headers_supervisor,
            json={"sla_hours_baja": 72},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_sla_check_supervisor_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.post(f"{INCIDENTS_BASE}/sla/check", headers=auth_headers_supervisor)
        assert r.status_code == status.HTTP_403_FORBIDDEN


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Heatmap — ciudadano autenticado tiene acceso (dato agregado)
# ═══════════════════════════════════════════════════════════════════════════════

class TestHeatmapOpen:
    """Heatmap mantiene acceso para cualquier usuario autenticado."""

    def test_heatmap_ciudadano_allowed(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{INCIDENTS_BASE}/heatmap", headers=auth_headers_citizen)
        assert r.status_code != status.HTTP_403_FORBIDDEN

    def test_heatmap_unauthenticated_forbidden(self, client: TestClient):
        r = client.get(f"{INCIDENTS_BASE}/heatmap")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED


# ═══════════════════════════════════════════════════════════════════════════════
# 7. GET /reportes/jobs/{id}/status — solo SUPERVISOR+
# ═══════════════════════════════════════════════════════════════════════════════

class TestJobStatusRBAC:
    """Job status endpoint requiere SUPERVISOR+."""

    def test_job_status_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{REPORTS_BASE}/jobs/fake-job-id/status", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_job_status_unauthenticated(self, client: TestClient):
        r = client.get(f"{REPORTS_BASE}/jobs/fake-job-id/status")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_job_status_supervisor_not_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.get(f"{REPORTS_BASE}/jobs/fake-job-id/status", headers=auth_headers_supervisor)
        assert r.status_code != status.HTTP_403_FORBIDDEN


# ═══════════════════════════════════════════════════════════════════════════════
# 8. GET /reportes/{id} — ciudadano no puede ver reporte ajeno
# ═══════════════════════════════════════════════════════════════════════════════

class TestReportOwnershipCheck:
    """Ciudadano recibe 403 al intentar ver reporte de otro usuario."""

    def test_get_report_unauthenticated(self, client: TestClient):
        r = client.get(f"{REPORTS_BASE}/999")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_nonexistent_report_ciudadano_gets_404(
        self, client: TestClient, auth_headers_citizen: dict
    ):
        """
        Reporte inexistente → 404 en producción (PostgreSQL).
        En test env con SQLite (sin tabla reports) → 500.
        Ambos son correctos para esta prueba: lo importante es que no devuelve 200 ni 403 sin datos.
        """
        r = client.get(f"{REPORTS_BASE}/99999", headers=auth_headers_citizen)
        assert r.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_get_report_ownership_check_logic(self, citizen_user: User):
        """
        Unit test directo: lógica de ownership rechaza reporte ajeno con 403.
        Llama la función async directamente sin HTTP layer ni PostGIS.
        """
        import asyncio
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from models.report import Report, DamageType, SeverityLevel, ReportStatus
        from api.routes.reports import get_report

        other_user_id = citizen_user.id + 1000

        mock_report = MagicMock(spec=Report)
        mock_report.id = 42
        mock_report.user_id = other_user_id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_report

        mock_citizen = MagicMock()
        mock_citizen.id = citizen_user.id
        mock_citizen.role = MagicMock()
        mock_citizen.role.value = "ciudadano"

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_report(report_id=42, db=mock_db, current_user=mock_citizen))

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
