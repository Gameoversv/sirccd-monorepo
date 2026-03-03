"""
Métricas de Prometheus (B-10)

Sistema de observabilidad con métricas para Prometheus:
- Contadores de peticiones por endpoint
- Histogramas de tiempos de respuesta
- Contadores de errores por código HTTP
- Métricas personalizadas de negocio
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
from fastapi import Request, Response
from typing import Callable
import time

from core.config import settings


# ============================================
# Registry de Prometheus
# ============================================

# Usar registry global de prometheus_client
registry = CollectorRegistry(auto_describe=True)


# ============================================
# Métricas Básicas HTTP
# ============================================

# Contador de peticiones HTTP
http_requests_total = Counter(
    'http_requests_total',
    'Total de peticiones HTTP recibidas',
    ['method', 'endpoint', 'status'],
    registry=registry
)

# Histograma de duración de peticiones
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Duración de peticiones HTTP en segundos',
    ['method', 'endpoint'],
    registry=registry,
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf'))
)

# Contador de errores HTTP
http_errors_total = Counter(
    'http_errors_total',
    'Total de errores HTTP (4xx y 5xx)',
    ['method', 'endpoint', 'status'],
    registry=registry
)

# Gauge de peticiones en progreso
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Número de peticiones HTTP en progreso',
    ['method', 'endpoint'],
    registry=registry
)


# ============================================
# Métricas de Negocio
# ============================================

# Contador de reportes creados
reports_created_total = Counter(
    'reports_created_total',
    'Total de reportes creados',
    ['damage_type', 'severity'],
    registry=registry
)

# Contador de incidentes por prioridad
incidents_by_priority = Gauge(
    'incidents_by_priority',
    'Número actual de incidentes por prioridad',
    ['priority', 'status'],
    registry=registry
)

# Histograma de tiempo de inferencia ML
ml_inference_duration_seconds = Histogram(
    'ml_inference_duration_seconds',
    'Duración de inferencia ML en segundos',
    ['model'],
    registry=registry,
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf'))
)

# Contador de detecciones ML
ml_detections_total = Counter(
    'ml_detections_total',
    'Total de detecciones ML',
    ['model', 'damage_type'],
    registry=registry
)

# Contador de deduplicación
deduplication_checks_total = Counter(
    'deduplication_checks_total',
    'Total de verificaciones de deduplicación',
    ['result'],  # duplicate, unique
    registry=registry
)

# Histograma de tiempo de exportación
export_duration_seconds = Histogram(
    'export_duration_seconds',
    'Duración de exportaciones en segundos',
    ['format', 'type'],  # format: geojson/csv, type: incidents/kpis
    registry=registry,
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float('inf'))
)

# Gauge de tamaño de índice FAISS
faiss_index_size = Gauge(
    'faiss_index_size',
    'Número de vectores en el índice FAISS',
    registry=registry
)

# Gauge de conexiones de base de datos
database_connections = Gauge(
    'database_connections',
    'Número de conexiones activas a la base de datos',
    registry=registry
)

# Gauge de tamaño de cola Redis
redis_queue_size = Gauge(
    'redis_queue_size',
    'Tamaño de la cola de tareas en Redis',
    ['queue'],
    registry=registry
)


# ============================================
# Middleware de Métricas
# ============================================

class PrometheusMiddleware:
    """
    Middleware para capturar métricas HTTP automáticamente
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extraer información de la petición
        method = scope["method"]
        path = scope["path"]
        
        # Ignorar endpoints de métricas para evitar loops
        if path in ["/metrics", "/api/v1/metrics"]:
            await self.app(scope, receive, send)
            return
        
        # Normalizar path (eliminar IDs)
        endpoint = self._normalize_path(path)
        
        # Incrementar gauge de peticiones en progreso
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        # Medir tiempo
        start_time = time.time()
        
        # Variables para capturar el status code
        status_code = 500
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            # Ejecutar la petición
            await self.app(scope, receive, send_wrapper)
        finally:
            # Calcular duración
            duration = time.time() - start_time
            
            # Decrementar gauge de peticiones en progreso
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
            
            # Registrar métricas
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # Registrar errores
            if status_code >= 400:
                http_errors_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status_code
                ).inc()
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalizar path para agrupar endpoints similares
        
        Ejemplos:
        - /api/v1/incidents/123 -> /api/v1/incidents/{id}
        - /api/v1/reports/456/approve -> /api/v1/reports/{id}/approve
        """
        parts = path.split('/')
        normalized = []
        
        for i, part in enumerate(parts):
            # Si es un número, reemplazar por {id}
            if part.isdigit():
                normalized.append('{id}')
            # Si es un UUID-like, reemplazar por {id}
            elif len(part) == 36 and part.count('-') == 4:
                normalized.append('{id}')
            # Si es un hash corto (8-16 chars alfanuméricos), reemplazar por {id}
            elif len(part) >= 8 and len(part) <= 16 and part.isalnum():
                normalized.append('{id}')
            else:
                normalized.append(part)
        
        return '/'.join(normalized)


# ============================================
# Funciones Helper para Registrar Métricas
# ============================================

def record_report_created(damage_type: str, severity: str):
    """Registrar creación de reporte"""
    reports_created_total.labels(
        damage_type=damage_type,
        severity=severity
    ).inc()


def record_ml_inference(model: str, duration: float, damage_type: str = None):
    """Registrar inferencia ML"""
    ml_inference_duration_seconds.labels(model=model).observe(duration)
    
    if damage_type:
        ml_detections_total.labels(
            model=model,
            damage_type=damage_type
        ).inc()


def record_deduplication_check(is_duplicate: bool):
    """Registrar verificación de deduplicación"""
    result = "duplicate" if is_duplicate else "unique"
    deduplication_checks_total.labels(result=result).inc()


def record_export(format: str, type: str, duration: float):
    """Registrar exportación"""
    export_duration_seconds.labels(
        format=format,
        type=type
    ).observe(duration)


def update_faiss_index_size(size: int):
    """Actualizar tamaño del índice FAISS"""
    faiss_index_size.set(size)


def update_database_connections(count: int):
    """Actualizar número de conexiones de BD"""
    database_connections.set(count)


def update_redis_queue_size(queue_name: str, size: int):
    """Actualizar tamaño de cola Redis"""
    redis_queue_size.labels(queue=queue_name).set(size)


def update_incidents_by_priority(priority: str, status: str, count: int):
    """Actualizar contador de incidentes por prioridad"""
    incidents_by_priority.labels(
        priority=priority,
        status=status
    ).set(count)


# ============================================
# Generar Métricas para Prometheus
# ============================================

def generate_metrics() -> bytes:
    """
    Generar métricas en formato Prometheus
    
    Returns:
        bytes con el contenido de las métricas
    """
    return generate_latest(registry)


def get_metrics_content_type() -> str:
    """
    Obtener el content type para métricas de Prometheus
    
    Returns:
        str con el content type
    """
    return CONTENT_TYPE_LATEST
