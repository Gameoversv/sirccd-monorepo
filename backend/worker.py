"""
Worker RQ - Procesa tareas en segundo plano

Ejecutar con:
    python worker.py

O con logging verbose:
    python worker.py -v
"""

import sys
import os
import logging
from pathlib import Path

# Agregar directorio backend al path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from redis import Redis
from rq import Worker, Queue
from core.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Inicia el worker RQ"""
    
    # Conectar a Redis
    redis_conn = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
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
    
    # Crear y ejecutar worker
    worker = Worker(
        queues,
        name=f"sirccd-worker-{os.getpid()}",
        connection=redis_conn
    )
    
    logger.info(f"🚀 Worker iniciado: {worker.name}")
    logger.info("⏳ Esperando tareas...")
    
    # Ejecutar worker (loop infinito)
    worker.work(with_scheduler=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Worker detenido por usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error en worker: {e}", exc_info=True)
        sys.exit(1)
