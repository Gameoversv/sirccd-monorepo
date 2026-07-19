"""
Queue Service - Gestión de cola RQ con Redis
"""

import logging
from typing import Optional
from redis import Redis
from rq import Queue
from rq.job import Job

from core.config import settings

logger = logging.getLogger(__name__)


class QueueService:
    """
    Servicio para gestionar cola de tareas RQ
    
    Maneja conexión a Redis y encolado de jobs.
    """
    
    def __init__(self):
        """Inicializa conexión a Redis y cola"""
        self.redis_conn: Optional[Redis] = None
        self.queue: Optional[Queue] = None
        self._connect()
    
    def _connect(self):
        """Conecta a Redis y crea instancia de Queue"""
        try:
            self.redis_conn = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,  # RQ necesita bytes
            )
            
            # Verificar conexión
            self.redis_conn.ping()
            
            # Crear cola
            self.queue = Queue(
                name='ml_inference',
                connection=self.redis_conn,
                default_timeout=300  # 5 minutos timeout por job
            )
            
            logger.info(f" Conectado a Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            logger.info(f" Cola 'ml_inference' creada")
            
        except Exception as e:
            logger.warning(f"⚠ Redis no disponible: {e}")
            self.redis_conn = None
            self.queue = None
    
    def enqueue_ml_detection(
        self,
        report_id: int,
        focal_scale_factor: Optional[float] = None,
    ) -> Optional[Job]:
        """
        Encola tarea de detección ML para un reporte

        Args:
            report_id: ID del reporte
            focal_scale_factor: Factor de zoom ya resuelto por la capa HTTP.
                La imagen no se pasa: el worker la baja de MinIO, porque corre
                en otro contenedor y no comparte disco con la API.

        Returns:
            Job de RQ o None si hay error
        """
        if not self.queue:
            logger.error(" Cola no disponible, reconectando...")
            try:
                self._connect()
            except Exception:
                return None
        
        try:
            from tasks.ml_tasks import process_report_ml_detection
            
            job = self.queue.enqueue(
                process_report_ml_detection,
                report_id=report_id,
                focal_scale_factor=focal_scale_factor,
                job_timeout=300,  # 5 minutos
                result_ttl=3600,  # Mantener resultado 1 hora
                failure_ttl=86400,  # Mantener failures 24 horas
            )
            
            logger.info(
                f" Job encolado: {job.id} para reporte {report_id}"
            )
            
            return job
            
        except Exception as e:
            logger.error(f" Error encolando job: {e}", exc_info=True)
            return None
    
    def get_job_status(self, job_id: str) -> dict:
        """
        Obtiene el estado de un job
        
        Args:
            job_id: ID del job
        
        Returns:
            dict con información del job
        """
        if not self.queue:
            return {"error": "Cola no disponible"}
        
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            
            return {
                "job_id": job.id,
                "status": job.get_status(),
                "result": job.result if job.is_finished else None,
                "error": str(job.exc_info) if job.is_failed else None,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_queue_stats(self) -> dict:
        """
        Obtiene estadísticas de la cola
        
        Returns:
            dict con estadísticas
        """
        if not self.queue:
            return {"error": "Cola no disponible"}
        
        try:
            from rq.registry import (
                StartedJobRegistry,
                FinishedJobRegistry,
                FailedJobRegistry
            )
            
            started_registry = StartedJobRegistry(queue=self.queue)
            finished_registry = FinishedJobRegistry(queue=self.queue)
            failed_registry = FailedJobRegistry(queue=self.queue)
            
            return {
                "name": self.queue.name,
                "queued": len(self.queue),
                "started": len(started_registry),
                "finished": len(finished_registry),
                "failed": len(failed_registry),
                "workers": self.queue.count,
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e)}
    

# Instancia global del servicio de cola
queue_service = QueueService()


def get_queue_service() -> QueueService:
    """
    Obtiene la instancia del servicio de cola
    
    Returns:
        QueueService singleton
    """
    return queue_service
