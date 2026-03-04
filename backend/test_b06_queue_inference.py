"""
Test B-06: Cola de inferencia ML con RQ

Prueba el sistema de procesamiento asíncrono con Redis Queue:
- Encolado de jobs de detección ML
- Procesamiento por worker
- Actualización de reportes
- Consulta de estado de jobs
"""

import os
import sys
import time
from pathlib import Path

# Agregar backend al path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
 sys.path.insert(0, str(backend_dir))

import requests
from PIL import Image
import io


# ============================================
# Configuración
# ============================================

API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USERNAME = "testb04user"
TEST_PASSWORD = "testb04password"

# Colores para output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'


# ============================================
# Funciones Auxiliares
# ============================================

def create_test_image(text="Test B-06", size=(800, 600)):
 """Crea una imagen de prueba simple"""
 img = Image.new('RGB', size, color='lightblue')
 
 # Guardar como bytes
 img_bytes = io.BytesIO()
 img.save(img_bytes, format='JPEG', quality=90)
 img_bytes.seek(0)
 
 return img_bytes


def login_test_user():
 """Autentica y obtiene token JWT"""
 response = requests.post(
 f"{API_BASE_URL}/auth/login",
 data={
 "username": TEST_USERNAME,
 "password": TEST_PASSWORD
 }
 )
 
 if response.status_code == 200:
 token = response.json()["access_token"]
 return token
 else:
 print(f"{RED} Error en login: {response.status_code}{RESET}")
 print(response.text)
 return None


def create_report_with_image(token):
 """Crea un reporte con imagen"""
 
 # Crear imagen de prueba
 image_bytes = create_test_image("B-06 Queue Test")
 
 # Preparar multipart
 files = {
 'image': ('test_b06.jpg', image_bytes, 'image/jpeg')
 }
 
 data = {
 'latitude': -34.603722,
 'longitude': -58.381592,
 'description': 'Test B-06: Procesamiento con cola RQ'
 }
 
 headers = {
 'Authorization': f'Bearer {token}'
 }
 
 response = requests.post(
 f"{API_BASE_URL}/reportes",
 files=files,
 data=data,
 headers=headers
 )
 
 return response


def get_job_status(token, job_id):
 """Consulta estado de un job"""
 headers = {'Authorization': f'Bearer {token}'}
 
 response = requests.get(
 f"{API_BASE_URL}/reportes/jobs/{job_id}/status",
 headers=headers
 )
 
 return response


def get_queue_stats(token):
 """Obtiene estadísticas de la cola"""
 headers = {'Authorization': f'Bearer {token}'}
 
 response = requests.get(
 f"{API_BASE_URL}/reportes/queue/stats",
 headers=headers
 )
 
 return response


def get_report(token, report_id):
 """Obtiene un reporte por ID"""
 headers = {'Authorization': f'Bearer {token}'}
 
 response = requests.get(
 f"{API_BASE_URL}/reportes/{report_id}",
 headers=headers
 )
 
 return response


# ============================================
# Tests
# ============================================

def test_queue_stats():
 """Test 1: Verificar estadísticas de cola"""
 print(f"\n{BLUE}{'='*60}{RESET}")
 print(f"{BLUE}1 TEST: ESTADÍSTICAS DE COLA RQ{RESET}")
 print(f"{BLUE}{'='*60}{RESET}")
 
 token = login_test_user()
 if not token:
 print(f"{RED} No se pudo autenticar{RESET}")
 return False
 
 response = get_queue_stats(token)
 
 print(f"\n Status Code: {response.status_code}")
 
 if response.status_code == 200:
 stats = response.json()
 print(f"\n Estadísticas de cola:")
 print(f" Cola: {stats.get('name', 'N/A')}")
 print(f" En cola: {stats.get('queued', 0)}")
 print(f" Procesando: {stats.get('started', 0)}")
 print(f" Completados: {stats.get('finished', 0)}")
 print(f" Fallidos: {stats.get('failed', 0)}")
 print(f" Workers: {stats.get('workers', 0)}")
 
 print(f"\n{GREEN} Estadísticas obtenidas correctamente{RESET}")
 return True
 else:
 print(f"{RED} Error obteniendo estadísticas{RESET}")
 print(response.text)
 return False


def test_create_report_with_queue():
 """Test 2: Crear reporte y verificar que se encola"""
 print(f"\n{BLUE}{'='*60}{RESET}")
 print(f"{BLUE}2 TEST: CREAR REPORTE CON ENCOLADO ML{RESET}")
 print(f"{BLUE}{'='*60}{RESET}")
 
 token = login_test_user()
 if not token:
 print(f"{RED} No se pudo autenticar{RESET}")
 return False, None, None
 
 print("\n Creando reporte con imagen...")
 
 response = create_report_with_image(token)
 
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 201:
 data = response.json()
 report_id = data['id']
 job_id = data.get('job_id')
 status_val = data['status']
 
 print(f"\n Reporte creado exitosamente:")
 print(f"  ID: {report_id}")
 print(f" Status: {status_val}")
 print(f" Job ID: {job_id}")
 print(f" URL: {data['image_url']}")
 print(f" Ubicación: ({data['latitude']}, {data['longitude']})")
 print(f" Tipo (placeholder): {data['damage_type']}")
 print(f" Severidad (placeholder): {data['severity']}")
 print(f" Confianza (placeholder): {data['confidence']}")
 
 if job_id:
 print(f"\n{GREEN} Job encolado: {job_id}{RESET}")
 return True, report_id, job_id
 else:
 print(f"\n{YELLOW} Reporte creado pero sin job_id (cola no disponible?){RESET}")
 return True, report_id, None
 else:
 print(f"{RED} Error creando reporte{RESET}")
 print(response.text)
 return False, None, None


def test_job_status(token, job_id):
 """Test 3: Consultar estado de job"""
 print(f"\n{BLUE}{'='*60}{RESET}")
 print(f"{BLUE}3 TEST: CONSULTAR ESTADO DE JOB{RESET}")
 print(f"{BLUE}{'='*60}{RESET}")
 
 if not job_id:
 print(f"{YELLOW} No hay job_id, skip test{RESET}")
 return False
 
 print(f"\n Consultando job: {job_id}")
 
 response = get_job_status(token, job_id)
 
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 200:
 job_info = response.json()
 
 print(f"\n Información del Job:")
 print(f" Job ID: {job_info.get('job_id', 'N/A')}")
 print(f" Estado: {job_info.get('status', 'N/A')}")
 print(f" Creado: {job_info.get('created_at', 'N/A')}")
 print(f" Iniciado: {job_info.get('started_at', 'N/A')}")
 print(f" Terminado: {job_info.get('ended_at', 'N/A')}")
 
 if job_info.get('result'):
 print(f" Resultado: {job_info['result']}")
 
 if job_info.get('error'):
 print(f" Error: {job_info['error']}")
 
 print(f"\n{GREEN} Estado del job obtenido{RESET}")
 return True
 else:
 print(f"{RED} Error consultando job{RESET}")
 print(response.text)
 return False


def test_wait_for_processing(token, report_id, job_id, max_wait=30):
 """Test 4: Esperar a que el worker procese el reporte"""
 print(f"\n{BLUE}{'='*60}{RESET}")
 print(f"{BLUE}4 TEST: ESPERAR PROCESAMIENTO (Worker){RESET}")
 print(f"{BLUE}{'='*60}{RESET}")
 
 if not job_id:
 print(f"{YELLOW} No hay job_id, verificando solo el reporte...{RESET}")
 
 # Esperar un poco por si se procesa inline
 time.sleep(2)
 
 # Ver estado del reporte
 response = get_report(token, report_id)
 if response.status_code == 200:
 data = response.json()
 print(f"\n Estado del reporte:")
 print(f" Status: {data['status']}")
 print(f" Tipo: {data['damage_type']}")
 print(f" Severidad: {data['severity']}")
 print(f" Confianza: {data['confidence']}")
 
 print(f"\n{YELLOW} No hay worker activo - test manual requerido{RESET}")
 print(f"{YELLOW} Para probar completamente, ejecutar: python backend/worker.py{RESET}")
 return False
 
 print(f"\n Esperando procesamiento del job {job_id}...")
 print(f" (máximo {max_wait} segundos)")
 
 for i in range(max_wait):
 time.sleep(1)
 
 # Consultar estado
 response = get_job_status(token, job_id)
 
 if response.status_code == 200:
 job_info = response.json()
 status_val = job_info.get('status', 'unknown')
 
 print(f" [{i+1}s] Estado: {status_val}", end='\r')
 
 if status_val == 'finished':
 print(f"\n\n{GREEN} Job completado!{RESET}")
 
 result = job_info.get('result')
 if result:
 print(f"\n Resultado del procesamiento ML:")
 print(f" Report ID: {result.get('report_id')}")
 print(f" Success: {result.get('success')}")
 print(f" Tipo de daño: {result.get('damage_type')}")
 print(f" Severidad: {result.get('severity')}")
 print(f" Confianza: {result.get('confidence')}")
 print(f" Detecciones: {result.get('num_detections', 0)}")
 
 # Verificar que el reporte fue actualizado
 report_response = get_report(token, report_id)
 if report_response.status_code == 200:
 report_data = report_response.json()
 print(f"\n Reporte actualizado:")
 print(f" Status: {report_data['status']}")
 print(f" Tipo: {report_data['damage_type']}")
 print(f" Severidad: {report_data['severity']}")
 print(f" Confianza: {report_data['confidence']}")
 
 if report_data.get('detections_json'):
 print(f" Detections JSON guardado")
 
 return True
 
 elif status_val == 'failed':
 print(f"\n\n{RED} Job falló!{RESET}")
 error = job_info.get('error')
 if error:
 print(f" Error: {error}")
 return False
 
 print(f"\n\n{YELLOW} Timeout esperando procesamiento{RESET}")
 print(f"{YELLOW} El worker puede estar detenido o muy lento{RESET}")
 print(f"{YELLOW} Ejecutar: python backend/worker.py{RESET}")
 
 return False


def test_direct_task_execution():
 """Test 5: Ejecutar task directamente (sin worker)"""
 print(f"\n{BLUE}{'='*60}{RESET}")
 print(f"{BLUE}5 TEST: EJECUCIÓN DIRECTA DE TASK{RESET}")
 print(f"{BLUE}{'='*60}{RESET}")
 
 print("\n Probando task de procesamiento ML directamente...")
 
 try:
 from tasks.ml_tasks import test_task
 
 result = test_task("Hello from B-06 test")
 
 print(f"\n Resultado:")
 print(f" Success: {result.get('success')}")
 print(f" Message: {result.get('message')}")
 print(f" Worker PID: {result.get('worker')}")
 
 print(f"\n{GREEN} Task ejecutada directamente OK{RESET}")
 return True
 
 except Exception as e:
 print(f"{RED} Error ejecutando task: {e}{RESET}")
 return False


# ============================================
# Main
# ============================================

def main():
 """Ejecuta todos los tests"""
 
 print(f"\n{BLUE}{'='*60}{RESET}")
 print(f"{BLUE} TESTS B-06: COLA DE INFERENCIA ML (RQ){RESET}")
 print(f"{BLUE}{'='*60}{RESET}")
 
 print(f"\n Tests a ejecutar:")
 print(f" 1. Estadísticas de cola RQ")
 print(f" 2. Crear reporte con encolado")
 print(f" 3. Consultar estado de job")
 print(f" 4. Esperar procesamiento por worker")
 print(f" 5. Ejecución directa de task")
 
 # Test 1: Queue stats
 test_queue_stats()
 
 # Test 2: Create report
 success, report_id, job_id = test_create_report_with_queue()
 
 if not success:
 print(f"\n{RED} Tests fallaron en creación de reporte{RESET}")
 return
 
 # Test 3: Job status
 token = login_test_user()
 if job_id:
 test_job_status(token, job_id)
 
 # Test 4: Wait for worker
 test_wait_for_processing(token, report_id, job_id)
 
 # Test 5: Direct execution
 test_direct_task_execution()
 
 # Resumen
 print(f"\n{BLUE}{'='*60}{RESET}")
 print(f"{BLUE} RESUMEN{RESET}")
 print(f"{BLUE}{'='*60}{RESET}")
 
 print(f"\n TESTS B-06 COMPLETADOS")
 
 print(f"\n Notas:")
 print(f"  Para procesamiento completo, ejecutar worker:")
 print(f" {YELLOW}python backend/worker.py{RESET}")
 print(f"  Worker escucha cola 'ml_inference' en Redis")
 print(f"  Reportes empiezan con status=PROCESSING")
 print(f"  Worker actualiza: damage_type, severity, confidence, detections_json")
 print(f"  job_id permite hacer polling del estado")
 
 print(f"\n ARQUITECTURA:")
 print(f" FastAPI  Redis Queue  Worker RQ  ML Service  DB Update")


if __name__ == '__main__':
 try:
 main()
 except KeyboardInterrupt:
 print(f"\n\n{YELLOW} Tests interrumpidos por usuario{RESET}")
 except Exception as e:
 print(f"\n{RED} Error en tests: {e}{RESET}")
 import traceback
 traceback.print_exc()
