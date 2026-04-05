"""
Test B-06 - Procesamiento DIRECTO sin Worker
=============================================

Este test procesa los jobs manualmente sin necesidad del worker RQ.
Ideal para Windows donde RQ tiene problemas con fork().
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[2]
if str(backend_dir) not in sys.path:
 sys.path.insert(0, str(backend_dir))

print("\n" + "="*70)
print(" TEST B-06: PROCESAMIENTO DIRECTO (Sin Worker)")
print("="*70)

# 1. Verificar cola
print("\n1 ESTADO DE LA COLA")
print("-" * 70)

from services.queue_service import queue_service

stats = queue_service.get_queue_stats()
print(f" Cola: {stats['name']}")
print(f" Encolados: {stats['queued']}")
print(f" Procesando: {stats['started']}")
print(f" Completados: {stats['finished']}")
print(f" Fallidos: {stats['failed']}")

# 2. Procesar jobs pendientes DIRECTAMENTE
if stats['queued'] > 0:
 print(f"\n2 PROCESANDO {stats['queued']} JOBS PENDIENTES")
 print("-" * 70)
 
 from redis import Redis
 from rq import Queue
 from core.config import settings
 
 redis_conn = Redis(
 host=settings.REDIS_HOST,
 port=settings.REDIS_PORT,
 db=settings.REDIS_DB,
 decode_responses=False
 )
 
 queue = Queue('ml_inference', connection=redis_conn)
 
 jobs_processed = 0
 while True:
 # Obtener siguiente job
 job_id = queue.job_ids
 if not job_id:
 break
 
 job_id = job_id[0]
 print(f"\n Procesando job: {job_id}")
 
 # Obtener y ejecutar job
 from rq.job import Job
 job = Job.fetch(job_id, connection=redis_conn)
 
 # Ejecutar directamente
 try:
 result = job.perform()
 print(f" Resultado: {result.get('success', False)}")
 
 if result.get('success'):
 print(f" Reporte ID: {result.get('report_id')}")
 print(f" Tipo: {result.get('damage_type')}")
 print(f" Severidad: {result.get('severity')}")
 print(f" Confianza: {result.get('confidence')}")
 print(f" Detecciones: {result.get('num_detections')}")
 else:
 print(f" Error: {result.get('error')}")
 
 jobs_processed += 1
 
 # Remover de la cola
 queue.remove(job)
 
 except Exception as e:
 print(f" Error ejecutando job: {e}")
 import traceback
 traceback.print_exc()
 break
 
 print(f"\n {jobs_processed} jobs procesados exitosamente")

else:
 print("\n  No hay jobs pendientes en la cola")

# 3. Estado final
print("\n3 ESTADO FINAL DE LA COLA")
print("-" * 70)

stats = queue_service.get_queue_stats()
print(f" Encolados: {stats['queued']}")
print(f" Completados: {stats['finished']}")
print(f" Fallidos: {stats['failed']}")

print("\n" + "="*70)
print(" TEST COMPLETADO")
print("="*70)
print("\n Este método procesa jobs sin necesidad de worker RQ")
print(" Ideal para Windows donde RQ tiene limitaciones\n")
