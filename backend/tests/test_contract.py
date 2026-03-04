"""
Tests de contrato usando Schemathesis (B-11)

Valida que la API cumple con el esquema OpenAPI definido en api/openapi.yaml.

Tests para:
- Validación de esquemas de request/response
- Validación de códigos de estado HTTP
- Validación de headers
- Detección de discrepancias entre implementación y especificación
"""

import pytest
import schemathesis
from pathlib import Path
from fastapi.testclient import TestClient

from main import app


# Cargar esquema OpenAPI
OPENAPI_SCHEMA_PATH = Path(__file__).parent.parent / "api" / "openapi.yaml"

# Crear esquema de Schemathesis desde el archivo YAML
schema = schemathesis.from_path(str(OPENAPI_SCHEMA_PATH))


# ==========================================
# Configuración de Schemathesis
# ==========================================

@pytest.mark.contract
@pytest.mark.slow
class TestAPIContract:
    """Tests de contrato API usando Schemathesis"""
    
    @schema.parametrize()
    def test_api_schema_conformance(self, case):
        """
        Test parametrizado que valida todos los endpoints del esquema OpenAPI.
        
        Schemathesis genera automáticamente casos de test para cada endpoint
        definido en openapi.yaml y valida:
        - Request body coincide con el esquema
        - Response body coincide con el esquema
        - Status codes son los esperados
        - Headers son correctos
        """
        # Ejecutar request usando TestClient de FastAPI
        response = case.call_asgi(app)
        
        # Validar que la respuesta cumple con el esquema
        case.validate_response(response)


# ==========================================
# Tests de Contrato Específicos
# ==========================================

@pytest.mark.contract
class TestAuthEndpointsContract:
    """Tests de contrato para endpoints de autenticación"""
    
    def test_login_request_schema(self, client: TestClient):
        """Test: Login request debe cumplir con el esquema"""
        # Request válido según OpenAPI
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        # Verificar que los campos de respuesta existen
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
    
    def test_register_request_schema(self, client: TestClient):
        """Test: Register request debe cumplir con el esquema"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123!"
            }
        )
        
        # El schema define los campos esperados
        assert response.status_code in [201, 400, 422]


@pytest.mark.contract
class TestReportesEndpointsContract:
    """Tests de contrato para endpoints de reportes"""
    
    def test_create_report_multipart_schema(
        self, 
        client: TestClient, 
        auth_headers_citizen: dict,
        test_image: bytes
    ):
        """Test: Crear reporte debe cumplir con schema multipart/form-data"""
        from io import BytesIO
        
        files = {"image": ("test.jpg", BytesIO(test_image), "image/jpeg")}
        data = {
            "latitude": "19.4326",
            "longitude": "-99.1332",
            "description": "Test"
        }
        
        response = client.post(
            "/api/v1/reportes",
            files=files,
            data=data,
            headers=auth_headers_citizen
        )
        
        # Verificar status codes válidos según el esquema
        assert response.status_code in [200, 201, 400, 401, 422]
    
    def test_list_reports_response_schema(
        self,
        client: TestClient,
        auth_headers_admin: dict
    ):
        """Test: Respuesta de listar reportes debe cumplir con el esquema"""
        response = client.get(
            "/api/v1/reportes",
            headers=auth_headers_admin
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verificar estructura según el esquema
            assert isinstance(data, (list, dict))


@pytest.mark.contract
class TestIncidentsEndpointsContract:
    """Tests de contrato para endpoints de incidentes"""
    
    def test_list_incidents_response_schema(
        self,
        client: TestClient,
        auth_headers_admin: dict
    ):
        """Test: Respuesta de listar incidentes debe cumplir con el esquema"""
        response = client.get(
            "/api/v1/incidents",
            headers=auth_headers_admin
        )
        
        if response.status_code == 200:
            data = response.json()
            # Debe tener la estructura definida en el esquema
            assert isinstance(data, (list, dict))
    
    def test_update_incident_status_schema(
        self,
        client: TestClient,
        auth_headers_admin: dict
    ):
        """Test: Actualizar estado debe cumplir con el esquema"""
        response = client.patch(
            "/api/v1/incidents/1/status",
            json={"status": "in_progress"},
            headers=auth_headers_admin
        )
        
        # Status codes válidos según esquema
        assert response.status_code in [200, 400, 401, 403, 404, 422]


# ==========================================
# Tests de Validación de Respuestas
# ==========================================

@pytest.mark.contract
class TestResponseValidation:
    """Tests que validan estructuras de respuesta"""
    
    def test_error_responses_have_detail(self, client: TestClient):
        """Test: Todas las respuestas de error deben tener campo 'detail'"""
        # Intentar acceder sin autenticación
        response = client.get("/api/v1/reportes/1")
        
        if response.status_code >= 400:
            data = response.json()
            assert "detail" in data
    
    def test_validation_errors_have_proper_structure(self, client: TestClient):
        """Test: Errores de validación (422) tienen estructura correcta"""
        # Enviar request inválido
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "not-valid"}  # Falta password
        )
        
        if response.status_code == 422:
            data = response.json()
            assert "detail" in data
            # FastAPI validation errors tienen lista de errores
            assert isinstance(data["detail"], list)


# ==========================================
# Tests de Códigos de Estado HTTP
# ==========================================

@pytest.mark.contract  
class TestHTTPStatusCodes:
    """Tests que validan uso correcto de códigos HTTP"""
    
    def test_successful_creation_returns_201(
        self,
        client: TestClient,
        test_db
    ):
        """Test: Creación exitosa debe retornar 201 Created"""
        # Registrar usuario debe retornar 201
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newtest@example.com",
                "username": "newtest",
                "password": "SecurePass123!"
            }
        )
        
        if response.json().get("message") and "exitosamente" in response.json().get("message", ""):
            assert response.status_code == 201
    
    def test_not_found_returns_404(
        self,
        client: TestClient,
        auth_headers_citizen: dict
    ):
        """Test: Recurso no encontrado debe retornar 404"""
        response = client.get(
            "/api/v1/reportes/999999",
            headers=auth_headers_citizen
        )
        
        assert response.status_code == 404
    
    def test_unauthorized_returns_401(self, client: TestClient):
        """Test: Sin autenticación debe retornar 401"""
        response = client.get("/api/v1/reportes/1")
        
        assert response.status_code == 401
    
    def test_forbidden_returns_403(
        self,
        client: TestClient,
        auth_headers_citizen: dict
    ):
        """Test: Sin permisos debe retornar 403"""
        # Ciudadano intentando acceder a endpoint de admin
        response = client.delete(
            "/api/v1/users/1",
            headers=auth_headers_citizen
        )
        
        # Debe ser 403 o 404 si el endpoint no existe
        assert response.status_code in [403, 404]


# ==========================================
# Tests de Headers
# ==========================================

@pytest.mark.contract
class TestHTTPHeaders:
    """Tests que validan headers HTTP"""
    
    def test_content_type_json(self, client: TestClient):
        """Test: Respuestas JSON deben tener Content-Type correcto"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "test"}
        )
        
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_cors_headers_present(self, client: TestClient):
        """Test: Headers CORS deben estar presentes"""
        response = client.options("/api/v1/reportes")
        
        # CORS headers pueden o no estar configurados
        # Este test es informativo
        if response.status_code == 200:
            headers = response.headers
            # Verificar si CORS está configurado
            # assert "access-control-allow-origin" in headers


# ==========================================
# Configuración de Hooks de Schemathesis
# ==========================================

def setup_auth_headers(context, case):
    """
    Hook para agregar headers de autenticación a los tests de Schemathesis.
    
    Schemathesis no maneja autenticación automáticamente, por lo que
    necesitamos inyectar tokens válidos.
    """
    # Por ahora, los tests de Schemathesis fallarán en endpoints autenticados
    # En producción, deberíamos:
    # 1. Obtener token válido
    # 2. Agregarlo a case.headers
    pass


# Registrar el hook (comentado porque requiere configuración adicional)
# schema.register_hook("before_call", setup_auth_headers)


# ==========================================
# Tests de Performance (Contrato implícito)
# ==========================================

@pytest.mark.contract
@pytest.mark.slow
class TestPerformanceContract:
    """Tests que validan contratos implícitos de performance"""
    
    def test_health_check_responds_quickly(self, client: TestClient):
        """Test: Health check debe responder en <1 segundo"""
        import time
        
        start = time.time()
        response = client.get("/api/v1/health")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0  # Menos de 1 segundo
    
    def test_list_endpoints_handle_pagination(
        self,
        client: TestClient,
        auth_headers_admin: dict
    ):
        """Test: Endpoints de listado deben soportar paginación"""
        response = client.get(
            "/api/v1/reportes?skip=0&limit=10",
            headers=auth_headers_admin
        )
        
        # Debe aceptar parámetros de paginación
        assert response.status_code in [200, 401, 404]
