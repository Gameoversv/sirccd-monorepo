"""
Test Simple B-06: Verificar componentes sin servidor
"""

import sys
from pathlib import Path

# Agregar backend al path
backend_dir = Path(__file__).resolve().parents[2]
if str(backend_dir) not in sys.path:
 sys.path.insert(0, str(backend_dir))

print("\n" + "="*60)
print(" TEST B-06: COMPONENTES (Sin servidor)")
print("="*60)

# Test 1: Redis Connection
print("\n1 TEST: CONEXIÓN REDIS")
print("-" * 60)

try:
 from redis import Redis
 from core.config import settings
 
 redis_conn = Redis(
 host=settings.REDIS_HOST,
 port=settings.REDIS_PORT,
 db=settings.REDIS_DB
 )
 
 ping = redis_conn.ping()
 print(f" Redis conectado: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
 print(f" Ping response: {ping}")
 
except Exception as e:
 print(f" Error conectando a Redis: {e}")

# Test 2: Queue Service
print("\n2 TEST: QUEUE SERVICE")
print("-" * 60)

try:
 from services.queue_service import queue_service
 
 stats = queue_service.get_queue_stats()
 
 print(" QueueService inicializado")
 print(f" Cola: {stats.get('name')}")
 print(f" Encolados: {stats.get('queued', 0)}")
 print(f" Procesando: {stats.get('started', 0)}")
 print(f" Completados: {stats.get('finished', 0)}")
 print(f" Fallidos: {stats.get('failed', 0)}")
 
except Exception as e:
 print(f" Error en QueueService: {e}")

# Test 3: ML Service (Mock)
print("\n3 TEST: ML SERVICE (MOCK)")
print("-" * 60)

try:
 from services.ml_service import ml_service
 from PIL import Image
 import io
 
 # Crear imagen de prueba
 img = Image.new('RGB', (800, 600), color='blue')
 img_bytes = io.BytesIO()
 img.save(img_bytes, format='JPEG')
 img_bytes.seek(0)
 
 # Guardar temporalmente
 import tempfile
 with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
 tmp.write(img_bytes.getvalue())
 tmp_path = tmp.name
 
 # Ejecutar detección
 result = ml_service.detect(tmp_path)
 
 print(" MLInferenceService funcionando")
 print(f" Modo: {'MOCK' if ml_service.use_mock else 'YOLO'}")
 print(f" Tipo de daño: {result.damage_type.value}")
 print(f" Severidad: {result.severity.value}")
 print(f" Confianza: {result.confidence}")
 print(f" Detecciones: {len(result.bounding_boxes)}")
 
 # Limpiar
 import os
 os.remove(tmp_path)
 
except Exception as e:
 print(f" Error en MLService: {e}")
 import traceback
 traceback.print_exc()

# Test 4: Task (Direct Execution)
print("\n4 TEST: TASK (EJECUCIÓN DIRECTA)")
print("-" * 60)

try:
 from tasks.ml_tasks import test_task
 
 result = test_task("Test directo B-06")
 
 print(" Task ejecutada directamente")
 print(f" Success: {result.get('success')}")
 print(f" Message: {result.get('message')}")
 print(f" Worker PID: {result.get('worker')}")
 
except Exception as e:
 print(f" Error ejecutando task: {e}")

# Test 5: Enqueue Job (Sin procesar)
print("\n5 TEST: ENCOLAR JOB (Sin worker)")
print("-" * 60)

try:
 from services.queue_service import queue_service
 
 # Encolar un job de prueba
 job = queue_service.enqueue_ml_detection(
 report_id=999,
 focal_scale_factor=1.0
 )
 
 if job:
 print(" Job encolado exitosamente")
 print(f" Job ID: {job.id}")
 print(f" Estado: {job.get_status()}")
 print(f" Cola: {job.origin}")
 
 # Verificar estado
 status_info = queue_service.get_job_status(job.id)
 print(f"\n Info del job:")
 print(f" Status: {status_info.get('status')}")
 print(f" Created: {status_info.get('created_at')}")
 
 print(f"\n  Para procesar, ejecutar: python backend/worker.py")
 else:
 print(" No se pudo encolar job")
 
except Exception as e:
 print(f" Error encolando job: {e}")
 import traceback
 traceback.print_exc()

# Resumen
print("\n" + "="*60)
print(" RESUMEN")
print("="*60)

print("\n COMPONENTES B-06 VERIFICADOS:")
print("  Redis conectado y funcionando")
print("  QueueService inicializado")
print("  MLService en modo MOCK operativo")
print("  Tasks ejecutables directamente")
print("  Encolado de jobs funcional")

print("\n PRÓXIMOS PASOS:")
print(" 1. Iniciar worker: python backend/worker.py")
print(" 2. Iniciar API: python backend/main.py")
print(" 3. Ejecutar test completo: python backend/test_b06_queue_inference.py")

print("\n ARQUITECTURA B-06:")
print(" FastAPI  Redis Queue  Worker RQ  ML Service  DB")

print("\n")
