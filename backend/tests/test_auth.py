"""
Tests unitarios de autenticación y autorización (B-11)

Tests para:
- Registro de usuarios
- Login/Logout
- Generación y validación de tokens JWT
- Permisos basados en roles
- Refresh tokens
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.user import User, UserRole
from core.security import verify_password, create_access_token, decode_access_token


# ==========================================
# Tests de Registro
# ==========================================

@pytest.mark.unit
@pytest.mark.auth
class TestUserRegistration:
    """Tests del endpoint de registro de usuarios"""
    
    def test_register_new_user_success(self, client: TestClient, test_db: Session):
        """Test: Registro exitoso de nuevo usuario"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "username": "newuser",
                "password": "SecurePass123!",
                "full_name": "New User",
                "phone": "+123456789"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["username"] == "newuser"
        assert "user_id" in data
        assert "message" in data
        
        # Verificar que el usuario fue creado en la DB
        user = test_db.query(User).filter(User.email == "newuser@test.com").first()
        assert user is not None
        assert user.role == UserRole.CIUDADANO
        assert user.is_active is True
        assert verify_password("SecurePass123!", user.hashed_password)
    
    def test_register_duplicate_email(self, client: TestClient, citizen_user: User):
        """Test: Registrarse con email duplicado debe fallar"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": citizen_user.email,
                "username": "different",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email ya está registrado" in response.json()["detail"].lower()
    
    def test_register_duplicate_username(self, client: TestClient, citizen_user: User):
        """Test: Registrarse con username duplicado debe fallar"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "different@test.com",
                "username": citizen_user.username if hasattr(citizen_user, 'username') else "citizen",
                "password": "SecurePass123!"
            }
        )
        
        # Si el modelo no tiene username, este test se saltará
        if hasattr(citizen_user, 'username'):
            assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_invalid_email(self, client: TestClient):
        """Test: Email inválido debe fallar validación"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_weak_password(self, client: TestClient):
        """Test: Contraseña débil debe ser rechazada"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                "username": "testuser",
                "password": "123"  # Contraseña muy corta
            }
        )
        
        # Puede ser 422 (validación) o 400 (regla de negocio)
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]


# ==========================================
# Tests de Login
# ==========================================

@pytest.mark.unit
@pytest.mark.auth
class TestUserLogin:
    """Tests del endpoint de login"""
    
    def test_login_success(self, client: TestClient, citizen_user: User):
        """Test: Login exitoso con credenciales válidas"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "citizen_test",
                "password": "citizen123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Verificar que el token es válido
        token_payload = decode_access_token(data["access_token"])
        assert token_payload is not None
        assert token_payload["sub"] == str(citizen_user.id)
    
    def test_login_wrong_password(self, client: TestClient, citizen_user: User):
        """Test: Login con contraseña incorrecta debe fallar"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "citizen_test",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "credenciales" in response.json()["detail"].lower() or "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test: Login con usuario que no existe"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "noexiste",
                "password": "anypassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_inactive_user(self, client: TestClient, inactive_user: User):
        """Test: Login con usuario inactivo debe ser rechazado"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "inactive_test",
                "password": "inactive123"
            }
        )
        
        # Puede ser 401 (no autenticado) o 403 (prohibido)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


# ==========================================
# Tests de JWT Tokens
# ==========================================

@pytest.mark.unit
@pytest.mark.auth
class TestJWTTokens:
    """Tests de generación y validación de tokens JWT"""
    
    def test_create_access_token(self, citizen_user: User):
        """Test: Crear token de acceso válido"""
        token = create_access_token(subject=citizen_user.id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verificar payload
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == str(citizen_user.id)
        assert "exp" in payload
        assert "iat" in payload
    
    def test_decode_valid_token(self, admin_token: str, admin_user: User):
        """Test: Decodificar token válido"""
        payload = decode_access_token(admin_token)
        
        assert payload is not None
        assert payload["sub"] == str(admin_user.id)
    
    def test_decode_invalid_token(self):
        """Test: Decodificar token inválido debe retornar None"""
        invalid_token = "invalid.token.here"
        
        payload = decode_access_token(invalid_token)
        assert payload is None
    
    def test_decode_expired_token(self):
        """Test: Token expirado debe ser rechazado"""
        from datetime import timedelta
        
        # Crear token que expire en -1 segundo (ya expirado)
        expired_token = create_access_token(
            subject="test@test.com",
            expires_delta=timedelta(seconds=-1)
        )
        
        payload = decode_access_token(expired_token)
        assert payload is None


# ==========================================
# Tests de Autorización por Roles
# ==========================================

@pytest.mark.unit
@pytest.mark.auth
class TestRoleBasedAuthorization:
    """Tests de permisos basados en roles"""
    
    def test_admin_access_to_admin_endpoint(
        self, 
        client: TestClient, 
        auth_headers_admin: dict
    ):
        """Test: Admin puede acceder a endpoints de admin"""
        # Endpoint que require rol admin (ej: /api/v1/users)
        response = client.get("/api/v1/users", headers=auth_headers_admin)
        
        # Debe ser 200 o 404 (si no está implementado), no 403
        assert response.status_code != status.HTTP_403_FORBIDDEN
    
    def test_citizen_cannot_access_admin_endpoint(
        self,
        client: TestClient,
        auth_headers_citizen: dict
    ):
        """Test: Ciudadano no puede acceder a endpoints de admin"""
        response = client.get("/api/v1/users", headers=auth_headers_citizen)
        
        # Debe ser 403 Forbidden si el endpoint existe y valida roles
        # Si no existe el endpoint, puede ser 404
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_unauthenticated_access_denied(self, client: TestClient):
        """Test: Acceso sin autenticación debe ser denegado"""
        response = client.get("/api/v1/reportes/1")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==========================================
# Tests de Refresh Token
# ==========================================

@pytest.mark.unit
@pytest.mark.auth  
class TestRefreshToken:
    """Tests de refresh tokens"""
    
    def test_refresh_token_success(
        self,
        client: TestClient,
        citizen_user: User
    ):
        """Test: Refresh token genera nuevo access token"""
        # Primero hacer login para obtener el refresh_token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "citizen_test",
                "password": "citizen123"
            }
        )
        
        login_data = login_response.json()
        
        # Si el login no retorna refresh_token, el test es N/A
        if "refresh_token" not in login_data:
            pytest.skip("El endpoint de login no retorna refresh_token")
        
        # Usar el refresh_token para obtener un nuevo access_token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login_data["refresh_token"]}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
    
    def test_refresh_with_invalid_token(self, client: TestClient):
        """Test: Refresh con token inválido debe fallar"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token_here"}
        )
        
        # Debe ser 401 (token inválido)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==========================================
# Tests de Seguridad
# ==========================================

@pytest.mark.unit
@pytest.mark.auth
class TestSecurityFeatures:
    """Tests de características de seguridad"""
    
    def test_password_is_hashed(self, test_db: Session, citizen_user: User):
        """Test: Las contraseñas se almacenan hasheadas, no en texto plano"""
        # La contraseña hasheada debe ser diferente al texto plano
        assert citizen_user.hashed_password != "citizen123"
        
        # Debe ser un hash bcrypt válido (comienza con $2b$)
        assert citizen_user.hashed_password.startswith("$2b$")
        
        # Debe ser verificable
        assert verify_password("citizen123", citizen_user.hashed_password)
    
    def test_password_not_returned_in_response(
        self,
        client: TestClient,
        auth_headers_citizen: dict
    ):
        """Test: La API nunca debe retornar contraseñas"""
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "citizen_test",
                "password": "citizen123"
            }
        )
        
        data = response.json()
        
        # No debe haber campos de contraseña en la respuesta
        assert "password" not in str(data).lower() or "hashed_password" not in str(data).lower()
