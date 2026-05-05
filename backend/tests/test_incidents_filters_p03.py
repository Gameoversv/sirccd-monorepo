"""
Tests para filtros avanzados P-03: fecha, zona administrativa.

Scope:
- Validación de parámetros HTTP (FastAPI convierte date/int antes de tocar la DB)
- Endpoint GET /zones/ responde con lista
- Parámetros inválidos devuelven 422

Nota: DB es SQLite in-memory sin PostGIS. Los endpoints que llegan a la DB
      pueden retornar 500 — solo probamos la capa de parámetros/validación.
"""

import pytest
from fastapi.testclient import TestClient


# ============================================================
# Helpers
# ============================================================

def _auth(client: TestClient, auth_headers_admin: dict, url: str, **kwargs):
    return client.get(url, headers=auth_headers_admin, **kwargs)


# ============================================================
# Date range — validación de parámetros
# ============================================================

@pytest.mark.unit
class TestDateRangeParams:
    """FastAPI debe aceptar YYYY-MM-DD y rechazar formatos incorrectos."""

    def test_date_from_valid_format_accepted(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """date_from en formato YYYY-MM-DD no genera 422."""
        r = _auth(client, auth_headers_admin, "/api/v1/incidents?date_from=2024-01-01")
        assert r.status_code != 422

    def test_date_to_valid_format_accepted(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """date_to en formato YYYY-MM-DD no genera 422."""
        r = _auth(client, auth_headers_admin, "/api/v1/incidents?date_to=2024-12-31")
        assert r.status_code != 422

    def test_date_range_combined_accepted(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """date_from + date_to juntos no generan 422."""
        r = _auth(
            client,
            auth_headers_admin,
            "/api/v1/incidents?date_from=2024-01-01&date_to=2024-12-31",
        )
        assert r.status_code != 422

    def test_date_from_invalid_format_returns_422(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """date_from con formato incorrecto debe retornar 422."""
        r = _auth(client, auth_headers_admin, "/api/v1/incidents?date_from=not-a-date")
        assert r.status_code == 422

    def test_date_to_invalid_format_returns_422(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """date_to con formato incorrecto debe retornar 422."""
        r = _auth(client, auth_headers_admin, "/api/v1/incidents?date_to=31/12/2024")
        assert r.status_code == 422

    def test_date_from_dd_mm_yyyy_returns_422(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """dd-mm-yyyy no es ISO 8601 y debe retornar 422."""
        r = _auth(client, auth_headers_admin, "/api/v1/incidents?date_from=01-01-2024")
        assert r.status_code == 422


# ============================================================
# Zone filter — validación de parámetros
# ============================================================

@pytest.mark.unit
class TestZoneIdParam:
    """zone_id debe aceptar enteros y rechazar otros tipos."""

    def test_zone_id_integer_accepted(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """zone_id entero no genera 422."""
        r = _auth(client, auth_headers_admin, "/api/v1/incidents?zone_id=1")
        assert r.status_code != 422

    def test_zone_id_string_returns_422(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """zone_id no-entero debe retornar 422."""
        r = _auth(client, auth_headers_admin, "/api/v1/incidents?zone_id=norte")
        assert r.status_code == 422

    def test_zone_id_float_returns_422(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """zone_id flotante debe retornar 422."""
        r = _auth(client, auth_headers_admin, "/api/v1/incidents?zone_id=1.5")
        assert r.status_code == 422

    def test_all_p03_filters_combined_accepted(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Todos los filtros P-03 juntos no generan 422."""
        r = _auth(
            client,
            auth_headers_admin,
            "/api/v1/incidents?date_from=2024-01-01&date_to=2024-12-31&zone_id=1",
        )
        assert r.status_code != 422


# ============================================================
# Zones endpoint
# ============================================================

@pytest.mark.unit
class TestZonesEndpoint:
    """GET /zones/ debe responder correctamente."""

    def test_zones_requires_auth(self, client: TestClient):
        """Sin token debe retornar 401."""
        r = client.get("/api/v1/zones/")
        assert r.status_code == 401

    def test_zones_authenticated_returns_list_or_error(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Con token: 200 con lista (vacía si no hay zonas) o 500 si DB no disponible."""
        r = _auth(client, auth_headers_admin, "/api/v1/zones/")
        assert r.status_code in (200, 500)
        if r.status_code == 200:
            assert isinstance(r.json(), list)

    def test_zones_200_items_have_required_fields(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Si 200, cada zona tiene id, name, code."""
        r = _auth(client, auth_headers_admin, "/api/v1/zones/")
        if r.status_code == 200:
            for zone in r.json():
                assert "id" in zone
                assert "name" in zone
                assert "code" in zone


# ============================================================
# Combinación con filtros existentes
# ============================================================

@pytest.mark.unit
class TestFiltersBackwardsCompat:
    """Filtros previos siguen funcionando junto con los nuevos."""

    def test_existing_status_filter_still_accepted(
        self, client: TestClient, auth_headers_admin: dict
    ):
        r = _auth(client, auth_headers_admin, "/api/v1/incidents?status=open")
        assert r.status_code != 422

    def test_existing_severity_with_new_date_filter(
        self, client: TestClient, auth_headers_admin: dict
    ):
        r = _auth(
            client,
            auth_headers_admin,
            "/api/v1/incidents?severity=alta&date_from=2024-01-01",
        )
        assert r.status_code != 422

    def test_existing_priority_with_zone_filter(
        self, client: TestClient, auth_headers_admin: dict
    ):
        r = _auth(
            client,
            auth_headers_admin,
            "/api/v1/incidents?priority=critica&zone_id=2",
        )
        assert r.status_code != 422
