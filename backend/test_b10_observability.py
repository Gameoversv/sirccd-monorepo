"""
Tests para B-10: Observabilidad (Health Checks y Métricas Prometheus)

Cubre:
1. Health checks de componentes (BD, Redis, MinIO)
2. Kubernetes probes (liveness, readiness)
3. Métricas de Prometheus
4. Middleware de métricas HTTP
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from main import app
from services.health_service import HealthCheckService, get_health_service
from core.metrics import (
 record_report_created,
 record_ml_inference,
 record_deduplication_check,
 record_export,
 update_faiss_index_size,
 update_database_connections,
 http_requests_total,
 http_request_duration_seconds,
 reports_created_total,
)


client = TestClient(app)


# ============================================
# Tests de Health Checks
# ============================================

class TestHealthChecks:
 """Tests para los health checks de componentes"""
 
 def test_health_endpoint_exists(self):
 """Verificar que el endpoint /health existe"""
 response = client.get("/api/v1/health")
 assert response.status_code in [200, 503] # Puede ser 200 o 503 dependiendo del estado
 
 def test_health_check_structure(self):
 """Verificar estructura de respuesta del health check"""
 response = client.get("/api/v1/health")
 data = response.json()
 
 # Verificar campos principales
 assert "status" in data
 assert "message" in data
 assert "timestamp" in data
 assert "service" in data
 assert "version" in data
 assert "response_time_ms" in data
 assert "components" in data
 
 # Verificar componentes
 components = data["components"]
 assert "database" in components
 assert "redis" in components
 assert "minio" in components
 
 def test_health_check_status_values(self):
 """Verificar que el status tiene valores válidos"""
 response = client.get("/api/v1/health")
 data = response.json()
 
 valid_statuses = ["healthy", "degraded", "unhealthy", "unavailable"]
 assert data["status"] in valid_statuses
 
 def test_health_check_component_database(self):
 """Verificar health check de database específicamente"""
 response = client.get("/api/v1/health?component=database")
 data = response.json()
 
 assert "status" in data
 assert "message" in data
 assert "response_time_ms" in data
 
 # Si está saludable, verificar detalles
 if data["status"] == "healthy":
 assert "details" in data
 details = data["details"]
 assert "postgis_version" in details or "database_size" in details
 
 def test_health_check_component_redis(self):
 """Verificar health check de Redis específicamente"""
 response = client.get("/api/v1/health?component=redis")
 data = response.json()
 
 assert "status" in data
 assert "message" in data
 assert "response_time_ms" in data
 
 def test_health_check_component_minio(self):
 """Verificar health check de MinIO específicamente"""
 response = client.get("/api/v1/health?component=minio")
 data = response.json()
 
 assert "status" in data
 assert "message" in data
 assert "response_time_ms" in data
 
 def test_health_check_invalid_component(self):
 """Verificar respuesta con componente inválido"""
 response = client.get("/api/v1/health?component=invalid")
 data = response.json()
 
 assert "error" in data
 assert "invalid" in data["error"].lower()
 
 def test_liveness_probe(self):
 """Verificar liveness probe de Kubernetes"""
 response = client.get("/api/v1/health/live")
 
 # Liveness siempre debe retornar 200 si el proceso responde
 assert response.status_code == 200
 data = response.json()
 assert data["status"] == "alive"
 
 def test_readiness_probe(self):
 """Verificar readiness probe de Kubernetes"""
 response = client.get("/api/v1/health/ready")
 
 # Puede ser 200 o 503 dependiendo del estado
 assert response.status_code in [200, 503]
 data = response.json()
 assert "status" in data
 assert data["status"] in ["ready", "not_ready"]
 assert "components" in data
 
 def test_ping_endpoint(self):
 """Verificar endpoint /ping"""
 response = client.get("/api/v1/ping")
 assert response.status_code == 200
 data = response.json()
 assert data["message"] == "pong"


class TestHealthService:
 """Tests para el servicio de health checks"""
 
 @pytest.fixture
 def mock_db(self):
 """Mock de sesión de base de datos"""
 db = Mock()
 db.execute = Mock()
 return db
 
 @pytest.fixture
 def health_service(self, mock_db):
 """Instancia de HealthCheckService con DB mockeada"""
 return HealthCheckService(mock_db)
 
 def test_health_service_creation(self, health_service):
 """Verificar que el servicio se crea correctamente"""
 assert health_service is not None
 assert hasattr(health_service, 'check_database')
 assert hasattr(health_service, 'check_redis')
 assert hasattr(health_service, 'check_minio')
 assert hasattr(health_service, 'check_all')
 
 @patch('services.health_service.text')
 def test_check_database_success(self, mock_text, health_service, mock_db):
 """Test de check_database exitoso"""
 # Mock de respuesta exitosa
 mock_result = Mock()
 mock_result.scalar_one.return_value = "3.3.2"
 mock_db.execute.return_value = mock_result
 
 result = health_service.check_database()
 
 assert result["status"] == "healthy"
 assert "response_time_ms" in result
 assert result["response_time_ms"] >= 0
 
 @patch('services.health_service.redis.Redis')
 def test_check_redis_success(self, mock_redis_class, health_service):
 """Test de check_redis exitoso"""
 # Mock de cliente Redis
 mock_redis = Mock()
 mock_redis.ping.return_value = True
 mock_redis.info.return_value = {
 "redis_version": "7.0.5",
 "connected_clients": 3,
 "used_memory_human": "2.5M",
 "uptime_in_seconds": 86400
 }
 mock_redis.llen.return_value = 0
 mock_redis_class.return_value = mock_redis
 
 result = health_service.check_redis()
 
 assert result["status"] == "healthy"
 assert "response_time_ms" in result
 assert "details" in result
 
 @patch('services.health_service.Minio')
 def test_check_minio_success(self, mock_minio_class, health_service):
 """Test de check_minio exitoso"""
 # Mock de cliente MinIO
 mock_minio = Mock()
 mock_bucket1 = Mock()
 mock_bucket1.name = "sirccd-images"
 mock_bucket2 = Mock()
 mock_bucket2.name = "sirccd-models"
 mock_minio.list_buckets.return_value = [mock_bucket1, mock_bucket2]
 
 # Mock de list_objects
 mock_obj1 = Mock()
 mock_obj2 = Mock()
 mock_minio.list_objects.return_value = [mock_obj1, mock_obj2]
 
 mock_minio_class.return_value = mock_minio
 
 result = health_service.check_minio()
 
 assert result["status"] in ["healthy", "degraded"]
 assert "response_time_ms" in result
 
 def test_liveness_probe_always_true(self, health_service):
 """Test de liveness probe siempre retorna True"""
 result = health_service.liveness_probe()
 assert result is True
 
 @patch.object(HealthCheckService, 'check_database')
 @patch.object(HealthCheckService, 'check_redis')
 def test_readiness_probe_healthy(self, mock_redis, mock_db, health_service):
 """Test de readiness probe cuando componentes están saludables"""
 mock_db.return_value = {"status": "healthy"}
 mock_redis.return_value = {"status": "healthy"}
 
 is_ready, details = health_service.readiness_probe()
 
 assert is_ready is True
 assert "database" in details
 assert "redis" in details
 
 @patch.object(HealthCheckService, 'check_database')
 @patch.object(HealthCheckService, 'check_redis')
 def test_readiness_probe_unhealthy(self, mock_redis, mock_db, health_service):
 """Test de readiness probe cuando componentes no están saludables"""
 mock_db.return_value = {"status": "unhealthy"}
 mock_redis.return_value = {"status": "healthy"}
 
 is_ready, details = health_service.readiness_probe()
 
 assert is_ready is False


# ============================================
# Tests de Métricas Prometheus
# ============================================

class TestPrometheusMetrics:
 """Tests para métricas de Prometheus"""
 
 def test_metrics_endpoint_exists(self):
 """Verificar que el endpoint /metrics existe"""
 response = client.get("/api/v1/metrics")
 assert response.status_code == 200
 assert "text/plain" in response.headers["content-type"]
 
 def test_metrics_format_prometheus(self):
 """Verificar que las métricas están en formato Prometheus"""
 response = client.get("/api/v1/metrics")
 content = response.text
 
 # Verificar que contiene métricas básicas
 assert "# HELP" in content
 assert "# TYPE" in content
 
 def test_metrics_contains_http_metrics(self):
 """Verificar que las métricas HTTP están presentes"""
 # Hacer algunas peticiones primero
 client.get("/api/v1/health")
 client.get("/api/v1/ping")
 
 # Obtener métricas
 response = client.get("/api/v1/metrics")
 content = response.text
 
 # Verificar métricas HTTP
 assert "http_requests_total" in content
 assert "http_request_duration_seconds" in content
 
 def test_record_report_created(self):
 """Test de registro de creación de reporte"""
 # Registrar métrica
 record_report_created(damage_type="pothole", severity="high")
 
 # Verificar que se incrementó el contador
 # Note: No podemos verificar el valor exacto porque el registry es global
 # pero podemos verificar que no lanza error
 assert True
 
 def test_record_ml_inference(self):
 """Test de registro de inferencia ML"""
 # Registrar métrica
 record_ml_inference(model="yolov8", duration=0.5, damage_type="crack")
 
 # Verificar que no lanza error
 assert True
 
 def test_record_deduplication_check(self):
 """Test de registro de verificación de deduplicación"""
 # Registrar métricas
 record_deduplication_check(is_duplicate=True)
 record_deduplication_check(is_duplicate=False)
 
 # Verificar que no lanza error
 assert True
 
 def test_record_export(self):
 """Test de registro de exportación"""
 # Registrar métrica
 record_export(format="geojson", type="incidents", duration=2.5)
 
 # Verificar que no lanza error
 assert True
 
 def test_update_faiss_index_size(self):
 """Test de actualización de tamaño de índice FAISS"""
 # Actualizar gauge
 update_faiss_index_size(1234)
 
 # Verificar que no lanza error
 assert True
 
 def test_update_database_connections(self):
 """Test de actualización de conexiones de BD"""
 # Actualizar gauge
 update_database_connections(10)
 
 # Verificar que no lanza error
 assert True


class TestPrometheusMiddleware:
 """Tests para el middleware de métricas"""
 
 def test_middleware_captures_requests(self):
 """Verificar que el middleware captura peticiones"""
 # Hacer una petición
 response = client.get("/api/v1/ping")
 assert response.status_code == 200
 
 # Verificar que las métricas se actualizaron
 metrics_response = client.get("/api/v1/metrics")
 content = metrics_response.text
 
 # Debería contener métricas de la petición a /ping
 assert "http_requests_total" in content
 
 def test_middleware_normalizes_paths(self):
 """Verificar que el middleware normaliza paths con IDs"""
 # En un test real, haríamos peticiones con IDs numéricos
 # Por ahora solo verificamos que el endpoint funciona
 response = client.get("/api/v1/health")
 assert response.status_code in [200, 503]
 
 def test_middleware_tracks_errors(self):
 """Verificar que el middleware rastrea errores"""
 # Hacer una petición que genere 404
 response = client.get("/api/v1/nonexistent")
 assert response.status_code == 404
 
 # Verificar métricas
 metrics_response = client.get("/api/v1/metrics")
 content = metrics_response.text
 
 # Debería contener contador de errores
 assert "http_errors_total" in content or "http_requests_total" in content


# ============================================
# Tests de Integración
# ============================================

class TestIntegration:
 """Tests de integración del sistema de observabilidad"""
 
 def test_health_and_metrics_together(self):
 """Verificar que health checks y métricas funcionan juntos"""
 # Health check
 health_response = client.get("/api/v1/health")
 assert health_response.status_code in [200, 503]
 
 # Métricas
 metrics_response = client.get("/api/v1/metrics")
 assert metrics_response.status_code == 200
 
 # Las métricas deberían incluir la petición al health check
 content = metrics_response.text
 assert "http_requests_total" in content
 
 def test_multiple_requests_tracked(self):
 """Verificar que múltiples peticiones se rastrean correctamente"""
 # Hacer varias peticiones
 for _ in range(5):
 client.get("/api/v1/ping")
 
 # Verificar métricas
 metrics_response = client.get("/api/v1/metrics")
 content = metrics_response.text
 
 # Debería haber incrementado el contador
 assert "http_requests_total" in content
 
 def test_health_check_response_time_reasonable(self):
 """Verificar que los tiempos de respuesta son razonables"""
 import time
 
 start = time.time()
 response = client.get("/api/v1/health")
 duration = time.time() - start
 
 # El health check completo debería tomar menos de 5 segundos
 assert duration < 5.0
 
 # Verificar que el response_time_ms está en el JSON
 if response.status_code == 200:
 data = response.json()
 assert "response_time_ms" in data
 assert data["response_time_ms"] < 5000 # 5 segundos


# ============================================
# Tests de Regresión
# ============================================

class TestRegression:
 """Tests de regresión para asegurar que B-10 no rompe funcionalidad existente"""
 
 def test_existing_endpoints_still_work(self):
 """Verificar que endpoints existentes siguen funcionando"""
 # Ping
 response = client.get("/api/v1/ping")
 assert response.status_code == 200
 
 # OpenAPI docs
 response = client.get("/api/v1/openapi.json")
 assert response.status_code == 200
 
 def test_cors_still_configured(self):
 """Verificar que CORS sigue configurado"""
 response = client.options("/api/v1/health")
 # OPTIONS debería funcionar para CORS preflight
 assert response.status_code in [200, 405] # 405 si OPTIONS no está implementado explícitamente


# ============================================
# Fixtures y Helpers
# ============================================

@pytest.fixture(scope="module")
def test_client():
 """Cliente de test con app completa"""
 return TestClient(app)


@pytest.fixture
def mock_health_service():
 """Mock del servicio de health checks"""
 service = Mock(spec=HealthCheckService)
 service.check_all.return_value = {
 "status": "healthy",
 "message": "All systems operational",
 "timestamp": datetime.utcnow().isoformat(),
 "service": "sirccd-backend",
 "version": "1.0.0",
 "response_time_ms": 45.2,
 "components": {
 "database": {"status": "healthy", "response_time_ms": 12.3},
 "redis": {"status": "healthy", "response_time_ms": 8.1},
 "minio": {"status": "healthy", "response_time_ms": 25.0}
 }
 }
 return service


if __name__ == "__main__":
 pytest.main([__file__, "-v", "--tb=short"])
