"""
Test Health Check Endpoint
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

_HEALTHY_RESULT = {
    "status": "healthy",
    "service": "SIRCCD API",
    "version": "0.1.0",
    "timestamp": "2026-01-01T00:00:00",
    "components": {
        "database": {"status": "healthy"},
        "redis": {"status": "healthy"},
        "minio": {"status": "healthy"},
    },
}


def _mock_health_service():
    svc = MagicMock()
    svc.check_all.return_value = _HEALTHY_RESULT
    svc.check_database.return_value = {"status": "healthy"}
    svc.check_redis.return_value = {"status": "healthy"}
    svc.check_minio.return_value = {"status": "healthy"}
    svc.liveness_probe.return_value = True
    svc.readiness_probe.return_value = (True, {"status": "ready"})
    return svc


def test_health_check():
    """Test del endpoint /health"""
    with patch("api.routes.health.get_health_service", return_value=_mock_health_service()):
        response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SIRCCD API"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_ping():
    """Test del endpoint /ping"""
    response = client.get("/api/v1/ping")
    
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}


def test_docs_accessible():
    """Verificar que la documentación es accesible"""
    response = client.get("/api/v1/docs")
    assert response.status_code == 200


def test_openapi_json():
    """Verificar que el schema OpenAPI es accesible"""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "openapi" in schema
    assert schema["info"]["title"] == "SIRCCD API"
