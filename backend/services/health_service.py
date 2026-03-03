"""
Servicio de Health Checks (B-10)

Verifica el estado de los componentes del sistema:
- Base de datos (PostgreSQL)
- Cola de tareas (Redis)
- Almacenamiento (MinIO)
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
import redis
from minio import Minio

from core.config import settings


class HealthCheckService:
    """
    Servicio para verificar el estado de salud de los componentes del sistema
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
    
    # ============================================
    # Health Check - Base de Datos
    # ============================================
    
    def check_database(self) -> Dict[str, Any]:
        """
        Verificar conexión y estado de PostgreSQL
        
        Returns:
            Dict con status, response_time y detalles
        """
        start_time = time.time()
        
        try:
            if not self.db:
                return {
                    "status": "unavailable",
                    "message": "No database session available",
                    "response_time_ms": 0
                }
            
            # Test query simple
            result = self.db.execute(text("SELECT 1"))
            result.fetchone()
            
            # Test PostGIS
            result = self.db.execute(text("SELECT PostGIS_Version()"))
            postgis_version = result.fetchone()[0]
            
            # Get database size
            result = self.db.execute(text(
                f"SELECT pg_size_pretty(pg_database_size('{settings.POSTGRES_DB}'))"
            ))
            db_size = result.fetchone()[0]
            
            # Count connections
            result = self.db.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = :dbname"
            ), {"dbname": settings.POSTGRES_DB})
            connections = result.fetchone()[0]
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "message": "Database connection successful",
                "response_time_ms": round(response_time, 2),
                "details": {
                    "host": settings.POSTGRES_HOST,
                    "port": settings.POSTGRES_PORT,
                    "database": settings.POSTGRES_DB,
                    "postgis_version": postgis_version,
                    "database_size": db_size,
                    "active_connections": connections
                }
            }
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "response_time_ms": round(response_time, 2),
                "details": {
                    "host": settings.POSTGRES_HOST,
                    "port": settings.POSTGRES_PORT,
                    "database": settings.POSTGRES_DB,
                    "error": str(e)
                }
            }
    
    # ============================================
    # Health Check - Redis (Cola de Tareas)
    # ============================================
    
    def check_redis(self) -> Dict[str, Any]:
        """
        Verificar conexión y estado de Redis
        
        Returns:
            Dict con status, response_time y detalles
        """
        start_time = time.time()
        
        try:
            # Conectar a Redis
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Ping test
            redis_client.ping()
            
            # Get info
            info = redis_client.info()
            
            # Get queue sizes (usando RQ)
            try:
                default_queue_size = redis_client.llen('rq:queue:default')
            except:
                default_queue_size = 0
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "message": "Redis connection successful",
                "response_time_ms": round(response_time, 2),
                "details": {
                    "host": settings.REDIS_HOST,
                    "port": settings.REDIS_PORT,
                    "redis_version": info.get("redis_version", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "uptime_seconds": info.get("uptime_in_seconds", 0),
                    "queue_size": default_queue_size
                }
            }
        
        except redis.ConnectionError as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}",
                "response_time_ms": round(response_time, 2),
                "details": {
                    "host": settings.REDIS_HOST,
                    "port": settings.REDIS_PORT,
                    "error": str(e)
                }
            }
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "message": f"Redis check failed: {str(e)}",
                "response_time_ms": round(response_time, 2),
                "details": {
                    "host": settings.REDIS_HOST,
                    "port": settings.REDIS_PORT,
                    "error": str(e)
                }
            }
    
    # ============================================
    # Health Check - MinIO (Almacenamiento)
    # ============================================
    
    def check_minio(self) -> Dict[str, Any]:
        """
        Verificar conexión y estado de MinIO
        
        Returns:
            Dict con status, response_time y detalles
        """
        start_time = time.time()
        
        try:
            # Conectar a MinIO
            minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            
            # List buckets (test de conexión)
            buckets = list(minio_client.list_buckets())
            bucket_names = [b.name for b in buckets]
            
            # Check if required buckets exist
            images_bucket_exists = settings.MINIO_BUCKET_IMAGES in bucket_names
            models_bucket_exists = settings.MINIO_BUCKET_MODELS in bucket_names
            
            # Get bucket stats if they exist
            bucket_stats = {}
            
            if images_bucket_exists:
                try:
                    objects = list(minio_client.list_objects(
                        settings.MINIO_BUCKET_IMAGES,
                        recursive=True
                    ))
                    bucket_stats["images"] = {
                        "exists": True,
                        "object_count": len(objects)
                    }
                except:
                    bucket_stats["images"] = {
                        "exists": True,
                        "object_count": 0
                    }
            else:
                bucket_stats["images"] = {"exists": False}
            
            if models_bucket_exists:
                try:
                    objects = list(minio_client.list_objects(
                        settings.MINIO_BUCKET_MODELS,
                        recursive=True
                    ))
                    bucket_stats["models"] = {
                        "exists": True,
                        "object_count": len(objects)
                    }
                except:
                    bucket_stats["models"] = {
                        "exists": True,
                        "object_count": 0
                    }
            else:
                bucket_stats["models"] = {"exists": False}
            
            response_time = (time.time() - start_time) * 1000
            
            # Determinar estado
            status = "healthy"
            message = "MinIO connection successful"
            
            if not images_bucket_exists or not models_bucket_exists:
                status = "degraded"
                message = "MinIO connected but some buckets are missing"
            
            return {
                "status": status,
                "message": message,
                "response_time_ms": round(response_time, 2),
                "details": {
                    "endpoint": settings.MINIO_ENDPOINT,
                    "secure": settings.MINIO_SECURE,
                    "total_buckets": len(buckets),
                    "bucket_names": bucket_names,
                    "required_buckets": {
                        "images": bucket_stats["images"],
                        "models": bucket_stats["models"]
                    }
                }
            }
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "message": f"MinIO connection failed: {str(e)}",
                "response_time_ms": round(response_time, 2),
                "details": {
                    "endpoint": settings.MINIO_ENDPOINT,
                    "secure": settings.MINIO_SECURE,
                    "error": str(e)
                }
            }
    
    # ============================================
    # Health Check - Completo
    # ============================================
    
    def check_all(self) -> Dict[str, Any]:
        """
        Ejecutar todos los health checks
        
        Returns:
            Dict con estado general y detalles de cada componente
        """
        start_time = time.time()
        
        # Ejecutar checks
        db_health = self.check_database()
        redis_health = self.check_redis()
        minio_health = self.check_minio()
        
        # Determinar estado general
        all_healthy = (
            db_health["status"] == "healthy" and
            redis_health["status"] == "healthy" and
            minio_health["status"] in ["healthy", "degraded"]
        )
        
        any_degraded = (
            db_health["status"] == "degraded" or
            redis_health["status"] == "degraded" or
            minio_health["status"] == "degraded"
        )
        
        if all_healthy:
            overall_status = "healthy"
            overall_message = "All systems operational"
        elif any_degraded:
            overall_status = "degraded"
            overall_message = "Some systems have issues but service is available"
        else:
            overall_status = "unhealthy"
            overall_message = "Critical systems are down"
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "status": overall_status,
            "message": overall_message,
            "timestamp": datetime.utcnow().isoformat(),
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "response_time_ms": round(total_time, 2),
            "components": {
                "database": db_health,
                "redis": redis_health,
                "storage": minio_health
            }
        }
    
    # ============================================
    # Liveness & Readiness Probes (Kubernetes)
    # ============================================
    
    def liveness_probe(self) -> bool:
        """
        Liveness probe - indica si la aplicación está viva
        
        Simplemente retorna True (el proceso está corriendo)
        """
        return True
    
    def readiness_probe(self) -> bool:
        """
        Readiness probe - indica si la aplicación está lista para recibir tráfico
        
        Verifica componentes críticos (DB y Redis)
        """
        db_health = self.check_database()
        redis_health = self.check_redis()
        
        return (
            db_health["status"] == "healthy" and
            redis_health["status"] == "healthy"
        )


def get_health_service(db: Session = None) -> HealthCheckService:
    """
    Factory para obtener instancia del servicio de health checks
    """
    return HealthCheckService(db)
