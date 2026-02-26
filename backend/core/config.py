"""
Configuración de la aplicación FastAPI
"""

from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Información del proyecto
    PROJECT_NAME: str = "SIRCCD API"
    DESCRIPTION: str = "Sistema Inteligente de Reporte Ciudadano de Calles Dañadas"
    VERSION: str = "0.1.0"
    
    # API
    API_V1_STR: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    
    # Database (PostgreSQL con PostGIS)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "sirccd_user"
    POSTGRES_PASSWORD: str = "sirccd_password"
    POSTGRES_DB: str = "sirccd_db"
    
    @property
    def DATABASE_URL(self) -> str:
        """URL de conexión a la base de datos"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # Redis (para caché)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        """URL de conexión a Redis"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # MinIO (almacenamiento de objetos)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "sirccd_admin"
    MINIO_SECRET_KEY: str = "sirccd_password_2026"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_IMAGES: str = "sirccd-images"
    MINIO_BUCKET_MODELS: str = "sirccd-models"
    
    # ML Model
    YOLO_MODEL_PATH: str = "models/yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    IOU_THRESHOLD: float = 0.4
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()
