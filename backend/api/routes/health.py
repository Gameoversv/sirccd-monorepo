"""
Health Check Endpoint
"""

from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Esquema de respuesta del health check"""
    status: str
    service: str
    version: str
    timestamp: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health Check Endpoint
    
    Verifica que el servicio está activo y funcionando.
    
    Returns:
        HealthResponse: Estado del servicio
    """
    return HealthResponse(
        status="healthy",
        service="SIRCCD API",
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint
    
    Returns:
        dict: Mensaje pong
    """
    return {"message": "pong"}
