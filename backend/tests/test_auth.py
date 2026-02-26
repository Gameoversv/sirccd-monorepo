"""
Tests de autenticación y autorización
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from db.base import Base
from db.session import get_db
from models.user import User, UserRole
from core.security import get_password_hash


# Configurar base de datos de prueba en memoria
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la dependencia de base de datos para tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Fixture para crear/destruir base de datos de test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(test_db):
    """Fixture para crear un usuario de prueba"""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        role=UserRole.CIUDADANO,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture(scope="function")
def test_admin(test_db):
    """Fixture para crear un usuario admin de prueba"""
    db = TestingSessionLocal()
    admin = User(
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        hashed_password=get_password_hash("adminpassword123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    return admin


@pytest.fixture(scope="function")
def test_brigada(test_db):
    """Fixture para crear un usuario brigada de prueba"""
    db = TestingSessionLocal()
    brigada = User(
        email="brigada@example.com",
        username="brigadauser",
        full_name="Brigada User",
        hashed_password=get_password_hash("brigadapass123"),
        role=UserRole.BRIGADA,
        is_active=True,
        is_verified=True
    )
    db.add(brigada)
    db.commit()
    db.refresh(brigada)
    db.close()
    return brigada


def get_auth_headers(username: str, password: str) -> dict:
    """Helper para obtener headers de autenticación"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Tests de registro

def test_register_user_success(test_db):
    """Test: Registro exitoso de usuario"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepass123",
            "full_name": "New User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "message" in data


def test_register_duplicate_email(test_user):
    """Test: Registro con email duplicado debe fallar"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",  # Email ya existe
            "username": "differentuser",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_register_duplicate_username(test_user):
    """Test: Registro con username duplicado debe fallar"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "different@example.com",
            "username": "testuser",  # Username ya existe
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "usuario" in response.json()["detail"].lower()


def test_register_weak_password(test_db):
    """Test: Registro con contraseña débil debe fallar"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "123"  # Muy corta
        }
    )
    assert response.status_code == 422  # Validation error


# Tests de login

def test_login_success(test_user):
    """Test: Login exitoso con credenciales correctas"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"] == test_user.id
    assert data["username"] == test_user.username
    assert data["role"] == test_user.role.value


def test_login_with_email(test_user):
    """Test: Login usando email en lugar de username"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "test@example.com",  # Usar email
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(test_user):
    """Test: Login con contraseña incorrecta debe fallar"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "credenciales" in response.json()["detail"].lower()


def test_login_nonexistent_user(test_db):
    """Test: Login con usuario inexistente debe fallar"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent",
            "password": "password123"
        }
    )
    assert response.status_code == 401


def test_login_inactive_user(test_db):
    """Test: Login con usuario inactivo debe fallar"""
    db = TestingSessionLocal()
    inactive_user = User(
        email="inactive@example.com",
        username="inactive",
        hashed_password=get_password_hash("password123"),
        role=UserRole.CIUDADANO,
        is_active=False  # Usuario inactivo
    )
    db.add(inactive_user)
    db.commit()
    db.close()
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "inactive",
            "password": "password123"
        }
    )
    assert response.status_code == 403
    assert "inactivo" in response.json()["detail"].lower()


# Tests de /me endpoint

def test_get_current_user_info(test_user):
    """Test: Obtener información del usuario autenticado"""
    headers = get_auth_headers("testuser", "testpassword123")
    response = client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert "hashed_password" not in data  # Password no debe estar en respuesta


def test_get_current_user_no_token(test_db):
    """Test: Acceder a /me sin token debe fallar"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(test_db):
    """Test: Acceder a /me con token inválido debe fallar"""
    headers = {"Authorization": "Bearer invalid_token_12345"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


# Tests de verificación de token

def test_verify_token_valid(test_user):
    """Test: Verificar un token válido"""
    headers = get_auth_headers("testuser", "testpassword123")
    token = headers["Authorization"].split(" ")[1]
    
    response = client.post(
        "/api/v1/auth/verify-token",
        params={"token": token}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["user_id"] == test_user.id
    assert data["role"] == test_user.role.value


def test_verify_token_invalid(test_db):
    """Test: Verificar un token inválido"""
    response = client.post(
        "/api/v1/auth/verify-token",
        params={"token": "invalid_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


# Tests de logout

def test_logout(test_user):
    """Test: Logout exitoso"""
    headers = get_auth_headers("testuser", "testpassword123")
    response = client.post("/api/v1/auth/logout", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["username"] == test_user.username


# Tests de OAuth2 endpoint

def test_login_oauth2_format(test_user):
    """Test: Login con formato OAuth2"""
    response = client.post(
        "/api/v1/auth/login/oauth2",
        data={  # OAuth2 usa form data, no JSON
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# Tests de autorización por roles

def test_admin_access_allowed(test_admin):
    """Test: Usuario admin puede acceder a endpoints protegidos"""
    headers = get_auth_headers("admin", "adminpassword123")
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["role"] == UserRole.ADMIN.value


def test_brigada_access_allowed(test_brigada):
    """Test: Usuario brigada puede autenticarse"""
    headers = get_auth_headers("brigadauser", "brigadapass123")
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["role"] == UserRole.BRIGADA.value


# Tests de seguridad de password

def test_password_hashing(test_db):
    """Test: Las contraseñas se almacenan hasheadas"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "secure@example.com",
            "username": "secureuser",
            "password": "mypassword123"
        }
    )
    assert response.status_code == 201
    
    # Verificar que la contraseña en DB está hasheada
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "secureuser").first()
    assert user.hashed_password != "mypassword123"
    assert user.hashed_password.startswith("$2b$")  # bcrypt hash
    db.close()


def test_token_contains_user_info(test_user):
    """Test: El token contiene información del usuario"""
    from core.security import decode_access_token
    
    headers = get_auth_headers("testuser", "testpassword123")
    token = headers["Authorization"].split(" ")[1]
    
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == str(test_user.id)
    assert payload["role"] == test_user.role.value
    assert payload["username"] == test_user.username
