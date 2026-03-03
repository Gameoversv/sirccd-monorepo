"""
Endpoints de health check y métricas (B-10)
"""

from fastapi import APIRouter, Depends, Response, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from services.health_service import get_health_service
from core.metrics import generate_metrics, get_metrics_content_type

router = APIRouter()


@router.get("/health")
async def health(
    component: Optional[str] = Query(None, description="Componente específico: database, redis, minio"),
    db: Session = Depends(get_db)
):
    """
    Health check endpoint con verificación de componentes
    
    Args:
        component: Componente específico a verificar (opcional)
        db: Sesión de base de datos
    
    Returns:
        dict: Estado de salud completo o de un componente específico
    
    Códigos HTTP:
    - 200: Sistema saludable o degradado
    - 503: Sistema no saludable (crítico)
    """
    health_service = get_health_service(db)
    
    # Si se solicita un componente específico
    if component:
        if component == "database":
            result = health_service.check_database()
        elif component == "redis":
            result = health_service.check_redis()
        elif component == "minio":
            result = health_service.check_minio()
        else:
            return {"error": f"Unknown component: {component}"}
        
        # Retornar 503 si el componente no está saludable
        if result["status"] not in ["healthy", "degraded"]:
            return Response(
                content=str(result),
                status_code=503,
                media_type="application/json"
            )
        return result
    
    # Verificación completa
    result = health_service.check_all()
    
    # Retornar 503 si el sistema no está saludable
    if result["status"] not in ["healthy", "degraded"]:
        return Response(
            content=str(result),
            status_code=503,
            media_type="application/json"
        )
    
    return result


@router.get("/health/live")
async def liveness(db: Session = Depends(get_db)):
    """
    Liveness probe para Kubernetes
    
    Verifica que el proceso está vivo y puede responder.
    
    Returns:
        dict: Estado de liveness (200 si vivo, 503 si no)
    """
    health_service = get_health_service(db)
    is_alive = health_service.liveness_probe()
    
    if is_alive:
        return {"status": "alive"}
    else:
        return Response(
            content={"status": "dead"},
            status_code=503,
            media_type="application/json"
        )


@router.get("/health/ready")
async def readiness(db: Session = Depends(get_db)):
    """
    Readiness probe para Kubernetes
    
    Verifica que el servicio está listo para recibir tráfico.
    Verifica componentes críticos: base de datos y Redis.
    
    Returns:
        dict: Estado de readiness con detalles (200 si listo, 503 si no)
    """
    health_service = get_health_service(db)
    is_ready, details = health_service.readiness_probe()
    
    if is_ready:
        return {
            "status": "ready",
            "components": details
        }
    else:
        return Response(
            content={
                "status": "not_ready",
                "components": details
            },
            status_code=503,
            media_type="application/json"
        )


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Endpoint de métricas para Prometheus
    
    Expone métricas en formato compatible con Prometheus para scraping.
    
    Métricas expuestas:
    - http_requests_total: Total de peticiones HTTP
    - http_request_duration_seconds: Duración de peticiones
    - http_errors_total: Total de errores HTTP
    - reports_created_total: Reportes creados
    - ml_inference_duration_seconds: Duración de inferencias ML
    - Y más...
    
    Ejemplo de configuración Prometheus:
    ```yaml
    scrape_configs:
      - job_name: 'sirccd-backend'
        static_configs:
          - targets: ['localhost:8000']
        metrics_path: '/api/v1/metrics'
    ```
    """
    metrics_data = generate_metrics()
    
    return Response(
        content=metrics_data,
        media_type=get_metrics_content_type()
    )


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint
    
    Returns:
        dict: Pong message
    """
    return {"message": "pong"}
