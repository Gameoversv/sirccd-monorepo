"""
Worker RQ Simplificado - Compatible con Windows

Procesa jobs de la cola sin usar fork (compatible con Windows)
"""

import sys
import os
import time
import logging
from pathlib import Path

# Agregar directorio backend al path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from redis import Redis
from rq import Queue, Worker
from core.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Inicia el worker RQ en modo simple (sin fork)"""
    
    # Conectar a Redis
    redis_conn = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=False
    )
    
    # Verificar conexión
    try:
        redis_conn.ping()
        logger.info(f"✅ Conectado a Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    except Exception as e:
        logger.error(f"❌ Error conectando a Redis: {e}")
        sys.exit(1)
    
    # Crear colas a escuchar
    queues = [
        Queue('ml_inference', connection=redis_conn),
        Queue('default', connection=redis_conn),
    ]
    
    logger.info(f"🎧 Escuchando colas: {[q.name for q in queues]}")
    
    # Crear worker
    worker = Worker(
        queues,
        name=f"sirccd-worker-{os.getpid()}",
        connection=redis_conn
    )
    
    logger.info(f"🚀 Worker iniciado: {worker.name}")
    logger.info("⏳ Esperando tareas...")
    logger.info("💡 Modo Windows: Procesamiento sincrónico sin fork")
    
    # Ejecutar worker en modo burst (procesa jobs existentes y termina)
    # o en loop simple
    try:
        # Usar work() con parámetros compatibles con Windows
        worker.work(burst=False, logging_level='INFO')
    except Exception as e:
        logger.error(f"❌ Error en worker: {e}")
        
        # Fallback: procesar manualmente en loop
        logger.info("📌 Intentando modo de procesamiento manual...")
        manual_worker_loop(queues, redis_conn)


def manual_worker_loop(queues, redis_conn):
    """
    Loop manual de procesamiento (alternativa para Windows)
    
    Procesa jobs de las colas sin usar fork
    """
    logger.info("🔄 Iniciando loop manual de procesamiento")
    
    while True:
        try:
            # Revisar cada cola
            job_found = False
            
            for queue in queues:
                # Intentar obtener un job
                job = queue.dequeue()
                
                if job:
                    job_found = True
                    logger.info(f"📥 Job recibido: {job.id} de cola '{queue.name}'")
                    
                    try:
                        # Ejecutar el job
                        result = job.perform()
                        job.set_status('finished')
                        job.save()
                        
                        logger.info(f"✅ Job {job.id} completado exitosamente")
                        
                    except Exception as e:
                        logger.error(f"❌ Error procesando job {job.id}: {e}")
                        job.set_status('failed')
                        job.save()
            
            # Si no hay jobs, esperar un poco
            if not job_found:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n👋 Worker detenido por usuario")
            break
        except Exception as e:
            logger.error(f"❌ Error en loop: {e}")
            time.sleep(2)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Worker detenido por usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)
