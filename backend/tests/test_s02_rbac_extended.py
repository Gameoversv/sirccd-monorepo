"""
Tests S-02 extended — RBAC gaps no cubiertos en test_s02_rbac.py

Cubre:
- /users/* RBAC completo (ciudadano/supervisor/admin)
- Role escalation: ciudadano intentando PATCH /users/{id}
- Admin self-protection: no puede bajar su propio rol ni desactivarse
- /export/* RBAC (ciudadano 403 en endpoints SUPERVISOR+)
- /admin/settings/priority RBAC (solo ADMIN)
- /deduplication write ops RBAC (rebuild/save/resolve → SUPERVISOR+)
- Positive ownership: supervisor puede ver reporte de cualquier ciudadano
"""

import asyncio
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from models.user import User, UserRole
from core.security import get_password_hash, create_access_token


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def supervisor_user(test_db: Session) -> User:
    user = User(
        email="supervisor2@test.com",
        username="supervisor_ext",
        full_name="Supervisor Extended",
        hashed_password=get_password_hash("sup123456"),
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


USERS_BASE = "/api/v1/users"
EXPORT_BASE = "/api/v1/export"
SETTINGS_BASE = "/api/v1/admin/settings"
DEDUP_BASE = "/api/v1/deduplication"

ALLOWED = {
    status.HTTP_200_OK,
    status.HTTP_201_CREATED,
    status.HTTP_204_NO_CONTENT,
    status.HTTP_400_BAD_REQUEST,  # lógica de negocio, no RBAC
    status.HTTP_404_NOT_FOUND,
    status.HTTP_422_UNPROCESSABLE_ENTITY,
    status.HTTP_500_INTERNAL_SERVER_ERROR,  # error de datos/PostGIS en test env
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. /users/* RBAC — ciudadano bloqueado
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsersEndpointsCiudadanoForbidden:
    """Ciudadano recibe 403 en todos los endpoints de usuarios excepto /me."""

    def test_list_users_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{USERS_BASE}/", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_by_id_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{USERS_BASE}/1", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_create_user_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.post(
            f"{USERS_BASE}/",
            headers=auth_headers_citizen,
            json={"email": "x@x.com", "username": "newuser", "password": "pass1234", "role": "ciudadano"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.patch(
            f"{USERS_BASE}/1",
            headers=auth_headers_citizen,
            json={"full_name": "Hack"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_deactivate_user_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.delete(f"{USERS_BASE}/1", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_permanent_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.delete(f"{USERS_BASE}/1/permanent", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_get_me_ciudadano_allowed(self, client: TestClient, auth_headers_citizen: dict):
        """/users/me es accesible para cualquier usuario autenticado."""
        r = client.get(f"{USERS_BASE}/me", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_200_OK


# ═══════════════════════════════════════════════════════════════════════════════
# 2. /users/* RBAC — supervisor bloqueado en endpoints ADMIN-only
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsersEndpointsSupervisorPartial:
    """Supervisor puede listar/ver usuarios pero NO crear/modificar/eliminar."""

    def test_list_users_supervisor_allowed(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.get(f"{USERS_BASE}/", headers=auth_headers_supervisor)
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_supervisor_allowed(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.get(f"{USERS_BASE}/999", headers=auth_headers_supervisor)
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_supervisor_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.post(
            f"{USERS_BASE}/",
            headers=auth_headers_supervisor,
            json={"email": "y@y.com", "username": "newuser2", "password": "pass1234", "role": "ciudadano"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_supervisor_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.patch(
            f"{USERS_BASE}/1",
            headers=auth_headers_supervisor,
            json={"full_name": "Intruder"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_deactivate_user_supervisor_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.delete(f"{USERS_BASE}/1", headers=auth_headers_supervisor)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_permanent_supervisor_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.delete(f"{USERS_BASE}/1/permanent", headers=auth_headers_supervisor)
        assert r.status_code == status.HTTP_403_FORBIDDEN


# ═══════════════════════════════════════════════════════════════════════════════
# 3. /users/* RBAC — admin tiene acceso completo
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsersEndpointsAdminAllowed:
    """Admin tiene acceso completo (no 403)."""

    def test_list_users_admin_allowed(self, client: TestClient, auth_headers_admin: dict):
        r = client.get(f"{USERS_BASE}/", headers=auth_headers_admin)
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_admin_allowed(self, client: TestClient, auth_headers_admin: dict):
        r = client.post(
            f"{USERS_BASE}/",
            headers=auth_headers_admin,
            json={"email": "nuevo@test.com", "username": "nuevo_test", "password": "segura1234", "role": "ciudadano"},
        )
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_update_other_user_admin_allowed(
        self, client: TestClient, auth_headers_admin: dict, citizen_user: User
    ):
        r = client.patch(
            f"{USERS_BASE}/{citizen_user.id}",
            headers=auth_headers_admin,
            json={"full_name": "Updated Name"},
        )
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Role escalation — ciudadano no puede subir su propio rol
# ═══════════════════════════════════════════════════════════════════════════════

class TestRoleEscalation:
    """Ciudadano intentando escalar privilegios → 403 (require_admin bloquea antes del código)."""

    def test_citizen_cannot_escalate_own_role(
        self, client: TestClient, citizen_user: User, auth_headers_citizen: dict
    ):
        r = client.patch(
            f"{USERS_BASE}/{citizen_user.id}",
            headers=auth_headers_citizen,
            json={"role": "admin"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_citizen_cannot_escalate_to_supervisor(
        self, client: TestClient, citizen_user: User, auth_headers_citizen: dict
    ):
        r = client.patch(
            f"{USERS_BASE}/{citizen_user.id}",
            headers=auth_headers_citizen,
            json={"role": "supervisor"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_supervisor_cannot_escalate_to_admin(
        self, client: TestClient, supervisor_user: User, auth_headers_supervisor: dict
    ):
        r = client.patch(
            f"{USERS_BASE}/{supervisor_user.id}",
            headers=auth_headers_supervisor,
            json={"role": "admin"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Admin self-protection
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdminSelfProtection:
    """Admin no puede bajar su propio rol ni desactivarse a sí mismo."""

    def test_admin_cannot_downgrade_own_role(
        self, client: TestClient, admin_user: User, auth_headers_admin: dict
    ):
        r = client.patch(
            f"{USERS_BASE}/{admin_user.id}",
            headers=auth_headers_admin,
            json={"role": "supervisor"},
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST
        assert "rol" in r.json().get("detail", "").lower()

    def test_admin_cannot_deactivate_self(
        self, client: TestClient, admin_user: User, auth_headers_admin: dict
    ):
        r = client.delete(f"{USERS_BASE}/{admin_user.id}", headers=auth_headers_admin)
        assert r.status_code == status.HTTP_400_BAD_REQUEST


# ═══════════════════════════════════════════════════════════════════════════════
# 6. /export/* RBAC
# ═══════════════════════════════════════════════════════════════════════════════

class TestExportCiudadanoForbidden:
    """Ciudadano recibe 403 en endpoints de exportación (SUPERVISOR+)."""

    def test_export_geojson_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{EXPORT_BASE}/incidents/geojson", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_export_incidents_csv_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{EXPORT_BASE}/incidents/csv", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_export_kpis_csv_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{EXPORT_BASE}/kpis/csv", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_export_pdf_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{EXPORT_BASE}/report/pdf", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_export_status_ciudadano_allowed(self, client: TestClient, auth_headers_citizen: dict):
        """/export/status usa CurrentUser → ciudadano tiene acceso."""
        r = client.get(f"{EXPORT_BASE}/status", headers=auth_headers_citizen)
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_export_unauthenticated_401(self, client: TestClient):
        r = client.get(f"{EXPORT_BASE}/incidents/geojson")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED


class TestExportSupervisorAllowed:
    """Supervisor tiene acceso a endpoints de exportación (no 403)."""

    def test_export_geojson_supervisor_not_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.get(f"{EXPORT_BASE}/incidents/geojson", headers=auth_headers_supervisor)
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_export_csv_supervisor_not_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.get(f"{EXPORT_BASE}/incidents/csv", headers=auth_headers_supervisor)
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. /admin/settings/priority RBAC
# ═══════════════════════════════════════════════════════════════════════════════

class TestSettingsRBAC:
    """Settings de prioridad son exclusivos de ADMIN."""

    def test_get_settings_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.get(f"{SETTINGS_BASE}/priority", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_put_settings_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.put(
            f"{SETTINGS_BASE}/priority",
            headers=auth_headers_citizen,
            json={"weight_severity": 0.4},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_get_settings_supervisor_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.get(f"{SETTINGS_BASE}/priority", headers=auth_headers_supervisor)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_put_settings_supervisor_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.put(
            f"{SETTINGS_BASE}/priority",
            headers=auth_headers_supervisor,
            json={"weight_severity": 0.4},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_get_settings_admin_not_forbidden(self, client: TestClient, auth_headers_admin: dict):
        r = client.get(f"{SETTINGS_BASE}/priority", headers=auth_headers_admin)
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_settings_unauthenticated_401(self, client: TestClient):
        r = client.get(f"{SETTINGS_BASE}/priority")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED


# ═══════════════════════════════════════════════════════════════════════════════
# 8. /deduplication write ops RBAC
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeduplicationWriteRBAC:
    """Operaciones de escritura en dedup requieren SUPERVISOR+."""

    def test_rebuild_index_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.post(f"{DEDUP_BASE}/index/rebuild", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_save_index_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.post(f"{DEDUP_BASE}/index/save", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_resolve_cluster_ciudadano_forbidden(self, client: TestClient, auth_headers_citizen: dict):
        r = client.post(
            f"{DEDUP_BASE}/clusters/resolve",
            headers=auth_headers_citizen,
            json={"cluster_id": 1, "keep_report_id": 1},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_resolve_all_clusters_ciudadano_forbidden(
        self, client: TestClient, auth_headers_citizen: dict
    ):
        r = client.post(f"{DEDUP_BASE}/clusters/resolve-all", headers=auth_headers_citizen)
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_rebuild_index_supervisor_not_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.post(f"{DEDUP_BASE}/index/rebuild", headers=auth_headers_supervisor)
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_save_index_supervisor_not_forbidden(
        self, client: TestClient, auth_headers_supervisor: dict
    ):
        r = client.post(f"{DEDUP_BASE}/index/save", headers=auth_headers_supervisor)
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_dedup_stats_ciudadano_allowed(self, client: TestClient, auth_headers_citizen: dict):
        """Stats de dedup son de solo lectura → cualquier autenticado."""
        r = client.get(f"{DEDUP_BASE}/stats", headers=auth_headers_citizen)
        assert r.status_code not in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_dedup_unauthenticated_401(self, client: TestClient):
        r = client.post(f"{DEDUP_BASE}/index/rebuild")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Ownership positivo — supervisor puede ver reporte de cualquier usuario
# ═══════════════════════════════════════════════════════════════════════════════

class TestOwnershipPositive:
    """Supervisor y admin no están restringidos por ownership de reportes."""

    def test_supervisor_can_view_any_report(self, supervisor_user: User):
        """Unit test directo: supervisor puede ver reporte de otro usuario (no 403)."""
        from api.routes.reports import get_report
        from models.report import Report, DamageType, SeverityLevel, ReportStatus

        other_user_id = supervisor_user.id + 500

        mock_report = MagicMock(spec=Report)
        mock_report.id = 77
        mock_report.user_id = other_user_id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_report

        mock_supervisor = MagicMock()
        mock_supervisor.id = supervisor_user.id
        mock_supervisor.role = MagicMock()
        mock_supervisor.role.value = "supervisor"

        with MagicMock() as mock_shape_module:
            import api.routes.reports as reports_module
            original = reports_module.to_shape

            mock_point = MagicMock()
            mock_point.y = 18.47
            mock_point.x = -69.95
            reports_module.to_shape = lambda _: mock_point

            try:
                # Supervisor: no exception should be raised for ownership
                # The function may raise for other reasons (missing fields on mock)
                # but NOT HTTPException 403
                from fastapi import HTTPException
                try:
                    asyncio.run(get_report(report_id=77, db=mock_db, current_user=mock_supervisor))
                except HTTPException as e:
                    assert e.status_code != status.HTTP_403_FORBIDDEN, (
                        f"Supervisor no debe recibir 403, recibió {e.status_code}"
                    )
                except Exception:
                    pass  # Otros errores de mock son esperados
            finally:
                reports_module.to_shape = original

    def test_citizen_can_view_own_report(self, citizen_user: User):
        """Unit test directo: ciudadano SÍ puede ver su propio reporte (no 403)."""
        from api.routes.reports import get_report
        from models.report import Report

        mock_report = MagicMock(spec=Report)
        mock_report.id = 88
        mock_report.user_id = citizen_user.id  # mismo usuario

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_report

        mock_citizen = MagicMock()
        mock_citizen.id = citizen_user.id
        mock_citizen.role = MagicMock()
        mock_citizen.role.value = "ciudadano"

        import api.routes.reports as reports_module
        original = reports_module.to_shape
        mock_point = MagicMock()
        mock_point.y = 18.47
        mock_point.x = -69.95
        reports_module.to_shape = lambda _: mock_point

        try:
            from fastapi import HTTPException
            try:
                asyncio.run(get_report(report_id=88, db=mock_db, current_user=mock_citizen))
            except HTTPException as e:
                assert e.status_code != status.HTTP_403_FORBIDDEN, (
                    f"Ciudadano no debe recibir 403 en su propio reporte, recibió {e.status_code}"
                )
            except Exception:
                pass  # Otros errores de mock son esperados
        finally:
            reports_module.to_shape = original
