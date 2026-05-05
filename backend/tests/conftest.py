"""
Configuración global de pytest para los tests del backend.

Proporciona fixtures compartidas para:
- Base de datos de test (SQLite en memoria)
- Cliente HTTP de test
- Usuarios de test con diferentes roles
- Mocks de servicios externos (MinIO, Redis, ML)
"""

import os
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Configurar variables de entorno para evitar conexiones reales en tests
os.environ["TESTING"] = "true"
os.environ["REDIS_HOST"] = "mock_redis"
os.environ["POSTGRES_HOST"] = "mock_postgres"
os.environ["MINIO_ENDPOINT"] = "mock_minio"

# Forzar stdout/stderr a UTF-8 para evitar UnicodeEncodeError con emojis en Windows
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Agregar el directorio backend al path para imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Mockear servicios que se inicializan al importar
# Necesitamos mockear antes de importar para evitar que se inicialicen los servicios
sys.modules['services.anonymizer'] = MagicMock()
sys.modules['services.storage'] = MagicMock()
sys.modules['services.ml_service'] = MagicMock()
sys.modules['services.queue_service'] = MagicMock()

# boto3 is not in requirements (MinIO client uses minio-py), stub it out
if 'boto3' not in sys.modules:
    sys.modules['boto3'] = MagicMock()

with patch('redis.Redis'):
    from main import app
from db.base import Base
from db.session import get_db
from models.user import User, UserRole
from core.security import get_password_hash, create_access_token


# ==========================================
# Base de Datos de Test
# ==========================================

# Usar SQLite en memoria para tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override de la dependencia de base de datos para tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# ==========================================
# Fixtures de Base de Datos
# ==========================================

@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    Fixture que proporciona una sesión de base de datos de test limpia.
    
    Crea todas las tablas before del test y las destruye después.
    Útil para tests que necesitan acceso directo a la DB.
    """
    # Crear solo la tabla users (sin tablas que usan PostGIS/geography)
    # Para SQLite in-memory, evitamos crear tablas con tipos PostGIS incompatibles
    User.__table__.create(bind=engine, checkfirst=True)
    
    # Proporcionar sesión
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Limpiar solo la tabla users 
        User.__table__.drop(bind=engine, checkfirst=True)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """
    Fixture que proporciona un cliente HTTP de test con DB configurada.
    
    Override la dependencia de DB para usar la DB de test.
    """
    app.dependency_overrides[get_db] = override_get_db
    
    # Usar raise_server_exceptions=False para manejar errores de startup en tests
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    
    # Limpiar overrides
    app.dependency_overrides.clear()


# ==========================================
# Fixtures de Usuarios
# ==========================================

@pytest.fixture
def admin_user(test_db: Session) -> User:
    """Crea un usuario administrador de test"""
    user = User(
        email="admin@test.com",
        username="admin_test",
        full_name="Admin Test",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def citizen_user(test_db: Session) -> User:
    """Crea un usuario ciudadano de test"""
    user = User(
        email="citizen@test.com",
        username="citizen_test",
        full_name="Citizen Test",
        hashed_password=get_password_hash("citizen123"),
        role=UserRole.CIUDADANO,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def inactive_user(test_db: Session) -> User:
    """Crea un usuario inactivo de test"""
    user = User(
        email="inactive@test.com",
        username="inactive_test",
        full_name="Inactive Test",
        hashed_password=get_password_hash("inactive123"),
        role=UserRole.CIUDADANO,
        is_active=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


# ==========================================
# Fixtures de Autenticación
# ==========================================

@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Genera token JWT para usuario admin"""
    return create_access_token(
        subject=admin_user.id,
        additional_claims={"role": admin_user.role.value, "username": admin_user.username}
    )


@pytest.fixture
def citizen_token(citizen_user: User) -> str:
    """Genera token JWT para usuario ciudadano"""
    return create_access_token(
        subject=citizen_user.id,
        additional_claims={"role": citizen_user.role.value, "username": citizen_user.username}
    )


@pytest.fixture
def auth_headers_admin(admin_token: str) -> dict:
    """Headers HTTP con autenticación de admin"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers_citizen(citizen_token: str) -> dict:
    """Headers HTTP con autenticación de ciudadano"""
    return {"Authorization": f"Bearer {citizen_token}"}


# ==========================================
# Mocks de Servicios Externos
# ==========================================

@pytest.fixture
def mock_minio_storage():
    """Mock del servicio de almacenamiento MinIO"""
    mock = MagicMock()
    mock.upload_image.return_value = "http://minio/test/image.jpg"
    mock.delete_image.return_value = True
    mock.get_image_url.return_value = "http://minio/test/image.jpg"
    return mock


@pytest.fixture
def mock_redis_cache():
    """Mock del servicio de caché Redis"""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_ml_service():
    """Mock del servicio de ML/detección"""
    mock = MagicMock()
    mock.detect_damage.return_value = {
        "damage_type": "bache",
        "severity": "media",
        "confidence": 0.85,
        "bbox": [100, 100, 200, 200]
    }
    mock.is_available.return_value = True
    return mock


@pytest.fixture
def mock_queue_service():
    """Mock del servicio de cola RQ"""
    mock = MagicMock()
    mock.enqueue.return_value = "job_123"
    mock.get_job_status.return_value = "completed"
    return mock


# ==========================================
# Fixtures de Datos de Test
# ==========================================

@pytest.fixture
def sample_report_data() -> dict:
    """Datos de ejemplo para crear un reporte"""
    return {
        "latitude": 19.4326,
        "longitude": -99.1332,
        "description": "Bache grande en Av. Principal",
        "damage_type": "bache",
        "severity": "alta"
    }


@pytest.fixture
def sample_incident_data() -> dict:
    """Datos de ejemplo para crear un incidente"""
    return {
        "latitude": 19.4326,
        "longitude": -99.1332,
        "damage_type": "grieta",
        "severity": "media",
        "confidence": 0.89,
        "status": "pending"
    }


# ==========================================
# Configuración de Entorno de Test
# ==========================================

@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Configura variables de entorno para tests"""
    os.environ["TESTING"] = "true"
    os.environ["SECRET_KEY"] = "test_secret_key_for_jwt_tokens"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["MINIO_ENDPOINT"] = "localhost:9000"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    yield
    
    # Limpiar después de todos los tests
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


# ==========================================
# Helpers para Tests
# ==========================================

def create_test_image() -> bytes:
    """
    Crea una imagen de test simple en memoria (1x1 pixel PNG)
    
    Returns:
        bytes: Contenido binario de imagen PNG
    """
    import io
    from PIL import Image
    
    img = Image.new('RGB', (1, 1), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.read()


@pytest.fixture
def test_image() -> bytes:
    """Fixture que proporciona una imagen de test"""
    return create_test_image()


# ==========================================
# Markers de Pytest
# ==========================================

def pytest_configure(config):
    """Registrar markers personalizados de pytest"""
    config.addinivalue_line(
        "markers", "unit: marca test como test unitario"
    )
    config.addinivalue_line(
        "markers", "integration: marca test como test de integración"
    )
    config.addinivalue_line(
        "markers", "contract: marca test como test de contrato/esquema"
    )
    config.addinivalue_line(
        "markers", "slow: marca test como lento (>1s)"
    )
    config.addinivalue_line(
        "markers", "auth: tests relacionados con autenticación"
    )
    config.addinivalue_line(
        "markers", "reports: tests relacionados con reportes"
    )
    config.addinivalue_line(
        "markers", "incidents: tests relacionados con incidentes"
    )
