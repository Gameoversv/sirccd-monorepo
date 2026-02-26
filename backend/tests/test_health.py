"""
Test Health Check Endpoint
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test del endpoint /health"""
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
